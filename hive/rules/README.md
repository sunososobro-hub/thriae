# Rule details (lazy loading)

`AGENTS.md` stays slim: one short line per theme, plus a full URL to the detail file here. Open a detail file when its topic comes up. Nothing learned is dropped: each file keeps every merged lesson (issue numbers, what happened, source links, concrete mechanisms, edge cases). The 250-line cap counts `AGENTS.md` only, not these files. Background: idea issue 40 (rulebook as folder blocks).

Full URLs are used in `AGENTS.md` because relative paths broke in role files (issue 38).

Each file starts with `Status: rule` or `Status: candidate` and its tally, `N projects (k measured)`. A rule needs k of at least 1, tags every source `[measured]` or `[anecdote]` and records a counter-example search in its Edge cases (`.github/CONTRIBUTING.md` step 4b). Candidate files are kept here so old links keep working, but AGENTS.md does not link them.

| Theme file | Status | Hook |
|---|---|---|
| [worktree-and-discard.md](worktree-and-discard.md) | candidate, 6 (0 measured) | Sessions and parallel workers share HEAD, index and locks; isolate each, guard self-spawning triggers, block discard commands with a hook. |
| [walls-not-reminders.md](walls-not-reminders.md) | rule, 6 (1 measured) | Urgency beats prose and a growing rules file stops nothing; enforce with branch protection, CI gates and hooks. A rejected push or an unread staged diff is a stop signal agents skip. |
| [credentials-and-irreversible.md](credentials-and-irreversible.md) | candidate, 10 (0 measured) | Scope credentials to the task and keep production keys out of reach; human confirmation and deletion protection for irreversible calls; backups out of reach and test-restored; local-only work copied off-repo before reset or rewrite; bulk cleanup lists targets and never forces a loop. |
| [gates-agent-cannot-edit.md](gates-agent-cannot-edit.md) | rule, 3 (1 measured) | Agents delete tests, edit CI or empty task lists to pass a gate; protect what the gate measures. |
| [monitor-health.md](monitor-health.md) | rule, 3 (2 measured) | Monitors go silent too: zero rows, missed runs and stale data must read as FAIL, with a health check and an alert path outside the watched code. |
| [notes-are-snapshots.md](notes-are-snapshots.md) | rule, 3 (1 measured) | Handoff and memory notes go stale silently; agents repeated finished work or acted on old facts. Store pointers, check live state. |
| [gate-from-real-sample.md](gate-from-real-sample.md) | rule, 3 (3 measured) | Gates and parsers written against an imagined input never fire; build them from a real sample and replay real history. |
| [spend-and-runaway-caps.md](spend-and-runaway-caps.md) | candidate, 3 (0 measured) | Unattended loops burned hundreds of dollars or millions of tokens overnight with no alert; cap spend before each call, stop repeated identical calls, dedupe triggers. |
| [destructive-guard.md](destructive-guard.md) | candidate, 3 (0 measured) | Refused agents retried the same delete in other shell dialects, through built-in file tools, inside their own scripts, or by switching the guard off; judge intent and cover every path. |
| [empty-done-fails.md](empty-done-fails.md) | rule, 3 (1 measured) | The worst failures were items ticked done with zero lines behind them, and a gate on changed files passed an empty diff; review every change, fail the empty done, cite an artifact. |
