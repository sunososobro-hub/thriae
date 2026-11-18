"""Evidence-quality gate on the rule files and AGENTS.md (.github/CONTRIBUTING.md step 4b).

Runs in CI with the other tests. It checks the shape a promotion must leave behind:
- every hive/rules/<theme>.md has a Status line and a tally `N projects (k measured)`;
- a file with `Status: rule` has N >= QUORUM and k >= MIN_MEASURED;
- every source under `## What happened` is tagged [measured] or [anecdote];
- the Edge cases section has a Counter-search line;
- AGENTS.md links only rule-status files, and each line is at most MAX_LINE characters
  without its `Detail:` link.
"""
import os
import re
import unittest

import review_lesson

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RULES = os.path.join(ROOT, "hive", "rules")
AGENTS = os.path.join(ROOT, "AGENTS.md")
MAX_LINE = 200             # characters per AGENTS.md line, Detail link excluded

STATUS_RE = re.compile(r"^Status: (rule|candidate)\b.*?Tally: (\d+) projects \((\d+) measured\)", re.M)
SECTION_RE = re.compile(r"^## (.+)$", re.M)
TAGGED_RE = re.compile(r"^- \[(measured|anecdote)\] issue \d+")
DETAIL_RE = re.compile(r"\s*Detail: \S+(?: and \S+)?$")
LINK_RE = re.compile(r"hive/rules/([a-z0-9-]+)\.md")


def rule_files():
    return sorted(f for f in os.listdir(RULES) if f.endswith(".md") and f != "README.md")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def sections(text):
    parts = SECTION_RE.split(text)
    return {parts[i].strip(): parts[i + 1] for i in range(1, len(parts), 2)}


class RuleFileTest(unittest.TestCase):
    def test_every_file_has_status_and_tally(self):
        for name in rule_files():
            with self.subTest(name):
                m = STATUS_RE.search(read(os.path.join(RULES, name)))
                self.assertIsNotNone(m, "missing `Status: ... Tally: N projects (k measured)` line")
                if m.group(1) == "rule":
                    self.assertGreaterEqual(int(m.group(2)), review_lesson.QUORUM)
                    self.assertGreaterEqual(int(m.group(3)), review_lesson.MIN_MEASURED,
                                            "a rule needs a measured vote; demote it to candidate")

    def test_tally_matches_the_tags(self):
        for name in rule_files():
            with self.subTest(name):
                text = read(os.path.join(RULES, name))
                tagged = sections(text).get("What happened", "")
                measured_tags = len(re.findall(r"^- \[measured\]", tagged, re.M))
                claimed = int(STATUS_RE.search(text).group(3))
                # Keeper-owned reports share one vote, so tags may exceed the tally, never fall short.
                self.assertGreaterEqual(measured_tags, claimed)

    def test_every_source_is_tagged(self):
        for name in rule_files():
            with self.subTest(name):
                happened = sections(read(os.path.join(RULES, name))).get("What happened", "")
                bullets = [l for l in happened.splitlines() if l.startswith("- ")]
                self.assertTrue(bullets, "no sources listed")
                for line in bullets:
                    self.assertRegex(line, TAGGED_RE, "untagged source: " + line[:60])

    def test_counter_search_recorded(self):
        for name in rule_files():
            with self.subTest(name):
                edge = sections(read(os.path.join(RULES, name))).get("Edge cases", "")
                self.assertIn("Counter-search", edge)


class AgentsFileTest(unittest.TestCase):
    def test_lines_are_short(self):
        for n, line in enumerate(read(AGENTS).splitlines(), 1):
            with self.subTest(line=n):
                self.assertLessEqual(len(DETAIL_RE.sub("", line)), MAX_LINE)

    def test_links_only_rules(self):
        for slug in LINK_RE.findall(read(AGENTS)):
            with self.subTest(slug):
                path = os.path.join(RULES, slug + ".md")
                self.assertTrue(os.path.exists(path), "broken link")
                self.assertEqual(STATUS_RE.search(read(path)).group(1), "rule",
                                 "AGENTS.md links a candidate file")


if __name__ == "__main__":
    unittest.main()
