#!/usr/bin/env python3
"""Lesson gate: scan an issue's title and body with leak_check.py before it stays public.

Reads ISSUE_TITLE and ISSUE_BODY from the environment (data only, never a shell
string), writes them to a temp file and runs `leak_check.py --text` on it.
Exit 0: clean, take no action. Exit 10: leak found; the fixed rejection message is
written to --message FILE (it never quotes the issue). Any other exit: the scan itself
failed, so the workflow fails and does nothing else.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REJECT = 10

MESSAGE = """\
Thanks for sharing. This submission was not accepted because it contains
information we do not publish. The issue is closed and locked; the text is not quoted here.

Categories found: {cats}

We do not edit or redact submissions. Please remove the item yourself and
submit again. Placeholders such as <YOUR_API_KEY>, <your-email> or
C:\\Users\\<you> are fine; any real-looking email address is rejected.

If this was a real key, token or password, treat it as leaked: revoke it and
issue a new one now.

You can check before submitting: python hive/scripts/leak_check.py --text <file>

感謝分享。這則投稿含有我們不公開的資訊，所以沒有收。我們不代為修改或遮蔽，
請自行移除後重新投稿。若是真的金鑰或密碼，請視為已外洩並立即作廢重發。
"""


def scan(title, body, blocklist_env=None):
    """Return (verdict_exit_code, categories). Runs leak_check with category-only output."""
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "issue.txt")
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(f"{title}\n{body}\n")
        env = dict(os.environ)
        env["GITHUB_ACTIONS"] = "true"  # category-only output
        if blocklist_env is not None:
            env["LEAK_BLOCKLIST"] = blocklist_env
        p = subprocess.run(
            [sys.executable, os.path.join(HERE, "leak_check.py"), "--text", f,
             "--no-file-keeper", "--allow-missing-blocklist"],
            capture_output=True, text=True, env=env, cwd=d)
    cats = sorted({m.group(1) for m in re.finditer(r"^LEAK (\S+) in ", p.stdout, re.M)})
    if p.returncode == 0:
        return 0, []
    if p.returncode == 1 and cats:
        return REJECT, cats
    return p.returncode or 2, []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--message", required=True, help="file to write the rejection message to")
    a = ap.parse_args()
    code, cats = scan(os.environ.get("ISSUE_TITLE", ""), os.environ.get("ISSUE_BODY", ""))
    if code == REJECT:
        with open(a.message, "w", encoding="utf-8") as fh:
            fh.write(MESSAGE.format(cats=", ".join(cats)))
        print("lesson_gate: rejected (" + ", ".join(cats) + ")")
    elif code == 0:
        print("lesson_gate: clean")
    else:
        print("lesson_gate: scan failed", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
