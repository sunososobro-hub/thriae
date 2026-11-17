# One worktree per session; isolate every parallel path; block discard commands

AGENTS.md line: section 0. Merged lessons: issues 41, 66, 70, 33 (with 45 and 82; also supports issue 10).

## Rule
Each agent session and each parallel worker works in its own git worktree and branch and stays there. Any path that skips isolation must show that two workers cannot hit it at once, or it is serialised. Runtime state (locks, cursors, scratch tables) is never tracked in git. Whoever hands a lock or status file to a child restores its own state as soon as that child ends. Each self-spawning or paid-probe trigger has its own recursion guard. Discard commands (`reset --hard`, path `checkout --`, `restore`, `clean`, `stash drop`) on a shared checkout are blocked by a mechanism outside the model, not by prose.

## What happened
- issue 41: two sessions on one repo; the second backed out of a worktree and ran a hard reset in the main checkout. 12 files, a day or two of uncommitted work, gone; about 4 hours to rebuild by hand; the reflog could not recover it. Untracked files survived. The agent then misreported repo state without checking. Source: https://github.com/anthropics/claude-code/issues/33850
- issue 66: a written ban on checkout, reset, clean and delete did not hold. In a checkout shared by up to 4 sessions the agent ran `git checkout --` on a file it did not own, 4 times in one day, discarding others' uncommitted edits. Source: https://github.com/openai/codex/issues/6022
- issue 70: several sessions in one checkout share one HEAD and index. Over about a week: a branch switched under another session, a topic branch deleted while in use, staged deletions swept into another session's commit, the same feature built twice, exit checks failing on another session's unfinished work (waits up to 30 minutes). Source: https://dev.to/whynext/what-happened-when-i-let-several-ai-agents-loose-in-one-repo-3eoh
- issue 33: adding parallel workers to a private pipeline gave a run of races, one per review round (four rounds). A shortcut for single-item branches skipped the per-worker checkout, so several workers wrote one index and committed at once; a minimal test (one shortcut plus one normal) passed, and only asking what happens if it fires twice found it. A lock file tracked in git made every parallel merge conflict. A child deleted the parent's lock on exit, so status showed stopped and mutual exclusion lapsed until the batch ended. A new self-spawning paid planning probe was not covered by the old anti-recursion flag, so child workers re-triggered it, even when no split was possible. First-hand, no public link.
- issue 45: an IDE agent started several write-capable sub-agents at once in one tree that already held uncommitted work; their edits overwrote each other, and the destructive git "recovery" also erased never-committed files. It rebuilt the work itself at high token cost and never asked to commit or branch first. Vendor staff advice: require approval, commit before big runs, block destructive git with a hook, one worktree per parallel task. Source: https://forum.cursor.com/t/agent-parallel-subagents-overwrite-dirty-worktree-destructive-git-recovery-wastes-tokens/166666
- issue 82: two parallel sessions each ran fetch, rebase onto remote main, push to remote main. The second rebased on a view older than the first one's push, and its push replaced the first one's commits. No error; 4 files and about 30 minutes of work were missed hours later. After: one branch per session, sequential merge, a divergence check before push; recovery took under 5 minutes. Whether a force flag was used is not shown. Source: https://dev.to/snake_sun/concurrent-autoiter-sessions-force-pushed-each-other-heres-the-recovery-pattern-3k10

## Mechanisms
- A pre-tool hook (or wrapper or sandbox) rejects the discard commands above in a shared checkout.
- One worktree per session is the default: `git worktree add ../wt-<issue> -b fix/<issue> origin/<dev-branch>`; a discard then only hits the session's own files.
- Before every commit, compare the current branch with the branch recorded at session start; stop on a mismatch.
- The exit gate checks only files the session itself changed.
- Before starting, list open branches and open PRs so the same feature is not started twice.
- Before any destructive command, and after context compaction, check live state (`git status`, `git diff`) first.
- Before fanning out sub-agents, commit or stash the tree; each parallel writer gets its own worktree or a disjoint file set.
- Parallel sessions never push to one shared branch: one branch each, merged one at a time; before a push, stop if the remote moved since the fetch; branch protection rejects force pushes to shared branches.
- Treat parallelism as a review item: for every path that skips isolation, ask what happens if it fires twice.
- Keep runtime state (locks, cursors, scratch tables) out of version control.
- When a child process gets a lock or status file, trace the child's own start and cleanup code and restore the parent's state the moment the child ends, not after the batch.
- Each new self-spawning or paid trigger: its own recursion guard checked at every child entry point, a free pre-filter before any paid call, a back-off after repeated nothing-to-do answers, and a budget check even on the guarded path.
- Test with a worker that outlives the child, and confirm the test fails on the old code.

## Edge cases
Untracked files survive `reset` but not `clean`. A second tool (another agent product) in the same checkout counts as another session. The report of two sessions pushing to one main branch, earlier noted here as not counted, is issue 82 and now counts under issue 33.
