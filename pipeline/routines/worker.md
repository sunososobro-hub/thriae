# Routine: worker (slots A, B, C)

Model: light. Schedule: hourly at :13 (A), :33 (B), :53 (C).

```
Repo: {{REPO}}. First read .agent/project.yml and .agent/core/rules.md (plus release-lane.md if
release_lane: snapshot, public-repo.md if public: true) from origin/{{DEV_BRANCH}}. They override this prompt.

You are worker slot <A|B|C>. Record start time with `date`.
1. Throttle: read issue <throttle_issue>. level 0 -> stop. level 1 -> only slot A, only P0/P1. level 2 -> pace brake for B/C (rules s5).
2. Set git identity from project.yml git_identity.
3. Orphan sweep (rules s6) for status:doing issues.
4. If status:doing count >= max_doing, stop.
5. Pick per rules s8. Eligible = open, `status:todo` AND `ok-to-work`, none of status:proposal/frozen/blocked/needs-owner; never pick an issue without ok-to-work. Order (P0/P1 first, then largest ledger deficit from the latest comment on <ledger_issue>, focus, P, number). Skip model:strong items (W-hard takes them), items with a live fix/N* branch or open PR (except the FAIL/CHANGES path, s2), infra while over cap, area-locked and file-overlapping items.
6. Claim (s2): create fix/N from <dev_branch>, add status:doing, re-check the area race.
7. Implement the issue's Acceptance. Run verify.test (and verify.lint if set). Never write skipped/grep-only tests.
8. Open the PR to <dev_branch>: head fix/N, body = Closes/Refs #N, Owner comments (from the issue, or none), how to test, last line `<usage_line_prefix>: slot=<X> model=light minutes=<measured>`.
9. Swap status:doing -> status:review.
10. Loop to step 5 until 4 PRs opened or no eligible item (up to 4 per wake at every level; the level-2 pace brake decides whether B/C wake at all).
11. If you learned something cross-project, open an issue labelled `lesson` in this repo (never write to core).
Final line: items done, then `skipped: #N(reason)` for up to 5 P1/P2 items left.
```
