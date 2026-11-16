#!/usr/bin/env python3
"""Self-checks for leak_check.py. Run: python -m unittest discover -s hive/scripts"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import leak_check as lc  # noqa: E402

AT = "@"
HASH = "#"
TERM = "zebrafoo"
KEEPER = "keeper-bee"
NOREPLY = "12345+" + KEEPER + AT + "users.noreply.github.com"


def cats(text, blob=False, terms=(TERM,)):
    sc = lc.Scanner(list(terms), set(), KEEPER)
    if blob:
        sc.check_blob("tree", "doc.md", text.encode())
    else:
        sc.check_lines("text", text)
    return {f[2] for f in sc.findings}


class LeakCheckTest(unittest.TestCase):
    def test_url_numeric_id_not_token(self):
        self.assertEqual(cats("see https://x.com/someuser/status/2048103471019434248 for the post"), set())
        self.assertEqual(cats("https://x.com/someuser/status/2048103471019434248/photo/1"), set())

    def test_url_secrets_still_flagged(self):
        sec = "a8F3kD92LmQx7Zp1Wv5Rt0Yb4NcE6HgJ"
        for u in ("https://example.org/p?token=" + sec,
                  "https://example.org/p/status/2048103471019434248?key=" + sec,
                  "https://example.org/p?access_token=" + sec,
                  "https://example.org/hook/" + sec):
            self.assertIn("token", cats(u), u)

    def test_clean_text(self):
        self.assertEqual(cats("nothing to see here"), set())

    def test_term_plain_and_case(self):
        self.assertIn("private-term", cats("a ZebraFoo b"))

    def test_term_with_separators(self):
        self.assertIn("private-term", cats("zebra foo"))
        self.assertIn("private-term", cats("zebra-foo"))

    def test_term_across_lines(self):
        self.assertIn("private-term", cats("zebra\nfoo"))

    def test_term_hidden_in_noreply_is_caught(self):
        self.assertIn("private-term", cats("1+" + TERM + AT + "users.noreply.github.com"))

    def test_keeper_handle_and_noreply_pass(self):
        self.assertEqual(cats("author " + KEEPER + " " + NOREPLY, terms=("keeper",)), set())

    def test_keeper_handle_as_other_email_fails(self):
        self.assertIn("email", cats(KEEPER + AT + "example.com"))

    def test_keeper_handle_with_suffix_is_not_excused(self):
        self.assertIn("private-term", cats(KEEPER + "x", terms=("keeper",)))

    def test_issue_ref_only_in_file_content(self):
        self.assertEqual(cats("see " + HASH + "12"), set())
        self.assertIn("issue-ref", cats("see " + HASH + "12", blob=True))
        self.assertEqual(cats("Closes " + HASH + "12", blob=True), set())

    def test_ci_report_hides_term_index_and_line(self):
        sc = lc.Scanner([TERM], set(), KEEPER)
        sc.check_blob("tree", "doc.md", ("x\n" + TERM + "\n").encode())
        lines = []
        lc.print = lines.append
        try:
            lc.report(sc.findings, ci=True)
        finally:
            del lc.print
        self.assertEqual(lines, ["LEAK private-term in tree doc.md"])

    def test_tool_noreply_addresses_pass(self):
        self.assertEqual(cats("noreply" + AT + "github.com"), set())
        self.assertEqual(cats("noreply" + AT + "anthropic.com"), set())
        self.assertIn("email", cats("someone" + AT + "github.com"))
        self.assertIn("email", cats("x.noreply" + AT + "github.com"))
        self.assertIn("email", cats("noreply" + AT + "github.com.evil.org"))

    def test_file_keeper_can_be_ignored(self):
        self.assertEqual(lc.pick_keeper(None, None, "file-bee"), "file-bee")
        self.assertEqual(lc.pick_keeper(None, None, "file-bee", ignore_file=True), lc.DEFAULT_KEEPER)
        self.assertEqual(lc.pick_keeper("var-bee", None, "file-bee", ignore_file=True), "var-bee")
        self.assertEqual(lc.pick_keeper("", "", "file-bee", ignore_file=True), lc.DEFAULT_KEEPER)


if __name__ == "__main__":
    unittest.main()
