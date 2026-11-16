#!/usr/bin/env python3
"""Leak guard: refuse anything private before it reaches a shared place.

Modes: --tree | --staged | --range A..B | --text FILE
Private terms come from env LEAK_BLOCKLIST or --blocklist PATH and are never
printed; findings are reported as category plus location only.
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

ALLOWED_EXT = {".md", ".py", ".sh", ".yml", ".yaml", ".json", ".txt", ".toml"}
ALLOWED_NAMES = {".leak-allow", ".gitignore", ".gitattributes"}
# Categories that no allowlist entry can ever waive.
NEVER_ALLOW = {"email", "token", "private-term", "session", "file-type", "blocklist-missing"}

OK_EMAIL = re.compile(r"[\w.+-]+@users\.noreply\.github\.com|noreply@anthropic\.com", re.I)
# The owner's public GitHub handle may appear (CODEOWNERS, commit author name);
# it is not allowed when it is the local part of an email address.
PUBLIC_HANDLE = re.compile(r"sunososobro-hub(?![\w.+-]*@)", re.I)
GENERIC = [
    ("email", re.compile(r"[\w.+%-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+", re.I)),
    ("home-path", re.compile(r"[a-z]:[\x5c/]+users[\x5c/]+\w|(?<![\w.])/users/\w|(?<![\w.])/home/\w", re.I)),
    ("token", re.compile(r"gh[pous]_[a-z0-9]{20,}|github_pat_[a-z0-9_]{20,}|sk-[a-z0-9_-]{20,}"
                         r"|akia[0-9a-z]{16}|-----begin [a-z ]*private key-----", re.I)),
    ("session", re.compile(r"claude\.ai/(?:code/)?session|session_[a-z0-9]{20,}", re.I)),
    ("issue-ref", re.compile(r"#\d+")),
]
B64 = re.compile(r"[A-Za-z0-9+/_-]{8,}={0,2}")
ENT = re.compile(r"[A-Za-z0-9_+/=-]{32,}")


def clean(s):
    s = unicodedata.normalize("NFKC", s)
    return "".join(c for c in s if unicodedata.category(c) != "Cf")


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
    def __init__(self, blocklist, allow):
        self.terms = [clean(t).casefold() for t in blocklist]
        self.allow = allow
        self.findings = []

    def add(self, where, cat, extra=""):
        self.findings.append((where, cat, extra))

    def check(self, where, text, line_no=None, path=None, depth=0, generic=True, entro=True):
        c = clean(text)
        f = PUBLIC_HANDLE.sub(" ", OK_EMAIL.sub(" ", c.casefold()))
        loc = where if line_no is None else f"{where}:{line_no}"
        lh = hashlib.sha256(c.strip().encode()).hexdigest()
        cats = set()
        for k, t in enumerate(self.terms, 1):
            if t and t in f:
                self.add(loc, "private-term", f"#{k}")
        if generic:
            for cat, rx in GENERIC:
                if rx.search(f):
                    cats.add(cat)
        if entro and depth == 0:
            for m in ENT.finditer(c):
                s = m.group(0)
                if any(x.isdigit() for x in s) and any(x.isalpha() for x in s) and entropy(s) >= 4.0:
                    cats.add("token")
        for cat in sorted(cats):
            if cat in NEVER_ALLOW or (path, lh) not in self.allow:
                self.add(loc, cat)
        if depth < 2:
            for n, t in decoded_blobs(c):
                self.check(loc + "(b64)", t, depth=depth + 1, path=path, generic=n >= 40, entro=False)

    def check_name(self, where, name):
        where = where.replace(name, "<file>")
        base = os.path.basename(name)
        ext = os.path.splitext(base)[1].lower()
        ok = (ext in ALLOWED_EXT or base in ALLOWED_NAMES or name.startswith(".github/"))
        if not ok:
            self.add(where, "file-type")
        self.check(where + "(name)", name, generic=True, entro=False)

    def check_blob(self, where, name, data):
        self.check_name(where, name)
        if b"\0" in data:
            self.add(where, "file-type")
            return
        for i, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
            self.check(where, line, i, path=name)


def git(*a, raw=False):
    r = subprocess.run(["git", *a], capture_output=True, check=True)
    return r.stdout if raw else r.stdout.decode("utf-8", "replace")


def load_allow():
    out = set()
    try:
        for ln in open(".leak-allow", encoding="utf-8"):
            ln = ln.strip()
            if ln and not ln.startswith("#") and " " in ln:
                p, h = ln.rsplit(None, 1)
                out.add((p, h))
    except OSError:
        pass
    return out


def scan_commit(sc, c):
    short = c[:10]
    meta = git("show", "-s", "--format=%an%x00%ae%x00%cn%x00%ce%x00%B", c).split("\0", 4)
    for lbl, v in zip(("author-name", "author-email", "committer-name", "committer-email"), meta[:4]):
        sc.check(f"commit {short} {lbl}", v)
    for i, line in enumerate(meta[4].splitlines(), 1):
        sc.check(f"commit {short} message", line, i)
    names = git("diff-tree", "-r", "-m", "--root", "--no-commit-id", "--name-only", "-z", c).split("\0")
    for n in sorted({x for x in names if x}):
        try:
            data = git("show", f"{c}:{n}", raw=True)
        except subprocess.CalledProcessError:
            sc.check_name(f"commit {short} {n}", n)  # deleted path
            continue
        sc.check_blob(f"commit {short} {n}", n, data)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--tree", action="store_true")
    g.add_argument("--staged", action="store_true")
    g.add_argument("--range")
    g.add_argument("--text")
    ap.add_argument("--blocklist")
    a = ap.parse_args()

    raw = os.environ.get("LEAK_BLOCKLIST", "")
    if a.blocklist:
        try:
            raw = open(a.blocklist, encoding="utf-8").read()
        except OSError:
            raw = ""
    terms = [t.strip() for t in raw.splitlines() if t.strip()]
    sc = Scanner(terms, load_allow())
    if not terms:
        sc.add("config", "blocklist-missing")

    if a.tree:
        for n in git("ls-files", "-z").split("\0"):
            if n:
                sc.check_blob("tree " + n, n, open(n, "rb").read())
    elif a.staged:
        for n in git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z").split("\0"):
            if n:
                sc.check_blob("staged " + n, n, git("show", ":" + n, raw=True))
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
        data = open(a.text, "rb").read()
        for i, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
            sc.check("text", line, i)

    for where, cat, extra in sc.findings:
        print(f"LEAK {cat} {extra} at {where}".replace("  ", " "))
    if sc.findings:
        print(f"leak_check: {len(sc.findings)} finding(s)")
        return 1
    print("leak_check: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
