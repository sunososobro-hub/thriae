#!/usr/bin/env python3
"""Lesson reviewer helper (quarantine reviewer).

Local, no API call:   python -I hive/scripts/review_lesson.py --issue N --dry-run
Workflow stages (see .github/workflows/review-lesson.yml):
  --env / --issue N / --issue-file F  choose the issue source (title and body are DATA)
  --dry-run                           print the prompt payload and exit
  --call --out FILE                   ask the model (no tools), validate, write verdict JSON
  --select FILE [--only N]            list the target's open lesson issues that need a review (max 5)
  --review-batch FILE --out FILE      ask the model for each selected issue, write verdict list
  --post FILE                         validate again, tally projects, post ONE comment + one review:* label per issue
  --tally [--issues-file F]           print distinct projects (n/3) per rule / candidate slug over all lesson issues
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
QUORUM = 3  # distinct projects needed before a rule may enter AGENTS.md (CONSTITUTION Art. 3)
SIMPLE = {
    "duplicate": "review:duplicate",
    "needs-evidence": "review:needs-evidence",
    "rejected": "review:rejected",
}
EVIDENCE_RE = re.compile(r"evidence:([A-Za-z0-9][A-Za-z0-9_.-]{0,39})")
CANDIDATE_RE = re.compile(r"candidate:(?=.{1,40}$)([a-z0-9]+(?:-[a-z0-9]+)*)")
PROJECT_RE = re.compile(r"^[ \t]*Project-ID:[ \t]*([0-9a-f]{12})[ \t]*$", re.I | re.M)
VERDICT_IN_COMMENT = re.compile(r"Lesson review: `([^`\n]{1,80})`")
# review:accepted / review:merge exist on old issues: tolerated, never created or set again.
LABELS = {
    "review:evidence": "0e8a16",
    "review:candidate": "1d76db",
    "review:duplicate": "cfd3d7",
    "review:needs-evidence": "fbca04",
    "review:rejected": "b60205",
    "quorum": "5319e7",
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
    if not valid_verdict(verdict):
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
    if verdict.startswith("evidence:"):
        return "review:evidence"
    if verdict.startswith("candidate:"):
        return "review:candidate"
    return SIMPLE[verdict]


def valid_verdict(v):
    return v in SIMPLE or bool(EVIDENCE_RE.fullmatch(v)) or bool(CANDIDATE_RE.fullmatch(v))


def project_id(body):
    """The anonymous Project-ID line of a lesson body, or None."""
    m = PROJECT_RE.search(str(body or ""))
    return m.group(1).lower() if m else None


def issue_verdict(comments):
    """Verdict parsed from the reviewer's own comment, or None (old / unreviewed issues)."""
    for c in comments or []:
        if is_reviewer_comment(c):
            m = VERDICT_IN_COMMENT.search(c.get("body") or "")
            if m and valid_verdict(m.group(1)):
                return m.group(1)
    return None


def make_records(issues, comments_by_number):
    """Lesson issues (open or closed) -> [{number, verdict, project}]. Pure."""
    out = []
    for i in issues:
        if "pull_request" in i:
            continue
        names = {lb.get("name") for lb in i.get("labels") or []}
        if "lesson" not in names and not str(i.get("title") or "").startswith("[lesson]"):
            continue
        out.append({"number": i["number"], "verdict": issue_verdict(comments_by_number.get(i["number"])),
                    "project": project_id(i.get("body"))})
    return out


def tally(records):
    """Per evidence:<rule> / candidate:<slug>: distinct projects, issue numbers, quorum. Pure.

    Same Project-ID twice = one project. No Project-ID = its own unknown project.
    `lonely_unknown` is True when the group is a single issue without a Project-ID.
    """
    groups = {}
    for r in sorted(records, key=lambda r: r["number"]):
        v = r.get("verdict")
        if not v or not (v.startswith("evidence:") or v.startswith("candidate:")):
            continue
        g = groups.setdefault(v, {"projects": set(), "issues": [], "noid": []})
        g["projects"].add(r.get("project") or "unknown-%d" % r["number"])
        g["issues"].append(r["number"])
        if not r.get("project"):
            g["noid"].append(r["number"])
    out = {}
    for k, g in sorted(groups.items()):
        out[k] = {"projects": len(g["projects"]), "needed": QUORUM, "issues": g["issues"],
                  "quorum": len(g["projects"]) >= QUORUM,
                  "lonely_unknown": len(g["issues"]) == 1 and bool(g["noid"])}
    return out


def existing_slugs(records):
    """{slug: [issue numbers]} of candidate verdicts already given (for slug reuse)."""
    out = {}
    for r in records:
        v = r.get("verdict") or ""
        if v.startswith("candidate:"):
            out.setdefault(v[len("candidate:"):], []).append(r["number"])
    return out


def format_tally(t):
    if not t:
        return "no evidence:/candidate: verdicts yet"
    return "\n".join("%s  %d/%d projects  issues %s%s" % (
        k, g["projects"], g["needed"], ",".join("%d" % n for n in g["issues"]),
        "  QUORUM" if g["quorum"] else "") for k, g in t.items())


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


def evidence_line(group):
    if not group:
        return "evidence: 0/%d projects (this verdict does not count toward a rule)" % QUORUM
    line = "evidence: %d/%d projects" % (group["projects"], QUORUM)
    if group["quorum"]:
        line += " — 3/3 — ready for an AGENTS.md PR"
    return line


def render_comment(verdict, reason, when=None, group=None):
    safe = re.sub(r"@(?=\w)", "@​", reason)
    quoted = "\n".join("> " + ln for ln in safe.splitlines() if ln.strip())
    return (
        "%s\n**Lesson review: `%s`**\n\n%s\n\n**%s**\n\n"
        "_Automated first pass. Nothing is merged automatically: a rule enters AGENTS.md only with "
        "independent evidence from 3 distinct projects (see `.github/CONTRIBUTING.md`, step 4)._"
        % (MARKER, verdict, quoted, evidence_line(group))
    ) + (("\n_Reviewed %s._" % when) if when else "")


def read_agents():
    with open(os.path.join(ROOT, "AGENTS.md"), encoding="utf-8") as f:
        return f.read()


def section_numbers(agents):
    return {int(m.group(1)) for m in re.finditer(r"^## (\d+)\.", agents, re.M)}


def build_payload(issue, agents, slugs=None):
    with open(os.path.join(ROOT, "hive", "prompts", "review.md"), encoding="utf-8") as f:
        system = f.read()
    data = {
        "title": str(issue.get("title") or "")[:MAX_TITLE],
        "body": str(issue.get("body") or "")[:MAX_BODY],
    }
    known = "\n".join("%s: issues %s" % (k, ", ".join("%d" % n for n in ns))
                      for k, ns in sorted((slugs or {}).items())) or "(none yet)"
    user = ("<agents_md>\n%s\n</agents_md>\n\n<existing_candidate_slugs>\n%s\n</existing_candidate_slugs>\n\n"
            "<lesson_issue>\n%s\n</lesson_issue>\n") % (
        agents, known, json.dumps(data, ensure_ascii=False, indent=1))
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


def collect_records():
    """All lesson issues of the target, open and closed, with the reviewer's parsed verdicts."""
    issues = [i for i in fetch_all("issues?state=all&sort=created&direction=asc&labels=lesson", pages=10)
              if "pull_request" not in i]
    comments = {i["number"]: fetch_all("issues/%d/comments" % i["number"]) for i in issues}
    return make_records(issues, comments)


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


def check_section(verdict, agents):
    m = EVIDENCE_RE.fullmatch(verdict)
    if m and m.group(1).isdigit() and int(m.group(1)) not in section_numbers(agents):
        raise ReviewError("evidence section does not exist")


def review_batch(path, out):
    with open(path, encoding="utf-8") as f:
        issues = json.load(f)[:MAX_PER_RUN]
    agents = read_agents()
    results = []
    for issue in issues:
        try:
            system, user = build_payload(issue, agents, issue.get("slugs"))
            verdict, reason = validate(parse_model_output(call_model(system, user)))
            check_section(verdict, agents)
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
    final = []
    for it in items[:MAX_PER_RUN]:
        if not isinstance(it, dict) or not isinstance(it.get("number"), int) or it["number"] < 1:
            print("skipping bad entry")
            continue
        try:
            v, r = validate({k: it.get(k) for k in ("verdict", "reason")})
        except ReviewError:
            print("skipping invalid verdict for #%d" % it["number"])
            continue
        final.append([it["number"], v, r])
    if not final:
        return
    by_num = {r["number"]: r for r in collect_records()}
    for f in final:
        by_num.setdefault(f[0], {"number": f[0], "verdict": None, "project": None})["verdict"] = f[1]
    # A lone issue without Project-ID is not evidence yet.
    for f in final:
        g = tally(list(by_num.values())).get(f[1])
        if g and g["lonely_unknown"]:
            f[1] = "needs-evidence"
            f[2] = "No Project-ID line, so no project can be counted. Add the Project-ID line from the upload prompt."
            by_num[f[0]]["verdict"] = f[1]
    t = tally(list(by_num.values()))
    for number, v, r in final:
        post({"verdict": v, "reason": r}, number, t.get(v))
    for k, g in t.items():
        if g["quorum"]:
            for n in g["issues"]:
                gh("POST", "issues/%d/labels" % n, {"labels": ["quorum"]})
                print("quorum on issue %d (%s)" % (n, k))


def post(obj, number, group=None):
    verdict, reason = validate(obj)
    label = label_for(verdict)
    for name, color in LABELS.items():
        try:
            gh("POST", "labels", {"name": name, "color": color})
        except urllib.error.HTTPError as e:
            if e.code != 422:  # already exists
                raise
    for lb in gh("GET", "issues/%d/labels?per_page=100" % number):
        stale = lb["name"].startswith("review:") and lb["name"] != label
        if lb["name"] == "quorum" and not (group and group["quorum"]):
            stale = True
        if stale:
            gh("DELETE", "issues/%d/labels/%s" % (number, urllib.parse.quote(lb["name"], safe="")))
    gh("POST", "issues/%d/labels" % number, {"labels": [label]})
    text = render_comment(verdict, reason, datetime.utcnow().strftime("%Y-%m-%d %H:%MZ"), group)
    for c in gh("GET", "issues/%d/comments?per_page=100" % number):
        if is_reviewer_comment(c):
            gh("PATCH", "issues/comments/%d" % c["id"], {"body": text})
            break
    else:
        gh("POST", "issues/%d/comments" % number, {"body": text})
    print("posted verdict %s on issue %d" % (verdict, number))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--issue", type=int)
    p.add_argument("--repo", default="sunososobro-hub/thriae")
    p.add_argument("--env", action="store_true", help="read ISSUE_TITLE / ISSUE_BODY from the environment")
    p.add_argument("--issue-file")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--call", action="store_true")
    p.add_argument("--out")
    p.add_argument("--post")
    p.add_argument("--select")
    p.add_argument("--only", type=int)
    p.add_argument("--review-batch")
    p.add_argument("--tally", action="store_true")
    p.add_argument("--issues-file", help="--tally: JSON {issues: [...], comments: {number: [...]}} instead of the API")
    a = p.parse_args()
    if a.post:
        return post_all(a.post)
    if a.tally:
        if a.issues_file:
            with open(a.issues_file, encoding="utf-8") as f:
                d = json.load(f)
            records = make_records(d["issues"], {int(k): v for k, v in d.get("comments", {}).items()})
        else:
            records = collect_records()
        print(format_tally(tally(records)))
        return
    if a.select:
        todo = select_from_target(a.only)
        slugs = existing_slugs(collect_records()) if todo else {}
        with open(a.select, "w", encoding="utf-8") as f:
            json.dump([{"number": i["number"], "title": i.get("title"), "body": i.get("body"),
                        "slugs": slugs} for i in todo], f)
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
        check_section(verdict, agents)
    except (ReviewError, subprocess.SubprocessError, urllib.error.URLError) as e:
        sys.exit("review failed, nothing will be posted: %s" % type(e).__name__)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"verdict": verdict, "reason": reason}, f)
    print("verdict:", verdict)


if __name__ == "__main__":
    main()
