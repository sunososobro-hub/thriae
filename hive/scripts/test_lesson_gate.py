#!/usr/bin/env python3
"""Self-checks for lesson_gate.py (fake data only)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lesson_gate as lg  # noqa: E402

AT = "@"
FAKE_EMAIL = "someone" + AT + "corp-example.net"
FAKE_TOKEN = "".join(["gh", "p_", "a8F3kD92", "LmQx7Zp1", "Wv5Rt0Yb", "4NcE6HgJ", "2sXq"])


class LessonGateTest(unittest.TestCase):
    def test_clean_issue_no_action(self):
        code, cats = lg.scan("[lesson] retries hid a failure",
                             "Measured 3 failures before and 0 after. Use placeholders like <your-email> and <YOUR_API_KEY>.")
        self.assertEqual((code, cats), (0, []))

    def test_email_is_rejected(self):
        code, cats = lg.scan("[lesson] x", f"contact me at {FAKE_EMAIL}")
        self.assertEqual(code, lg.REJECT)
        self.assertTrue(cats)

    def test_token_in_title_is_rejected(self):
        code, _ = lg.scan(f"[lesson] key {FAKE_TOKEN}", "body")
        self.assertEqual(code, lg.REJECT)

    def test_blocklist_term_is_rejected(self):
        code, _ = lg.scan("[lesson] x", "we saw it at Zebrafoo Corp", blocklist_env="zebrafoo\n")
        self.assertEqual(code, lg.REJECT)

    def _run(self, title, body):
        with tempfile.TemporaryDirectory() as d:
            msg = os.path.join(d, "m.txt")
            ev = os.path.join(d, "event.json")
            with open(ev, "w", encoding="utf-8") as fh:
                json.dump({"issue": {"title": title, "body": body}}, fh)
            env = dict(os.environ, GITHUB_EVENT_PATH=ev)
            p = subprocess.run([sys.executable, os.path.join(HERE, "lesson_gate.py"), "--message", msg],
                               capture_output=True, text=True, env=env)
            text = open(msg, encoding="utf-8").read() if os.path.exists(msg) else None
            return p, text

    def test_cli_reject_writes_fixed_message_without_quoting(self):
        p, text = self._run("t", f"mail {FAKE_EMAIL}")
        self.assertEqual(p.returncode, lg.REJECT)
        self.assertIsNotNone(text)
        self.assertNotIn("corp-example", text)
        self.assertNotIn("corp-example", p.stdout + p.stderr)
        self.assertIn("Thanks for sharing", text)

    def test_cli_clean_writes_no_message(self):
        p, text = self._run("t", "plain lesson text")
        self.assertEqual(p.returncode, 0)
        self.assertIsNone(text)

    SLUG = "https://dev.to/someauthor/how-i-rebuilt-my-agent-loop-in-2026-with-8-small-rules-4k9x2m7qzp1"

    def test_evidence_url_with_long_slug_is_clean(self):
        code, _ = lg.scan("[lesson] x", f"Evidence: {self.SLUG} and {self.SLUG}/")
        self.assertEqual(code, 0)

    def test_token_in_url_query_still_rejected(self):
        code, cats = lg.scan("[lesson] x", f"see {self.SLUG}?key=" + "".join(["Zk3Qp9Xv", "2Lm8Rt5Y", "b7Nc4Hd6", "Jf1Wg0Sa"]))
        self.assertEqual(code, lg.REJECT)
        self.assertIn("token", cats)

    def test_empty_body_is_clean(self):
        self.assertEqual(lg.scan("[lesson] x", "")[0], 0)
        p, text = self._run("[lesson] x", None)
        self.assertEqual(p.returncode, 0)
        self.assertIsNone(text)

    def test_very_long_body_is_clean_and_not_via_env(self):
        p, text = self._run("[lesson] x", "plain words here. " * 20000)
        self.assertEqual(p.returncode, 0)
        self.assertIsNone(text)


if __name__ == "__main__":
    unittest.main()
