# Rule details (lazy loading)

`AGENTS.md` stays slim: one short line per theme, plus a full URL to the detail file here. Open a detail file when its topic comes up. Nothing learned is dropped: each file keeps every merged lesson (issue numbers, what happened, source links, concrete mechanisms, edge cases). The 250-line cap counts `AGENTS.md` only, not these files. Background: idea issue 40 (rulebook as folder blocks).

Full URLs are used in `AGENTS.md` because relative paths broke in role files (issue 38).

| Theme file | Hook |
|---|---|
| [worktree-and-discard.md](worktree-and-discard.md) | Sessions and parallel workers share HEAD, index and locks; isolate each, guard self-spawning triggers, block discard commands with a hook. |
| [walls-not-reminders.md](walls-not-reminders.md) | Urgency beats prose and a growing rules file stops nothing; enforce with branch protection, CI gates and hooks. A rejected push or an unread staged diff is a stop signal agents skip. |
| [credentials-and-irreversible.md](credentials-and-irreversible.md) | Scope credentials to the task and keep production keys out of reach; human confirmation and deletion protection for irreversible calls; backups out of reach and test-restored; local-only work copied off-repo before reset or rewrite; bulk cleanup lists targets and never forces a loop. |
| [gates-agent-cannot-edit.md](gates-agent-cannot-edit.md) | Agents delete tests, edit CI or empty task lists to pass a gate; protect what the gate measures. |
| [monitor-health.md](monitor-health.md) | Monitors go silent too: zero rows, missed runs and stale data must read as FAIL, with a health check and an alert path outside the watched code. |
| [notes-are-snapshots.md](notes-are-snapshots.md) | Handoff and memory notes go stale silently; agents repeated finished work or acted on old facts. Store pointers, check live state. |
| [gate-from-real-sample.md](gate-from-real-sample.md) | Gates and parsers written against an imagined input never fire; build them from a real sample and replay real history. |
| [spend-and-runaway-caps.md](spend-and-runaway-caps.md) | Unattended loops burned hundreds of dollars or millions of tokens overnight with no alert; cap spend before each call, stop repeated identical calls, dedupe triggers. |
