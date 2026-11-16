#!/usr/bin/env python3
"""Leak guard: refuse anything private before it reaches a shared place.

Modes: --tree | --staged | --range A..B | --text FILE
Private terms come from env LEAK_BLOCKLIST or --blocklist PATH and are never
printed; findings are reported as category plus location only. In CI
(GITHUB_ACTIONS=true or --ci) only the category and the file are printed,
never a term index or a line number.

Private terms are matched on the unmasked text, again with every
non-alphanumeric character removed (catches `foo bar` / `foo-bar` for
`foobar`), and across each pair of adjacent lines. The keeper's public handle
(--keeper, env THRIAE_KEEPER_HANDLE, or a `keeper: <handle>` line in
hive/.leak-allow) and its noreply address are excused only
where they appear whole; they are masked only for the generic email rule.
The issue-ref rule (a hash followed by digits) applies to file content only, never to commit
messages or --text, and `Closes/Fixes/Refs #N` is always allowed.
Issues and comments are not scanned by CI: run --text on anything you post.

Limits (what it cannot catch):
- Private terms that are not in the blocklist; the blocklist is only as good as you keep it.
- Paraphrase, translation, abbreviation or a description that identifies a person or project
  without naming it.
- Text inside images, binaries or archives (these file types are refused, not read).
- Encodings other than base64 (hex, rot13, compression, encryption), and terms split across more
  than two lines or across files.
- Issues, comments, wiki, releases and anything posted outside git, unless you run --text on it.
- Fork and Dependabot PRs: no secrets, so only the generic checks run there.
- History that was already pushed: it reports, it cannot un-publish.
"""
import argparse
import base64
import binascii
import hashlib
import math
import os
import re
import subprocess
import sys
import unicodedata

DEFAULT_KEEPER = "sunososobro-hub"
ALLOWED_EXT = {".md", ".py", ".sh", ".yml", ".yaml", ".json", ".txt", ".toml", ".svg"}
ALLOWED_NAMES = {".leak-allow", ".gitignore", ".gitattributes", "LICENSE"}
ALLOW_FILE = os.path.join("hive", ".leak-allow")
# Categories that no allowlist entry can ever waive.
NEVER_ALLOW = {"email", "token", "private-term", "session", "file-type", "blocklist-missing"}

# Addresses that may appear anywhere: GitHub noreply (users and the web-flow
# committer) and the agent tool's documented noreply identity.
OK_EMAIL = re.compile(r"[\w.+-]+@users\.noreply\.github\.com"
                      r"|(?<![\w.+-])noreply@(?:github|anthropic)\.com(?![\w.-])", re.I)
LINK_REF = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?|refs?)\s+#\d+", re.I)
GENERIC = [
    ("email", re.compile(r"[\w.+%-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+", re.I)),
    ("home-path", re.compile(r"[a-z]:[\x5c/]+users[\x5c/]+\w|(?<![\w.])/users/\w|(?<![\w.])/home/\w", re.I)),
    ("token", re.compile(r"gh[pous]_[a-z0-9]{20,}|github_pat_[a-z0-9_]{20,}|sk-[a-z0-9_-]{20,}"
                         r"|akia[0-9a-z]{16}|-----begin [a-z ]*private key-----", re.I)),
    ("session", re.compile(r"claude\.ai/(?:code/)?session|session_[a-z0-9]{20,}", re.I)),
]
ISSUE_REF = re.compile(r"#\d+")
B64 = re.compile(r"[A-Za-z0-9+/_-]{8,}={0,2}")
ENT = re.compile(r"[A-Za-z0-9_+/=-]{32,}")
NON_ALNUM = re.compile(r"[\W_]+")
URL_PATH = re.compile(r"https?://[^\s?#]+", re.I)
URL_ID = re.compile(r"/\d+(?=/|$)")


def drop_url_ids(s):
    """Blank digit-only path segments of http(s) URLs (post IDs); query strings stay."""
    return URL_PATH.sub(lambda m: URL_ID.sub("/", m.group(0)), s)


def clean(s):
    s = unicodedata.normalize("NFKC", s)
    return "".join(c for c in s if unicodedata.category(c) != "Cf")


def squash(s):
    return NON_ALNUM.sub("", s)


def keeper_rx(handle):
    h = re.escape(clean(handle).casefold())
    # Whole handle, or its noreply address; never the local part of another address.
    return re.compile(rf"(?:\d+\+)?{h}@users\.noreply\.github\.com|(?<![\w-]){h}(?![\w-])(?![\w.+-]*@)")


def entropy(s):
    n = len(s)
    return -sum(s.count(c) / n * math.log2(s.count(c) / n) for c in set(s))


def printable(b):
    t = b.decode("utf-8", "replace")
    return t if sum(c.isprintable() or c in "\n\t" for c in t) >= 0.9 * max(len(t), 1) else None


def decoded_blobs(text):
    for m in B64.finditer(text):
        run = m.group(0).rstrip("=")
        raw = run.replace("-", "+").replace("_", "/")
        raw += "=" * (-len(raw) % 4)
        try:
            t = printable(base64.b64decode(raw, validate=True))
        except (binascii.Error, ValueError):
            continue
        if t:
            yield len(run), t


class Scanner:
    def __init__(self, blocklist, allow, keeper=DEFAULT_KEEPER):
        self.terms = [clean(t).casefold() for t in blocklist]
        self.sterms = [squash(t) for t in self.terms]
        self.allow = allow
        self.keeper = keeper_rx(keeper)
        self.findings = []

    def add(self, src, line, cat, extra=""):
        self.findings.append((src, line, cat, extra))

    def term_hits(self, text):
        """Indexes of private terms in text (cleaned, casefolded, unmasked)."""
        spans = [m.span() for m in self.keeper.finditer(text)]
        hits = set()
        for k, t in enumerate(self.terms, 1):
            i = text.find(t) if t else -1
            while i != -1:
                if not any(a <= i and i + len(t) <= b for a, b in spans):
                    hits.add(k)
                    break
                i = text.find(t, i + 1)
        parts = [squash(p) for p in self.keeper.split(text)]
        for k, t in enumerate(self.sterms, 1):
            if t and any(t in p for p in parts):
                hits.add(k)
        return hits

    def check(self, src, text, line=None, path=None, depth=0, generic=True, entro=True, refs=False):
        c = clean(text)
        cf = c.casefold()
        for k in sorted(self.term_hits(cf)):
            self.add(src, line, "private-term", f"#{k}")
        cats = set()
        if generic:
            f = self.keeper.sub(" ", OK_EMAIL.sub(" ", cf))
            for cat, rx in GENERIC:
                if rx.search(f):
                    cats.add(cat)
            if refs and ISSUE_REF.search(LINK_REF.sub(" ", f)):
                cats.add("issue-ref")
        if entro and depth == 0:
            for m in ENT.finditer(drop_url_ids(c)):
                s = m.group(0)
                if any(x.isdigit() for x in s) and any(x.isalpha() for x in s) and entropy(s) >= 4.0:
                    cats.add("token")
        lh = hashlib.sha256(c.strip().encode()).hexdigest()
        for cat in sorted(cats):
            if cat in NEVER_ALLOW or (path, lh) not in self.allow:
                self.add(src, line, cat)
        if depth < 2:
            for n, t in decoded_blobs(c):
                self.check(src, t, line, path=path, depth=depth + 1, generic=n >= 40, entro=False)

    def check_lines(self, src, text, path=None, refs=False):
        lines = text.splitlines()
        for i, ln in enumerate(lines, 1):
            self.check(src, ln, i, path=path, refs=refs)
        # Terms split across a line break.
        prev = None
        for i, ln in enumerate(lines, 1):
            cur = clean(ln).casefold()
            if prev is not None:
                new = self.term_hits(prev + "\n" + cur) - self.term_hits(prev) - self.term_hits(cur)
                for k in sorted(new):
                    self.add(src, i - 1, "private-term", f"#{k}")
            prev = cur

    def check_name(self, src, name):
        """Check a path; returns the label to show for it (redacted if dirty)."""
        before = len(self.findings)
        base = os.path.basename(name)
        ext = os.path.splitext(base)[1].lower()
        if not (ext in ALLOWED_EXT or base in ALLOWED_NAMES or name.startswith(".github/")):
            self.add(f"{src} <file>", None, "file-type")
        self.check(f"{src} <file>(name)", name, entro=False)
        return name if len(self.findings) == before else "<file>"

    def check_blob(self, src, name, data):
        shown = self.check_name(src, name)
        if b"\0" in data:
            self.add(f"{src} {shown}", None, "file-type")
            return
        self.check_lines(f"{src} {shown}", data.decode("utf-8", "replace"), path=name, refs=True)


ROOT = "."


def git(*a, raw=False):
    r = subprocess.run(["git", "-C", ROOT, *a], capture_output=True, check=True)
    return r.stdout if raw else r.stdout.decode("utf-8", "replace")


def load_allow(path):
    """Returns ({(path, line_hash)}, keeper handle or None)."""
    out, keeper = set(), None
    try:
        for ln in open(path, encoding="utf-8"):
            ln = ln.strip()
            if ln.startswith("keeper:"):
                keeper = ln.split(":", 1)[1].strip() or None
            elif ln and not ln.startswith("#") and " " in ln:
                p, h = ln.rsplit(None, 1)
                out.add((p, h))
    except OSError:
        pass
    return out, keeper


def pick_keeper(arg, env, file_keeper, ignore_file=False):
    """--keeper, then env, then the allow file's `keeper:` line (unless ignored), then the default."""
    return arg or env or (None if ignore_file else file_keeper) or DEFAULT_KEEPER


def scan_commit(sc, c):
    short = c[:10]
    meta = git("show", "-s", "--format=%an%x00%ae%x00%cn%x00%ce%x00%B", c).split("\0", 4)
    for lbl, v in zip(("author-name", "author-email", "committer-name", "committer-email"), meta[:4]):
        sc.check(f"commit {short} {lbl}", v)
    sc.check_lines(f"commit {short} message", meta[4])
    names = git("diff-tree", "-r", "-m", "--root", "--no-commit-id", "--name-only", "-z", c).split("\0")
    for n in sorted({x for x in names if x}):
        try:
            data = git("show", f"{c}:{n}", raw=True)
        except subprocess.CalledProcessError:
            sc.check_name(f"commit {short}", n)  # deleted path
            continue
        sc.check_blob(f"commit {short}", n, data)


def report(findings, ci):
    seen = set()
    for src, line, cat, extra in findings:
        if ci:
            msg = f"LEAK {cat} in {src}"
        else:
            loc = src if line is None else f"{src}:{line}"
            msg = f"LEAK {cat} {extra} at {loc}".replace("  ", " ")
        if msg not in seen:
            seen.add(msg)
            print(msg)


def main():
    global ROOT
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--tree", action="store_true")
    g.add_argument("--staged", action="store_true")
    g.add_argument("--range")
    g.add_argument("--text")
    ap.add_argument("--blocklist")
    ap.add_argument("--allow-file", help=f"default: <repo root>/{ALLOW_FILE}")
    ap.add_argument("--keeper", help="keeper's public handle (default: env THRIAE_KEEPER_HANDLE, "
                    "then `keeper:` in the allow file, then the built-in default)")
    ap.add_argument("--no-file-keeper", action="store_true",
                    help="ignore the `keeper:` line in the allow file (CI: a PR could edit it)")
    ap.add_argument("--ci", action="store_true", default=os.environ.get("GITHUB_ACTIONS") == "true",
                    help="print only category and file (default when GITHUB_ACTIONS=true)")
    ap.add_argument("--allow-missing-blocklist", action="store_true",
                    help="run only the generic checks when no blocklist is available (fork PRs)")
    a = ap.parse_args()

    text_data = open(a.text, "rb").read() if a.text else None
    try:
        ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                              check=True, text=True).stdout.strip() or "."
    except (OSError, subprocess.CalledProcessError):
        ROOT = "."

    raw = os.environ.get("LEAK_BLOCKLIST", "")
    if a.blocklist:
        try:
            raw = open(a.blocklist, encoding="utf-8").read()
        except OSError:
            raw = ""
    terms = [t.strip() for t in raw.splitlines() if t.strip()]
    allow, cfg_keeper = load_allow(a.allow_file or os.path.join(ROOT, ALLOW_FILE))
    keeper = pick_keeper(a.keeper, os.environ.get("THRIAE_KEEPER_HANDLE"), cfg_keeper, a.no_file_keeper)
    sc = Scanner(terms, allow, keeper)
    if not terms:
        if a.allow_missing_blocklist:
            print("::notice::leak_check: no blocklist available; ran the generic checks only")
        else:
            sc.add("config", None, "blocklist-missing")

    if a.tree:
        for n in git("ls-files", "-z").split("\0"):
            if n:
                with open(os.path.join(ROOT, n), "rb") as fh:
                    sc.check_blob("tree", n, fh.read())
    elif a.staged:
        for n in git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").split("\0"):
            if n:
                sc.check_blob("staged", n, git("show", ":" + n, raw=True))
    elif a.range:
        spec = a.range
        if ".." in spec:
            lo, hi = spec.split("..", 1)
            rev = ["rev-list", "--reverse", hi] if set(lo) <= {"0"} else ["rev-list", "--reverse", spec]
        else:
            rev = ["rev-list", "--reverse", spec]
        for c in git(*rev).split():
            scan_commit(sc, c)
    else:
        sc.check_lines("text", text_data.decode("utf-8", "replace"))

    report(sc.findings, a.ci)
    if sc.findings:
        print(f"leak_check: {len(sc.findings)} finding(s)")
        return 1
    print("leak_check: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
