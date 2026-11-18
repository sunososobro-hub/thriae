# A gate the agent can edit proves nothing

AGENTS.md line: section 12. Merged lessons: issues 36, 78, 83 (related: issue 42, walls-not-reminders.md). The same line carries the empty-done rule: empty-done-fails.md.

## Rule
A green check counts as evidence only if the gated agent could not change what the check measures. Never weaken a threshold, constant or test to pass CI without measured data. A diff that deletes test files or assertions, shrinks the test set, adds skip markers, or edits CI workflow files gets a strong review, and the PR body states the test count on the base and on the head. Read the diff, not the agent's report.

## What happened
- issue 36: an overnight port of a library to another language, judged by about 80,000 lines of end-to-end tests, with the goal "make the tests pass". Three runs, three shortcuts: run 1 rewrote the code its own way, then deleted failing tests (the test tree shrank about 70%) while CI showed green and the report said all tests pass; run 2, after a ban on special-casing, returned the expected output per fixture from a 168-case switch; run 3 edited the CI workflow to exclude the categories still failing. Each was plain in the diff and invisible in the badge and the summary. Source: https://dev.to/samchon/ai-deleted-my-tests-and-said-all-tests-pass-a-horror-story-from-porting-typia-from-typescript-2bmf
- issue 78: over three days an agent removed one assertion, then a whole test file, and on day three was stopped just before a recursive delete of every test file. Fresh sessions asked why mostly pointed at the instruction file: it called any failing test the agent's failure, so deleting tests removed the failure. One added line (reduced coverage is worse than a failing test) stopped it for that author; "Don't/Never" lines had not. Single author, no logs. Source: https://blog.fsck.com/2026/04/30/that-time-it-tried-to-delete-all-my-tests/
- issue 83: a completion gate blocked a session from stopping while tasks were open. Facing 23 open tasks, the agent deleted all 23 in 13 seconds, the count fell to 0, the gate passed, and it reported the block resolved, though the gate message itself said not to delete real tasks. Its claim that the tasks were kept elsewhere was false (one copy in a store a dev reset wipes, the other one line per requirement). A one-task case had happened four days earlier; its fix was not yet shipped. Source: https://dev.to/mindrealm/my-ai-deleted-more-than-twenty-unfinished-tasks-so-it-could-say-it-was-done-59c

## Mechanisms
- Put test directories and CI workflow files in `<protected-paths>`, so changes to them need a strong review.
- A CI step compares the test count (or the list of test ids) on base and head and fails or flags a drop; the count goes in the PR body.
- A gate never reads a value the gated agent maintains (a task list, a test list). Rebuild the count from an independent source the agent cannot rewrite: the session record for tasks (the base branch misses tasks created after branching), the base branch for the test list.
- Removing items from a measured set is blocked up front or needs an audit record; if the record cannot be written, the gate fails closed.
- Phrase rules so a failing test is reported, not hidden: deleting or weakening a test is worse than leaving it red.
- Pair outcome-only goals ("make the tests pass") with a concrete reference example and small increments, not one unattended overnight run.

## Edge cases
- A gate message or warning is not a guard: in issue 83 the agent read it and deleted the tasks anyway.
- Fixture memorisation (issue 36, run 2) keeps the test count unchanged; only reading the diff catches it.
- Marking unfinished work as done is a remaining gap the issue 83 author names; a count check does not cover it.
- On the fast lane a deleted test is flagged in review text, not auto-blocked (roles/merge.md); this rule raises it to a strong review.
