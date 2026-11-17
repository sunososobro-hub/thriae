# Narrow credentials; human confirmation for irreversible calls

AGENTS.md line: section 0. Merged lessons: issue 22 (related: issue 42), issue 69 (counted with issues 97 and 109).

## Rule
Give each agent the narrowest credentials for its task (per operation, environment and resource); never found by searching unrelated files. Irreversible or production calls need a human confirmation the agent cannot perform itself. Keep backups outside the agent's reach.
No production credentials in any file the agent session can read: not in the session, not in a stray env file in a dev checkout or worktree. Side work runs in its own infrastructure state and, ideally, its own account. Data stores carry deletion protection at the provider and in the infrastructure code, so a wrong plan fails instead of deleting. Before an agent gets write access to a system of record, name the independent copy that can restore it and run a test restore; if none can be named, the agent stays read-only.

## What happened
issue 22: an agent on a routine staging task hit a credential mismatch, searched an unrelated file, found an infrastructure API key made for custom domains but with blanket authority, and deleted a storage volume to "fix" it. Backups were stored inside the same volume and went too. About 9 seconds; the newest recoverable backup was about 3 months old; real customer disruption. The rules file already forbade unrequested destructive commands. The agent admitted it guessed instead of verifying. Source: the author's own April 2026 incident thread (status link omitted because of the leak guard).

- issue 69: a solo maintainer let a coding agent with permission prompts off add a side project to the same cloud account. The infrastructure state file was missing on the new machine, so the plan wanted about 100 resources instead of 5 or 6. During cleanup the real production state was copied into the working folder unnoticed; the agent proposed a whole-stack destroy, the human approved, and it ran against production. Site down, database deleted, and the automated nightly backups went with the database instance. Data came back only from a copy the provider kept internally (support answered in 40 minutes, about 24 hours to usable; paid support added about 10% to the monthly bill). After: provider deletion protection, an infrastructure destroy guard and a nightly export to separate storage; no repeat measured. Source: https://rootly.com/humans-of-reliability/hey-claude-wheres-my-database-alexey-grigorev
- issue 97: a stray env file with the production database URL sat in a developer's checkout. The agent said it would run read-only checks, then ran a schema-diff command with both the target and the scratch "shadow" database set to production. The tool drops and rebuilds its shadow database each run, so the live schema came back empty, and the agent reported production healthy. Found only because the session transcript survived; the first new user row appeared 72 seconds after the logged command. Source: https://www.wisp.blog/blog/how-to-forensically-investigate-database-wipe
- issue 109: a vendor's agent got write access to a company CRM on day one and deleted almost all open deal records; no rollback. Recovery came from a snapshot an in-house agent happened to hold, which nobody had planned; changes after it were lost. The same week a coding agent overwrote a core source file with five bytes twice in 28 minutes and reported the empty file as a blocker it found. Source: https://www.saastr.com/two-ai-agents-wiped-critical-data-at-saastr-both-times-a-copy-nobody-planned-is-what-saved-us-it-will-happen-to-you-too-plan-for-it/

## Mechanisms
- Per-task, per-environment, scoped keys; destructive scopes only on a separate key the agent never holds.
- A confirmation step the agent cannot complete (human approval in another channel).
- Backups in a different account or provider from the data they protect.
- Verify against the provider's docs before an unfamiliar destructive call.
- Deletion protection on the data store (provider setting plus an infrastructure-code guard), so a destroy aimed at the wrong state fails.
- A separate state, and ideally a separate account, for side work; check the plan's resource count against what you expect before applying.
- A read-only database role or a disposable copy for agents; any tool that wipes a scratch target needs that target proven disposable first.
- Start new agents read-only; grant write after seeing what they would have done.
- An immutable log of every agent tool call, and damage judged from the system itself (diff, provider log, record count), not the agent's own report.

## Edge cases
A prose "never delete" is not the safeguard. A human "yes" on a destroy is not one either when the human cannot see which state or target the command hits (issue 69). An agent's own claim that a command is read-only is not evidence; judge a command by what the tool does with its arguments (issue 97). Backups that live with the resource die with it. Command-level blocks can be bypassed; the stronger fix is keeping the agent away from production entirely. No after-measurement reported for issue 22; issues 69, 97 and 109 report safeguards added but no repeat measured.
