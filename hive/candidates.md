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

## Not ported
- Changing a method's error contract (swallow-and-return-nothing to rethrow) means checking all callers: duplicate of the existing candidate "changing a shared contract means checking every caller", so it adds nothing new.
