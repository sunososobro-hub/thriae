# An empty done fails; review is never skipped by size

AGENTS.md line: section 12 (merged into the gates line, one in, one out). Merged lessons: issue 29 (same-owner, together with issue 58 one vote; counted with issues 139 and 140).

## Rule
Review runs on every change. Never skip or downgrade it because a diff is small, and never because of a marker the author sets. A task that was meant to change something and ends with no change to non-bookkeeping files is a failure, caught by a mechanical check in the orchestrator before the paid review runs, not by the reviewer. Every done or complete status points at something a reader can check (a diff, a file hash, a log line, a response ID); without one the status says "no checkable artifact yet". Escalate the reviewer model by what was touched (protected paths) or an explicit risk tag, not by size.

## What happened
- issue 29 (keeper's own pipeline): a proposal to save review cost would have skipped the reviewer on small diffs. The record showed the two worst failures were zero-line diffs: items ticked done with no code behind them, once eight at a time. Size did not predict defects: rejected diffs averaged about 246 changed lines, passed ones about 318. About 9% of roughly 45 real verdicts were rejects. Re-reviewing 12 passed diffs with a stronger model changed 7 verdicts, but the prompt was leading and one identical diff got opposite verdicts on two runs, so only the qualitative point stands: a second, different reviewer finds different defects. No public link.
- issue 58 (keeper's own project, same vote as issue 29): escalating by diff size sent 73 of 200 PRs to strong review, and only 5 of those (7%) got changes requested; median wait 41 minutes. Escalation by protected path replaced it (roles/merge.md, core/rules.md section 3).
- issue 139: a build agent running a three-model benchmark reported two of five tasks complete, with scores and latency comparisons. The API key had never been loaded: no audit log, no response IDs, an untouched provider balance. The same run swapped the approved scope without asking, and after the key was fixed a broken fixture scored every model 0 on one task, which looked like a real result. Source: https://dev.to/pavelbuild/my-ai-agent-told-me-the-benchmark-was-complete-it-had-never-made-a-single-api-call-1957
- issue 140: a PR-writing agent was given a test file at 100% line coverage, decided nothing could be improved and finished with zero changes. The gate ran lint, type-check and tests only on changed files, so zero files meant nothing was checked and "do nothing" passed. The existing tests only asserted a value was defined and not null. Source: https://dev.to/gitautoai/zero-changes-passed-our-quality-gate-3h43

## Mechanisms
- Orchestrator check: a done on a change task with an empty diff (bookkeeping files excluded) is reverted or rejected before review. A retry may close with no change only if it again finds nothing and states why.
- Gates that inspect only changed files also assert that the change set is non-empty for change tasks.
- Cheap mechanical checks first; the paid model review runs only after they pass.
- Status lines carry an artifact pointer; a preflight checks credentials and fixtures before a run, and uniform all-zero scores trigger a harness check before they are reported as a result (a working harness can still score every model 0).
- A scope change needs explicit confirmation, recorded on the issue.
- A small fixed share of random spot checks by a stronger model, so author and reviewer do not share blind spots.

## Edge cases
- Do not judge a reviewer-model swap by re-reviewing already-passed work with a leading prompt; verdicts on the same diff flipped between runs (issue 29).
- Some tasks legitimately end with no change (an investigation, a duplicate); they close with a stated reason, not as done work.
- Issue 29's numbers come from one pipeline and a small sample; issues 139 and 140 have no after-measurement.
- Related: gates-agent-cannot-edit.md (marking unfinished work done is the gap issue 83 names).
