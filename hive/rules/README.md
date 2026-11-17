# Rule details (lazy loading)

`AGENTS.md` stays slim: one short line per theme, plus a full URL to the detail file here. Open a detail file when its topic comes up. Nothing learned is dropped: each file keeps every merged lesson (issue numbers, what happened, source links, concrete mechanisms, edge cases). The 250-line cap counts `AGENTS.md` only, not these files. Background: idea issue 40 (rulebook as folder blocks).

Full URLs are used in `AGENTS.md` because relative paths broke in role files (issue 38).

| Theme file | Hook |
|---|---|
| [worktree-and-discard.md](worktree-and-discard.md) | Sessions share HEAD and index; give each its own worktree and block discard commands with a hook. |
| [walls-not-reminders.md](walls-not-reminders.md) | Urgency beats prose; enforce with branch protection, CI gates and hooks. |
| [credentials-and-irreversible.md](credentials-and-irreversible.md) | Scope credentials to the task; human confirmation for irreversible calls; backups out of reach. |
