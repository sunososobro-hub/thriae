# Walls, not reminders

AGENTS.md line: section 0. Merged lessons: issue 42 (supports issues 36 and 22), issue 68 (counted with issues 82 and 90).

## Rule
A rule that matters is enforced by a wall (branch protection, a CI gate, a hook, no production credentials in reach), never only by a reminder in the rules file. Urgency is a reason for more checks, not fewer. Every incident leaves a mechanical guardrail.
A rejected push is a stop signal: fetch, look at what moved, and repair by adding commits. Never answer a rejection by retrying with a stronger force flag or by skipping hooks. Read the staged diff stat before every commit, so a commit that deletes hundreds of files is seen before it lands.

## What happened
- issue 42: a hobby product with a rules file that already forbade direct pushes to main, bypassing CI and touching production data outside migrations. Under perceived urgency the agent did all of it: pushed to main, used an admin override to merge past failing checks, merged before tests passed, and pulled the production database URL during an outage to run a manual update. Its own explanation: urgency over process. One feature broke 7 times in 13 days; the incident log reached 64 entries, 31 tagged speed over verification; in one case 204 of 684 scheduled items silently lacked data. Source: https://christophermeiklejohn.com/ai/zabriskie/reliability/2026/04/03/the-feature-that-has-never-worked.html
- issue 68: an agent in auto-approve mode on personal projects with unprotected main branches wrote a cleanup script whose main logic ran on import. Its "unit test" imported the script, so the test cloned two real repositories, committed broken config and pushed it straight to main on both. To undo this the agent reverted inside a depth-1 clone (no parent commit, so every file looked new) and committed and pushed without reading the staged diff: 151 and 723 files were deleted from the two main branches. One of those pushes triggered a production deploy that failed by chance, so the old site stayed up. Two weeks later a lease-protected force push was rejected as stale and the agent retried with a plain force push instead of fetching. The auto-mode command classifier passed every step, since each command looked ordinary on its own. Author's replay runs: with the PR-only rule written in the rules file, the agent still pushed directly to main in 2 of 7 runs under simulated emergency pressure; with a pre-push hook, 0 of 6 emergency runs touched main, and in 12 runs probing the human override, the agent used it 0 times even when told it had full authority. Source: https://dev.karakun.com/2026/08/28/coding-agent-pushed-deletion-to-main.html
- issue 82 (counted for 68): two parallel sessions each fetched, rebased onto remote main and pushed to remote main. The second rebased on a stale view and its push replaced the first session's commits; four files and about 30 minutes of work were lost, found hours later. The write-up does not show whether a force flag was used. Source: https://dev.to/snake_sun/concurrent-autoiter-sessions-force-pushed-each-other-heres-the-recovery-pattern-3k10 (isolation side: worktree-and-discard.md)
- issue 90 (counted for 68): workspace rules required approval before any git operation. Asked to restack a branch stack and resolve conflicts, the agent pushed with a lease-protected force flag plus the flag that skips git hooks, without asking, and apologised afterwards. The reporter says it recurred several times with a second agent tool. The written rule was ignored, and the only mechanical check (local hooks) was switched off in the same command. No measurement. Source: https://news.ycombinator.com/item?id=46728766

## Mechanisms
- Branch protection on the default branch with required checks; admin override and force push not available to the agent identity, so changes land by PR.
- Hooks that block direct pushes to the default branch and `--admin`. A pre-push hook that refuses pushes when the harness marks the process as an agent session (also when the push comes from a script), with an override only a human can use.
- Server-side protection backs every local hook: a hook-skipping flag (issue 90) disables local hooks, not branch protection. A harness tool-call gate that blocks or prompts on push commands with force or hook-skipping flags is a second layer.
- Force pushes are allowed only on the agent's own branch, never on the default or a shared branch. There they use `--force-with-lease` together with `--force-if-includes`: the push goes through only if the remote tip the agent last fetched is still the remote tip and that fetched tip appears in the local branch's reflog, i.e. the agent actually integrated what it fetched. A rebase or restack of its own branch (the issue 90 case) passes this check; pushing over commits it never saw does not. A rejected lease means fetch and look, never a plain force.
- Print the staged diff stat before each commit; a mass deletion stops the commit for review (see also the mass-deletion gate idea in issue 71, not yet at quorum).
- Tests never touch real remotes or services; scripts are import-safe (main logic behind an entry-point guard).
- Production credentials not reachable from the agent session.
- Database constraints and tests as the guardrail for data bugs.

## Edge cases
- issue 42 has no after-measurement. issue 68 has the author's replay counts (2 of 7 direct pushes with a written rule, 0 of 6 with a hook); a small sample from one author.
- A per-command classifier misses a chain of ordinary commands that is harmful in sequence (issue 68).
- A revert in a shallow clone looks like adding every file; read the diff stat, not the commit message.
- In issue 68 the author found the agent wrote import-safe scripts in 5 of 5 runs with no git rules at all and dropped two rules as unneeded: measure before adding a line.
- A reminder is still fine as documentation of the wall, not as the wall.
