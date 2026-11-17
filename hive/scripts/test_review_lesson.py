import unittest

import review_lesson as rl

OWNER = "keeper"


def issue(number, body, login=OWNER, labels=()):
    return {"number": number, "title": "t%d" % number, "body": body,
            "user": {"login": login}, "labels": [{"name": n} for n in labels]}


def records(*issues, reviewed=None):
    """Parse issues; reviewed maps number -> (verdict, counts)."""
    recs = {i["number"]: rl.parse_issue(i, OWNER) for i in issues}
    for n, (verdict, counts) in (reviewed or {}).items():
        recs[n]["verdict"], recs[n]["counts"] = verdict, counts
    return recs


def ref(n):
    """An issue reference, built here so this file holds no literal one."""
    return "#%d" % n


def sup(*numbers):
    return "Supports " + " and ".join(ref(n) for n in numbers) + "\n"


SCOUT = "Source (forager credit): https://example.org/post\n"


class ParseTest(unittest.TestCase):
    def test_supports_lines(self):
        self.assertEqual(rl.parse_supports(sup(10, 1) + "x\n" + sup(33)), [10, 1, 33])
        self.assertEqual(rl.parse_supports("Closes %s, see %s" % (ref(5), ref(6))), [])

    def test_scout_report_is_not_a_keeper_project(self):
        mine = rl.parse_issue(issue(1, "Project-ID: aaaaaaaaaaaa"), OWNER)
        scouted = rl.parse_issue(issue(2, SCOUT + "Project-ID: bbbbbbbbbbbb"), OWNER)
        self.assertTrue(mine["keeper"])
        self.assertFalse(scouted["keeper"])
        self.assertEqual(scouted["pid"], "bbbbbbbbbbbb")


class TallyTest(unittest.TestCase):
    def test_same_account_two_source_projects_are_two_votes(self):
        recs = records(issue(1, SCOUT + "Project-ID: aaaaaaaaaaaa"),
                       issue(2, SCOUT + sup(1) + "Project-ID: bbbbbbbbbbbb"),
                       reviewed={1: ("candidate:x-y-z", True), 2: ("evidence:" + ref(1), True)})
        self.assertEqual(rl.tally(1, recs)["n"], 2)

    def test_keeper_projects_together_are_one_vote(self):
        recs = records(issue(1, "Project-ID: aaaaaaaaaaaa"),
                       issue(2, sup(1) + "Project-ID: bbbbbbbbbbbb"),
                       issue(3, sup(1) + "Project-ID: cccccccccccc"),
                       reviewed={n: ("candidate:x-y-z", True) for n in (1, 2, 3)})
        result = rl.tally(1, recs)
        self.assertEqual(result["n"], 1)
        self.assertEqual(result["same_owner"], [1, 2, 3])

    def test_report_without_a_real_failure_does_not_count(self):
        recs = records(issue(1, "Project-ID: aaaaaaaaaaaa"),
                       issue(2, SCOUT + sup(1) + "Project-ID: bbbbbbbbbbbb"),
                       issue(3, SCOUT + sup(1) + "Project-ID: cccccccccccc"),
                       reviewed={1: ("needs-evidence", False), 2: ("evidence:" + ref(1), True)})
        result = rl.tally(1, recs)
        self.assertEqual(result["n"], 1)
        self.assertEqual(result["counted"], [2])
        self.assertEqual([n for n, _ in result["not_counted"]], [1, 3])

    def test_same_project_id_counts_once_and_cap_is_quorum(self):
        bodies = ["aaaaaaaaaaaa", "aaaaaaaaaaaa", "bbbbbbbbbbbb", "cccccccccccc", "dddddddddddd"]
        issues = [issue(1, SCOUT + "Project-ID: " + bodies[0])]
        issues += [issue(n, SCOUT + sup(1) + "Project-ID: " + bodies[n - 1]) for n in range(2, 6)]
        recs = records(*issues, reviewed={n: ("evidence:" + ref(1), True) for n in range(1, 6)})
        result = rl.tally(1, recs)
        self.assertEqual(result["n"], rl.QUORUM)
        self.assertIn((2, "same project as another report"), result["not_counted"])


class CommentTest(unittest.TestCase):
    def test_refresh_replaces_only_the_count(self):
        recs = records(issue(1, SCOUT + "Project-ID: aaaaaaaaaaaa"),
                       issue(2, SCOUT + sup(1) + "Project-ID: bbbbbbbbbbbb"),
                       reviewed={1: ("candidate:x-y-z", True), 2: ("evidence:" + ref(1), True)})
        old = rl.MARK + "\n**Lesson review: `candidate:x-y-z`**\n\n> why\n\n**evidence: 1/3 projects**\n\n_tail_\n"
        new = rl.refresh_comment(old, recs[1], rl.evidence_block(recs[1], rl.tally(1, recs), recs))
        self.assertIn("**evidence: 2/3 projects**", new)
        self.assertNotIn("1/3", new)
        self.assertIn("> why", new)
        self.assertIn("_tail_", new)
        again = {"verdict": None, "counts": False, "supports": []}
        rl.apply_review_state(again, new)
        self.assertEqual((again["verdict"], again["counts"]), ("candidate:x-y-z", True))
        self.assertEqual(rl.refresh_comment(new, recs[1], rl.evidence_block(recs[1], rl.tally(1, recs), recs)), new)

    def test_validate_rejects_bad_verdicts(self):
        recs = records(issue(1, ""), issue(2, ""))
        ok = {"issue": 2, "verdict": "evidence:" + ref(1), "counts": True, "supports": [1], "reason": ["real failure"]}
        self.assertEqual(rl.validate_verdict(ok, recs), [])
        self.assertTrue(rl.validate_verdict(dict(ok, verdict="great"), recs))
        self.assertTrue(rl.validate_verdict(dict(ok, verdict="rejected"), recs))  # counts must be false
        self.assertTrue(rl.validate_verdict(dict(ok, supports=[99]), recs))
        self.assertTrue(rl.validate_verdict(dict(ok, reason=["a\nb"]), recs))

    def test_select_puts_tally_movers_first(self):
        recs = records(issue(1, "Project-ID: aaaaaaaaaaaa"),
                       issue(2, "x", labels=("review:candidate",)),
                       issue(3, SCOUT + "Project-ID: bbbbbbbbbbbb"))
        self.assertEqual([r["number"] for r in rl.select_order(recs)], [3, 1])


if __name__ == "__main__":
    unittest.main()


class RetallyLabelTest(unittest.TestCase):
    def test_retally_write_sets_quorum_without_a_post(self):
        recs = records(issue(1, "Project-ID: aaaaaaaaaaaa"),
                       issue(2, SCOUT + sup(1) + "Project-ID: bbbbbbbbbbbb"),
                       issue(3, SCOUT + sup(1) + "Project-ID: cccccccccccc"),
                       reviewed={1: ("candidate:x-y-z", True), 2: ("evidence:" + ref(1), True),
                                 3: ("evidence:" + ref(1), True)})
        hive = rl.Hive.__new__(rl.Hive)
        hive.records, hive.comments, hive.labels = recs, {}, []
        for n in recs:
            hive.comments[n] = {"body": rl.MARK + "\n**evidence: 0/3 projects**"}
        hive.set_label = lambda n, name, want: hive.labels.append((n, name, want))
        hive.write_comment = lambda n, body: None
        hive.retally(write=True)
        self.assertIn((1, rl.QUORUM_LABEL, True), hive.labels)
