# 🐝 Thriae

One AGENTS.md, distilled from real agent failures.

<p align="center"><img src="hive/assets/pain-cure.svg" alt="Four pains and their cures: same mistake again becomes one file for any tool; a rules file that keeps growing becomes every rule has evidence; agents that collide become dead rules removed; private data leaks become a built-in leak guard" width="900"></p>

<p align="center"><img src="hive/assets/who.svg" alt="Who is it for: anyone who codes with AI agents (Claude Code, Codex, Cursor), solo developer or team" width="900"></p>

<p align="center"><img src="hive/assets/quickstart.svg" alt="Quickstart: 1 copy AGENTS.md, 2 fill your project block, 3 done. Claude Code also needs CLAUDE.md. When: a new project, or an agent repeats a mistake. Works with Claude Code, Codex and Cursor" width="900"></p>

<p align="center"><img src="hive/assets/how-it-grows.svg" alt="How a rule grows: failure, lesson plus evidence, 3 projects confirm, rule, and when it stops helping it is removed. You are here: seed rules from 1 pipeline" width="900"></p>

<p align="center"><img src="hive/assets/hive-architecture.svg" alt="Architecture: the compass constitution guards the flow; the keeper is scout number one and holds the brake. Bees from your projects bring lessons into quarantine; when 3 projects confirm, the rule goes into the AGENTS.md honey jar, reaches everyone, and lessons come back with credit" width="900"></p>

<p align="center"><a href="hive/CONTRIBUTORS.md"><img src="hive/assets/bees.svg" alt="Contributor roles: scout, forager, honey-maker, guard, cleaner, nurse, builder, AI" width="900"></a></p>

<p align="center"><a href="hive/CONTRIBUTORS.md">Every kind of help gets credit</a></p>

<p align="center"><img src="hive/assets/three-loops.svg" alt="Three loops inside the constitution: hourly do at the center, weekly rules around it, monthly mechanism outside; outer loops are slower and stricter" width="900"></p>

<p align="center">In Greek myth the Thriae were three bee-nymphs who spoke the truth after eating honey.</p>

<p align="center"><img src="hive/assets/hive-map.svg" alt="Repo layout as a honeycomb: the door row holds README, AGENTS.md (the honey), LICENSE, .github and CLAUDE.md; below it the hive holds the compass constitution, red leak-guard cells, purple contributors and green pipeline cells" width="600"></p>

<p align="center">
  <a href="../../issues/new?template=lesson.yml">🐝 Contribute a lesson</a> ·
  <a href="hive/CONSTITUTION.md">🧭 Constitution</a> ·
  <a href="LICENSE">📄 License MIT</a>
</p>

<details><summary>Read as text</summary>

One `AGENTS.md` for any team using Claude Code, Codex or Cursor, plus an optional pipeline, a constitution and a leak guard.
These are seed rules from one production pipeline. A rule becomes shared wisdom once evidence from 3 or more independent projects arrives.

## The bees
- In Greek myth the Thriae were three bee-nymph prophetesses who spoke the truth after eating honey.
- Here the three are three loops: craft (hourly PRs), rules (weekly: keep, tighten or drop), mechanism (monthly: review the pipeline itself).
- The honey is distilled wisdom: `AGENTS.md`, short, and only what evidence keeps.
- Thomas Seeley's *Honeybee Democracy*: scouts check sites independently and bring back evidence; a choice is made when a quorum agrees.
- So a rule lands on evidence from independent projects, never on votes, and the queen does not vote: the keeper is scout #1, signs amendments and holds the emergency brake.

## Quickstart
1. Copy `AGENTS.md` into the root of your repo and fill in its "Fill in for your project" block.
2. For Claude Code, also copy `CLAUDE.md` (one line, `@AGENTS.md`, so Claude Code loads it). Codex, Cursor and similar tools read `AGENTS.md` directly.
3. Optional: `hive/pipeline/` for scheduled agents (see its README), and `hive/scripts/leak_check.py` as a leak guard.

## Leak guard limits
`hive/scripts/leak_check.py` blocks blocklisted terms, emails, home paths, tokens and session links in commits, PRs and files. It cannot catch:
- private terms missing from your blocklist, or a paraphrase, translation or description that identifies someone without naming them;
- text in images, binaries or archives (refused, not read), or encodings other than base64;
- issues, comments, wiki and releases, unless you run `--text` on them;
- fork and Dependabot PRs beyond the generic checks (they get no secrets, so no blocklist);
- anything already pushed: it reports, it cannot un-publish.

## Contribute a lesson
Open an issue with the Lesson form: what happened, the rule that changed, measured before and after, a link to the evidence. Redact private names first. The full flow is in [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md); the rules about rules are in [`hive/CONSTITUTION.md`](hive/CONSTITUTION.md).

## License
MIT. See [`LICENSE`](LICENSE).

</details>
