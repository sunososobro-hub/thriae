#!/usr/bin/env python3
"""Lesson reviewer helper (quarantine reviewer).

Local, no API call:   python -I hive/scripts/review_lesson.py --issue N --dry-run
Workflow stages (see .github/workflows/review-lesson.yml):
  --env / --issue N / --issue-file F  choose the issue source (title and body are DATA)
  --dry-run                           print the prompt payload and exit
  --call --out FILE                   ask the model (no tools), validate, write verdict JSON
  --select FILE [--only N]            list the target's open lesson issues that need a review (max 5)
  --review-batch FILE --out FILE      ask the model for each selected issue, write verdict list
  --post FILE                         validate again, post ONE comment + one review:* label per issue
Target repo = GITHUB_REPOSITORY (the workflow sets it from THRIAE_TARGET_REPO).
Standard library only. Nothing here executes text from an issue.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

MODEL = "claude-sonnet-5-5"
MARKER = "<!-- thriae-review -->"
MAX_REASON = 600
MAX_REASON_LINES = 4
MAX_BODY = 12000
MAX_TITLE = 300
MAX_PER_RUN = 5
EDIT_SLACK = timedelta(seconds=120)  # our own label/comment bumps issue.updated_at a little
TRUSTED_ASSOC = {"OWNER", "MEMBER", "COLLABORATOR"}
SIMPLE = {
    "accepted": "review:accepted",
    "duplicate": "review:duplicate",
    "needs-evidence": "review:needs-evidence",
    "rejected": "review:rejected",
}
MERGE_RE = re.compile(r"^merge-into:(\d{1,2})$")
LABELS = {
    "review:accepted": "0e8a16",
    "review:merge": "1d76db",
    "review:duplicate": "cfd3d7",
    "review:needs-evidence": "fbca04",
    "review:rejected": "b60205",
}
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


class ReviewError(ValueError):
    pass


def validate(obj):
    """Return (verdict, reason) or raise ReviewError. Strict: two fields only."""
    if not isinstance(obj, dict):
        raise ReviewError("not an object")
    if set(obj) != {"verdict", "reason"}:
        raise ReviewError("fields must be exactly verdict and reason")
    verdict, reason = obj["verdict"], obj["reason"]
    if not isinstance(verdict, str) or not isinstance(reason, str):
        raise ReviewError("verdict and reason must be strings")
    if verdict not in SIMPLE and not MERGE_RE.match(verdict):
        raise ReviewError("verdict not allowed")
    reason = reason.strip()
    if not reason:
        raise ReviewError("empty reason")
    if len(reason) > MAX_REASON:
        raise ReviewError("reason too long")
    if CTRL.search(reason):
        raise ReviewError("control characters in reason")
    if len([ln for ln in reason.splitlines() if ln.strip()]) > MAX_REASON_LINES:
        raise ReviewError("reason has too many lines")
    return verdict, reason


def label_for(verdict):
    return "review:merge" if verdict.startswith("merge-into:") else SIMPLE[verdict]


def parse_model_output(text):
    """Pull the first JSON object out of the model text (tolerates a code fence)."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    start = text.find("{")
    if start < 0:
        raise ReviewError("no JSON object in output")
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
    except ValueError as e:
        raise ReviewError("invalid JSON: %s" % e)
    return obj


def _ts(value):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


def is_reviewer_comment(c):
    """Our comment: marker plus a bot or maintainer author (an outsider pasting the marker is ignored)."""
    if MARKER not in (c.get("body") or ""):
        return False
    return (c.get("user") or {}).get("type") == "Bot" or c.get("author_association") in TRUSTED_ASSOC


def is_lesson(issue):
    if "pull_request" in issue or issue.get("state", "open") != "open":
        return False
    names = {lb.get("name") for lb in issue.get("labels") or []}
    return "lesson" in names or str(issue.get("title") or "").startswith("[lesson]")


def needs_review(issue, comments):
    """True when a lesson issue has no review:* label, no reviewer comment, or was edited after the last one."""
    if not is_lesson(issue):
        return False
    names = {lb.get("name") or "" for lb in issue.get("labels") or []}
    if not any(n.startswith("review:") for n in names):
        return True
    mine = [c for c in comments or [] if is_reviewer_comment(c)]
    if not mine:
        return True
    last = max(_ts(c.get("updated_at") or c["created_at"]) for c in mine)
    return _ts(issue["updated_at"]) > last + EDIT_SLACK


def select_issues(issues, comments_by_number, limit=MAX_PER_RUN):
    """Oldest first, at most `limit`. Pure function on issue / comment JSON."""
    todo = [i for i in issues if needs_review(i, comments_by_number.get(i["number"]))]
    todo.sort(key=lambda i: (i["created_at"], i["number"]))
    return todo[:limit]


def render_comment(verdict, reason, when=None):
    safe = re.sub(r"@(?=\w)", "@​", reason)
    quoted = "\n".join("> " + ln for ln in safe.splitlines() if ln.strip())
    return (
        "%s\n**Lesson review: `%s`**\n\n%s\n\n"
        "_Automated first pass. Nothing is merged automatically: a maintainer batches "
        "accepted lessons into an AGENTS.md PR (see `.github/CONTRIBUTING.md`)._"
        % (MARKER, verdict, quoted)
    ) + (("\n_Reviewed %s._" % when) if when else "")


def read_agents():
    with open(os.path.join(ROOT, "AGENTS.md"), encoding="utf-8") as f:
        return f.read()


def section_numbers(agents):
    return {int(m.group(1)) for m in re.finditer(r"^## (\d+)\.", agents, re.M)}


def build_payload(issue, agents):
    with open(os.path.join(ROOT, "hive", "prompts", "review.md"), encoding="utf-8") as f:
        system = f.read()
    data = {
        "title": str(issue.get("title") or "")[:MAX_TITLE],
        "body": str(issue.get("body") or "")[:MAX_BODY],
    }
    user = "<agents_md>\n%s\n</agents_md>\n\n<lesson_issue>\n%s\n</lesson_issue>\n" % (
        agents, json.dumps(data, ensure_ascii=False, indent=1))
    return system, user


def http(method, url, token=None, body=None, headers=None):
    h = {"Accept": "application/vnd.github+json", "User-Agent": "thriae-review"}
    if token:
        h["Authorization"] = "Bearer " + token
    h.update(headers or {})
    data = json.dumps(body).encode() if body is not None else None
    if data:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    return json.loads(raw) if raw else None


def gh(method, path, body=None):
    repo = os.environ["GITHUB_REPOSITORY"]
    return http(method, "https://api.github.com/repos/%s/%s" % (repo, path),
                os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"), body)


def load_issue(args):
    if args.issue_file:
        with open(args.issue_file, encoding="utf-8") as f:
            return json.load(f)
    if args.env:
        return {"title": os.environ.get("ISSUE_TITLE", ""), "body": os.environ.get("ISSUE_BODY", "")}
    if args.issue:
        if os.environ.get("GITHUB_REPOSITORY") and (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")):
            d = gh("GET", "issues/%d" % args.issue)
        else:
            out = subprocess.run(["gh", "api", "repos/%s/issues/%d" % (args.repo, args.issue)],
                                 capture_output=True, text=True, check=True).stdout
            d = json.loads(out)
        return {"title": d.get("title"), "body": d.get("body")}
    sys.exit("choose --issue N, --env or --issue-file")


def call_model(system, user):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        body = {"model": MODEL, "max_tokens": 700, "system": system,
                "messages": [{"role": "user", "content": user}]}
        d = http("POST", "https://api.anthropic.com/v1/messages", None, body,
                 {"x-api-key": key, "anthropic-version": "2023-06-01"})
        return "".join(b.get("text", "") for b in d.get("content", []))
    if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        # Claude Code CLI with every tool disabled: it can only return text.
        cmd = ["claude", "-p", "--model", MODEL, "--tools", "", "--disable-slash-commands",
               "--append-system-prompt", system]
        return subprocess.run(cmd, input=user, capture_output=True, text=True,
                              check=True, timeout=300).stdout
    sys.exit("reviewer secret not set")


def fetch_all(path, pages=5):
    out = []
    for n in range(1, pages + 1):
        chunk = gh("GET", "%s%sper_page=100&page=%d" % (path, "&" if "?" in path else "?", n))
        out += chunk
        if len(chunk) < 100:
            break
    return out


def select_from_target(only=None):
    if only:
        d = gh("GET", "issues/%d" % only)
        return [d] if "pull_request" not in d else []
    issues = fetch_all("issues?state=open&sort=created&direction=asc")
    comments = {}
    for i in issues:
        if is_lesson(i) and any((lb.get("name") or "").startswith("review:") for lb in i.get("labels") or []):
            comments[i["number"]] = fetch_all("issues/%d/comments" % i["number"])
    return select_issues(issues, comments)


def review_batch(path, out):
    with open(path, encoding="utf-8") as f:
        issues = json.load(f)[:MAX_PER_RUN]
    agents = read_agents()
    results = []
    for issue in issues:
        try:
            system, user = build_payload(issue, agents)
            verdict, reason = validate(parse_model_output(call_model(system, user)))
            m = MERGE_RE.match(verdict)
            if m and int(m.group(1)) not in section_numbers(agents):
                raise ReviewError("merge-into section does not exist")
            results.append({"number": int(issue["number"]), "verdict": verdict, "reason": reason})
            print("#%s: %s" % (issue["number"], verdict))
        except (ReviewError, subprocess.SubprocessError, urllib.error.URLError) as e:
            print("#%s: review failed, nothing will be posted (%s)" % (issue.get("number"), type(e).__name__))
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f)
    return results


def post_all(path):
    with open(path, encoding="utf-8") as f:
        items = json.load(f)
    if not isinstance(items, list):
        sys.exit("verdict file must be a list")
    for it in items[:MAX_PER_RUN]:
        if not isinstance(it, dict) or not isinstance(it.get("number"), int) or it["number"] < 1:
            print("skipping bad entry")
            continue
        post({k: it.get(k) for k in ("verdict", "reason")}, it["number"])


def post(obj, number):
    verdict, reason = validate(obj)
    label = label_for(verdict)
    for name, color in LABELS.items():
        try:
            gh("POST", "labels", {"name": name, "color": color})
        except urllib.error.HTTPError as e:
            if e.code != 422:  # already exists
                raise
    for lb in gh("GET", "issues/%d/labels?per_page=100" % number):
        if lb["name"].startswith("review:") and lb["name"] != label:
            gh("DELETE", "issues/%d/labels/%s" % (number, urllib.parse.quote(lb["name"], safe="")))
    gh("POST", "issues/%d/labels" % number, {"labels": [label]})
    text = render_comment(verdict, reason, datetime.utcnow().strftime("%Y-%m-%d %H:%MZ"))
    for c in gh("GET", "issues/%d/comments?per_page=100" % number):
        if is_reviewer_comment(c):
            gh("PATCH", "issues/comments/%d" % c["id"], {"body": text})
            break
    else:
        gh("POST", "issues/%d/comments" % number, {"body": text})
    print("posted verdict %s on #%d" % (verdict, number))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--issue", type=int)
    p.add_argument("--repo", default="sunososobro-hub/thriae-staging")
    p.add_argument("--env", action="store_true", help="read ISSUE_TITLE / ISSUE_BODY from the environment")
    p.add_argument("--issue-file")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--call", action="store_true")
    p.add_argument("--out")
    p.add_argument("--post")
    p.add_argument("--select")
    p.add_argument("--only", type=int)
    p.add_argument("--review-batch")
    a = p.parse_args()
    if a.post:
        return post_all(a.post)
    if a.select:
        todo = select_from_target(a.only)
        with open(a.select, "w", encoding="utf-8") as f:
            json.dump([{"number": i["number"], "title": i.get("title"), "body": i.get("body")} for i in todo], f)
        print("%d lesson issue(s) to review" % len(todo))
        return
    if a.review_batch:
        review_batch(a.review_batch, a.out)
        return
    agents = read_agents()
    system, user = build_payload(load_issue(a), agents)
    if a.dry_run or not a.call:
        print("=== SYSTEM ===\n%s\n=== USER ===\n%s\n=== model: %s, no tools, no API call made ==="
              % (system, user, MODEL))
        return
    try:
        verdict, reason = validate(parse_model_output(call_model(system, user)))
        m = MERGE_RE.match(verdict)
        if m and int(m.group(1)) not in section_numbers(agents):
            raise ReviewError("merge-into section does not exist")
    except (ReviewError, subprocess.SubprocessError, urllib.error.URLError) as e:
        sys.exit("review failed, nothing will be posted: %s" % type(e).__name__)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"verdict": verdict, "reason": reason}, f)
    print("verdict:", verdict)


if __name__ == "__main__":
    main()
