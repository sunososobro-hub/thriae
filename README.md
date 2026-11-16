# Thriae

<p align="center"><img src="hive/assets/hive-map.svg" alt="Thriae as a honeycomb: the door row holds README, AGENTS.md (the honey), LICENSE and .github; below it the hive holds the compass constitution, red leak-guard cells, purple contributors and green pipeline cells" width="600"></p>

One `AGENTS.md` for any team using Claude Code, Codex or Cursor, plus an optional pipeline, a constitution and a leak guard.
These are seed rules from one production pipeline. A rule becomes shared wisdom once evidence from 3 or more independent projects arrives.

## The bees
- In Greek myth the Thriae were three bee-nymph prophetesses who spoke the truth after eating honey.
- Here the three are three loops: craft (hourly PRs), rules (weekly: keep, tighten or drop), mechanism (monthly: review the pipeline itself).
- The honey is distilled wisdom: `AGENTS.md`, short, and only what evidence keeps.
- Thomas Seeley's *Honeybee Democracy*: scouts check sites independently and bring back evidence; a choice is made when a quorum agrees.
- So a rule lands on evidence from independent projects, never on votes, and the queen does not vote: the keeper only signs and holds the emergency brake.

## Quickstart
1. Copy `AGENTS.md` into the root of your repo and fill in its "Fill in for your project" block.
2. For Claude Code, also copy `CLAUDE.md` (one line, `@AGENTS.md`, so Claude Code loads it). Codex, Cursor and similar tools read `AGENTS.md` directly.
3. Optional: `hive/pipeline/` for scheduled agents (see its README), and `hive/scripts/leak_check.py` as a leak guard.

## Contribute a lesson
Open an issue with the Lesson form: what happened, the rule that changed, measured before and after, a link to the evidence. Redact private names first. The full flow is in [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md); the rules about rules are in [`hive/CONSTITUTION.md`](hive/CONSTITUTION.md).

## License
MIT. See [`LICENSE`](LICENSE).
