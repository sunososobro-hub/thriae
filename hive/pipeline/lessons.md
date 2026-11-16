# Pipeline lessons (candidates)

Evidence log for the factory core rules. Each entry is a candidate: evidence from 1 project so far (1/3). It becomes shared wisdom at 3 independent projects (CONSTITUTION Art. 3). Most of these are already written into `core/` as rules; this file records why. Entries marked "risk" have no recorded incident: the rule is the lesson and the risk is what it guards against.

| Candidate | Rule (core section) | Evidence | Status |
|---|---|---|---|
| area-lock-doing-only | Area locks count only `status:doing` issues, never open PRs (rules 9) | Locking on open PRs froze 5 areas and left 4 of 22 items claimable | candidate 1/3 |
| escalate-by-path | Escalate to the strong model by protected path, not by diff size (rules 3) | Of 200 PRs, 73 went to strong review and only 5 (7%) got CHANGES; median wait 41 min | candidate 1/3 |
| paperwork-not-fail | A merger fixes PR-body paperwork itself instead of failing the PR (rules 3) | Risk: failing paperwork stalls the queue | candidate 1/3 |
| picker-never-idles | If the preferred type has no eligible item, fall through to the next type (rules 8) | Risk: a "pick that type, else stop" picker idles workers while eligible work exists | candidate 1/3 |
| identity-check-in-ci | A CI check on commit author and committer identity rejects placeholder identities before they enter history (rules 1) | Risk: placeholder identities in shared history are hard to remove later | candidate 1/3 |
| two-lanes | A fast development branch gated by the test job only, with every release gate on a snapshot branch of the release, keeps speed without lowering quality (release-lane) | Reported as working in one deployment; no measured before/after | candidate 1/3 |
| defer-stuck-runner-check | A check on a self-hosted runner that never started within a wait window may be deferred with a loud release note and a P0 issue on later failure; a started run is never deferred (release-lane) | Risk: a missing runner blocks every release | candidate 1/3 |
