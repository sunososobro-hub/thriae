# One worktree per session; block discard commands

AGENTS.md line: section 0. Merged lessons: issues 41, 66, 70 (also supports issues 10, 33, 45).

## Rule
Each agent session works in its own git worktree and stays there. Discard commands (`reset --hard`, path `checkout --`, `restore`, `clean`, `stash drop`) on a shared checkout are blocked by a mechanism outside the model, not by prose.

## What happened
- issue 41: two sessions on one repo; the second backed out of a worktree and ran a hard reset in the main checkout. 12 files, a day or two of uncommitted work, gone; about 4 hours to rebuild by hand; the reflog could not recover it. Untracked files survived. The agent then misreported repo state without checking. Source: https://github.com/anthropics/claude-code/issues/33850
- issue 66: a written ban on checkout, reset, clean and delete did not hold. In a checkout shared by up to 4 sessions the agent ran `git checkout --` on a file it did not own, 4 times in one day, discarding others' uncommitted edits. Source: https://github.com/openai/codex/issues/6022
- issue 70: several sessions in one checkout share one HEAD and index. Over about a week: a branch switched under another session, a topic branch deleted while in use, staged deletions swept into another session's commit, the same feature built twice, exit checks failing on another session's unfinished work (waits up to 30 minutes). Source: https://dev.to/whynext/what-happened-when-i-let-several-ai-agents-loose-in-one-repo-3eoh

## Mechanisms
- A pre-tool hook (or wrapper or sandbox) rejects the discard commands above in a shared checkout.
- One worktree per session is the default: `git worktree add ../wt-<issue> -b fix/<issue> origin/<dev-branch>`; a discard then only hits the session's own files.
- Before every commit, compare the current branch with the branch recorded at session start; stop on a mismatch.
- The exit gate checks only files the session itself changed.
- Before starting, list open branches and open PRs so the same feature is not started twice.
- Before any destructive command, and after context compaction, check live state (`git status`, `git diff`) first.

## Edge cases
Untracked files survive `reset` but not `clean`. A second tool (another agent product) in the same checkout counts as another session. Related report, not counted: two parallel sessions pushing to one main branch, the second push replacing the first one's commits (4 files, about 30 minutes).
