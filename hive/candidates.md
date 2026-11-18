# Lesson candidates (agent behaviour)

Index only. Each candidate lives in its own `[lesson]` issue, which carries the claim, the evidence, the Project-ID and the reviewer's tally (`evidence: n/3 projects`). To add evidence from another project, open a lesson issue that says `Supports #N`. Nothing here is a rule yet; a rule needs 3 independent projects, at least 1 of them measured (`.github/CONTRIBUTING.md` step 4b).

| Candidate | Issue |
|---|---|
| manual-check-stays-blocked | [issue 49](https://github.com/sunososobro-hub/thriae/issues/49) |
| no-always-true-assertions | [issue 50](https://github.com/sunososobro-hub/thriae/issues/50) |
| validate-against-server-truth | [issue 51](https://github.com/sunososobro-hub/thriae/issues/51) |
| cross-field-invariants | [issue 52](https://github.com/sunososobro-hub/thriae/issues/52) |
| tests-run-on-every-pr | [issue 53](https://github.com/sunososobro-hub/thriae/issues/53) |
| backup-before-reset | [issue 54](https://github.com/sunososobro-hub/thriae/issues/54) |
| cleanup-dry-run-first | [issue 55](https://github.com/sunososobro-hub/thriae/issues/55) |
| quota-caps | [issue 56](https://github.com/sunososobro-hub/thriae/issues/56) |

## Demoted rules (measured-vote gate, 2026-11-18)
These were rules; they had 3 or more projects but no measured vote, so their AGENTS.md lines were removed. Each detail file stays in `hive/rules/` with `Status: candidate`, all evidence kept. A `Supports` lesson with a replay, rerun, audit or before/after numbers re-promotes it.

| Candidate | Projects | Why held | Lead for a measured vote |
|---|---|---|---|
| [worktree-and-discard](rules/worktree-and-discard.md) | 6 (0 measured) | single incidents only | none found yet |
| [destructive-guard](rules/destructive-guard.md) | 3 (0 measured) | issue 92 has no run counts | denylist study: 69.0% to 98.6% of 1,709 real denylists leave a bypass (https://arxiv.org/html/2606.15549) |
| [credentials-and-irreversible](rules/credentials-and-irreversible.md) | 10 (0 measured) | no before/after of a safeguard | none found yet |
| [spend-and-runaway-caps](rules/spend-and-runaway-caps.md) | 3 (0 measured) | issue 65 is a counterfactual estimate | none found yet |

## Not ported
- Changing a method's error contract means checking all callers: duplicate of [issue 3](https://github.com/sunososobro-hub/thriae/issues/3), so it adds nothing new.
