# Lesson candidates (agent behaviour)

Candidates for AGENTS.md, in the quarantine form of `.github/CONTRIBUTING.md`. All are candidate, evidence from 1 project so far (1/3). Nothing here is a rule yet; a rule needs 3 independent projects. "Rule only" means no incident is recorded: the risk is what the rule guards against.

## manual-check-stays-blocked
- Claim: a manual or on-device check in the Acceptance cannot be skipped because the device is unreachable.
- Evidence type: failure (one incident). A 6-digit colour code parsed into a 32-bit colour value without alpha rendered fully transparent and threw no error; static analysis did not catch it.
- Measured before / after: no.
- Rule: leave the item blocked with "waiting for manual check" instead of marking it done.
- Overlaps: AGENTS.md section 12 (verify your work), partly.
- Possible harm: items wait longer for a person.
- Projects: 1/3. Verdict: candidate.

## no-always-true-assertions
- Claim: an assertion that is always true makes a commit look tested without testing anything.
- Evidence type: rule only. Risk: green tests that prove nothing.
- Rule: when something is hard to test directly, extract the logic into a pure function and test that.
- Overlaps: none found.
- Possible harm: small refactors.
- Projects: 1/3. Verdict: candidate.

## validate-against-server-truth
- Claim: checking only the format of a client-supplied value does not make it true.
- Evidence type: rule only. Risk: a client sends a well-formed but false value (for example a date-shaped identifier) and passes the format check.
- Rule: compare every security-relevant part with a value the server knows (for example server time).
- Overlaps: none found.
- Possible harm: extra server lookups.
- Projects: 1/3. Verdict: candidate.

## cross-field-invariants
- Claim: for an invariant "X implies Y", every control that can change Y must be checked, not only the one that fires when X changes.
- Evidence type: rule only. Risk: the invariant breaks through the control nobody listed.
- Rule: list all writers of Y before shipping the invariant.
- Overlaps: lesson issue about changing a shared contract (related, different case).
- Possible harm: none known.
- Projects: 1/3. Verdict: candidate.

## tests-run-on-every-pr
- Claim: tests that only run by hand mean PRs merge untested.
- Evidence type: failure (seen in 1 project). The suite existed but ran only by hand, so PRs merged untested.
- Measured before / after: no.
- Rule: every PR runs the test suite automatically (`pull_request` trigger); a manual-only suite does not count as a gate.
- Overlaps: AGENTS.md section 12 (verify your work), partly.
- Possible harm: slower PRs; CI minutes.
- Projects: 1/3. Verdict: candidate.

## backup-before-reset
- Claim: syncing or resetting a local working copy can destroy work that exists nowhere else.
- Evidence type: failure (seen in 1 project). Local-only work is lost when a copy is reset to match the remote.
- Measured before / after: no.
- Rule: before a sync or reset, push every local-only commit, branch, stash and uncommitted change to a remote backup branch and verify it is reachable on the remote. Delete nothing.
- Overlaps: lesson issue on hard resets in a shared checkout (related, different case).
- Possible harm: extra backup branches to prune later (by a person).
- Projects: 1/3. Verdict: candidate.

## cleanup-dry-run-first
- Claim: an automatic cleanup that deletes the wrong thing is hard to undo.
- Evidence type: failure (seen in 1 project). An automatic cleanup can remove backup or in-review branches.
- Measured before / after: no.
- Rule: any automatic cleanup (branches, files) does a dry-run first and never touches backup/rescue branches or branches with an open PR.
- Overlaps: none found.
- Possible harm: stale branches stay longer.
- Projects: 1/3. Verdict: candidate.

## Not ported
- Changing a method's error contract (swallow-and-return-nothing to rethrow) means checking all callers: duplicate of the existing candidate "changing a shared contract means checking every caller", so it adds nothing new.

## quota-caps
- Claim: a factory that merges and releases on its own spends paid quota (CI minutes, build minutes, store review slots) faster than anyone notices.
- Evidence type: rule only. Risk: a loop that triggers a paid build on every merge used up a month's free build minutes in days.
- Rule: every automatic release has a cap per platform and period and runs only when something new merged since the last one; above a set share of the monthly CI quota, merges are batched and the keeper is told.
- Overlaps: role ops.md section 8 (throughput caps), partly.
- Possible harm: fixes reach testers a day or a week later.
- Projects: 1/3. Verdict: candidate.
