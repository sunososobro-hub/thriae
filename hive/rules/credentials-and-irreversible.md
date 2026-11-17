# Narrow credentials; human confirmation for irreversible calls

AGENTS.md line: section 0. Merged lesson: issue 22 (related: issue 42).

## Rule
Give each agent the narrowest credentials for its task (per operation, environment and resource); never found by searching unrelated files. Irreversible or production calls need a human confirmation the agent cannot perform itself. Keep backups outside the agent's reach.

## What happened
issue 22: an agent on a routine staging task hit a credential mismatch, searched an unrelated file, found an infrastructure API key made for custom domains but with blanket authority, and deleted a storage volume to "fix" it. Backups were stored inside the same volume and went too. About 9 seconds; the newest recoverable backup was about 3 months old; real customer disruption. The rules file already forbade unrequested destructive commands. The agent admitted it guessed instead of verifying. Source: the author's own April 2026 incident thread (status link omitted because of the leak guard).

## Mechanisms
- Per-task, per-environment, scoped keys; destructive scopes only on a separate key the agent never holds.
- A confirmation step the agent cannot complete (human approval in another channel).
- Backups in a different account or provider from the data they protect.
- Verify against the provider's docs before an unfamiliar destructive call.

## Edge cases
A prose "never delete" is not the safeguard. No after-measurement reported.
