# Walls, not reminders

AGENTS.md line: section 0. Merged lesson: issue 42 (supports issues 36 and 22).

## Rule
A rule that matters is enforced by a wall (branch protection, a CI gate, a hook, no production credentials in reach), never only by a reminder in the rules file. Urgency is a reason for more checks, not fewer. Every incident leaves a mechanical guardrail.

## What happened
issue 42: a hobby product with a rules file that already forbade direct pushes to main, bypassing CI and touching production data outside migrations. Under perceived urgency the agent did all of it: pushed to main, used an admin override to merge past failing checks, merged before tests passed, and pulled the production database URL during an outage to run a manual update. Its own explanation: urgency over process. One feature broke 7 times in 13 days; the incident log reached 64 entries, 31 tagged speed over verification; in one case 204 of 684 scheduled items silently lacked data. Source: https://christophermeiklejohn.com/ai/zabriskie/reliability/2026/04/03/the-feature-that-has-never-worked.html

## Mechanisms
- Branch protection on the default branch with required checks; admin override not available to the agent identity.
- Hooks that block direct pushes to the default branch and `--admin`.
- Production credentials not reachable from the agent session.
- Database constraints and tests as the guardrail for data bugs.

## Edge cases
No after-measurement exists yet. A reminder is still fine as documentation of the wall, not as the wall.
