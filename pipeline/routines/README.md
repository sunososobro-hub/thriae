# Routine prompt templates

Cloud routines (scheduled agents) are configured in your agent platform, not in git. These templates are the source text; adapt wording to your platform.

## Parameterization
Each template starts with a fixed preamble that points at the vendored core, so the pasted prompt stays short and stable:

    Repo: <owner/name>. First read .agent/project.yml and .agent/core/rules.md
    (plus .agent/core/release-lane.md if release_lane: snapshot, .agent/core/public-repo.md if public: true)
    from origin/<dev_branch>. They override anything below. Then do the role steps.

Only `{{REPO}}` and `{{DEV_BRANCH}}` are substituted when pasting; everything else is read at run time from project.yml, so changing the project config needs no routine edit.

## Pasting
1. Copy the template for the role, replace `{{REPO}}`, `{{DEV_BRANCH}}`.
2. Create one routine per slot (worker A/B/C = same template, different cron offset) in the cloud UI, using the template's schedule line.
3. Record which `core-vX.Y.Z` the pasted text came from in the routine's description.

## Source of truth
At each project's migration the core templates become the source of truth and replace the live cloud prompts. The old live prompts are not compared or merged.

## When a template changes
A new `core-v` tag that edits `pipeline/routines/*.md` does NOT update running routines. The sync PR (pipeline/scripts/sync_core.sh) lists changed templates in its body; the owner (or R-hard with owner approval) re-pastes them into the cloud routines and updates the description. A routine whose recorded version lags the project's `core_version` by a minor or more is a defect.

## Templates
| File | Role | Model | Schedule |
|---|---|---|---|
| worker.md | slots A/B/C (light style) | light | hourly :13 / :33 / :53 |
| w-hard.md | hard worker | strong | hourly :48 |
| merger.md | R-merge / S-merge | light | every 30 min |
| r-hard.md | Strong review queue, bump, conflicts | strong | 2 shifts/day |
| s-hard.md | sweep, ledger, supply, health, lessons | strong | hourly |
