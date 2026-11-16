# Thriae

Not one person's experience — wisdom distilled by every team that uses it. Copy AGENTS.md, then bring back what you learn.

## Quickstart
Copy one file, `AGENTS.md`, into the root of your repo. Fill in the "Fill in for your project" block (dev branch, test command, protected paths). Claude Code, Codex, Cursor and similar tools read it automatically.

## Optional: the full pipeline
`pipeline/` is the automation built on the same rules: vendored core rules, optional release-lane and public-repo profiles, routine prompt templates for scheduled agents (workers, mergers, reviewers), a `project.yml` template, `pipeline/scripts/bootstrap.sh` (labels, control issues, minimal CI) and `pipeline/scripts/sync_core.sh` (vendor a tagged core into your repo as a PR). Both scripts default to a dry run.

## The three loops
1. Craft (hourly): agents pick one issue, make one small PR, and merge when the test job is green.
2. Rules (weekly): the measured outcomes of loop 1 decide which working rules to keep, tighten or drop.
3. Mechanism (monthly): the pipeline itself is reviewed, and only changes that raise outcomes survive.
Outer loops are slower and have higher thresholds; `CONSTITUTION.md` sits above all three.

## Contributing
Lessons come back through issues, with evidence from at least 3 independent projects before a rule lands. See `CONTRIBUTING.md`.
