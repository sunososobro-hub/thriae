# 🐝 Thriae

One AGENTS.md, distilled from real agent failures.

<p align="center"><img src="hive/assets/pain-cure.svg" alt="Four pains and their cures: same mistake again becomes one file for any tool; a rules file that keeps growing becomes every rule has evidence; agents that collide become dead rules removed; private data leaks become a built-in leak guard" width="900"></p>

<p align="center"><img src="hive/assets/get-the-honey.svg" alt="Get the honey: your AI agent (Claude Code, Codex or Cursor) plus the AGENTS.md honey jar, copied into your project with your project block filled in (Claude Code also needs CLAUDE.md), and the agent stops repeating mistakes. When: a new project, or the same mistake again" width="900"></p>

<p align="center"><a href="hive/prompts/download.md">⬇️ Get the honey: paste the download prompt</a> · already have rules? <a href="hive/prompts/upload.md">⬆️ share them first</a></p>

<p align="center"><img src="hive/assets/factory.svg" alt="Door 2, the factory: issue, worker, review, merge, release, and lessons flow back into AGENTS.md. Candidate, evidence from 1 project so far (1/3)" width="900"></p>

<p align="center"><b>Door 2: 🏭 the factory (optional).</b> Scheduled agents take issues to releases. Candidate, 1/3: evidence from 1 project so far. <a href="hive/pipeline/README.md">Open the factory</a></p>

<p align="center"><img src="hive/assets/how-it-grows.svg" alt="How a rule grows: failure, lesson plus evidence, 3 projects confirm, rule, and when it stops helping it is removed. Now: 1 of 3 projects; seed rules wait for 2 more projects" width="900"></p>

<p align="center"><img src="hive/assets/hive-architecture.svg" alt="Architecture: the compass constitution guards the flow; the keeper is scout number one and holds the brake. Bees from your projects bring lessons into quarantine; when 3 projects confirm, the rule goes into the AGENTS.md honey jar, reaches everyone, and lessons come back with credit" width="900"></p>

<p align="center"><a href="hive/CONTRIBUTORS.md"><img src="hive/assets/bees.svg" alt="Contributor roles: scout, forager, honey-maker, guard, cleaner, nurse, builder, AI" width="900"></a></p>

<p align="center"><a href="hive/CONTRIBUTORS.md">Every kind of help gets credit</a></p>

<p align="center"><img src="hive/assets/three-loops.svg" alt="Three loops inside the constitution: hourly do at the center, weekly rules around it, monthly mechanism outside; outer loops are slower and stricter" width="900"></p>

<p align="center">In Greek myth the Thriae were three bee-nymphs who spoke the truth after eating honey.</p>

<p align="center"><img src="hive/assets/hive-map.svg" alt="Repo layout as a honeycomb: the door row holds README, AGENTS.md (the honey), LICENSE, .github and CLAUDE.md; below it the hive holds the compass constitution, red leak-guard cells, purple contributors and green pipeline cells" width="600"></p>

<p align="center"><img src="hive/assets/up-down.svg" alt="Two prompts. Upload, share your lessons: paste, sort your rules into universal, project-only and dead, you say yes, sent. Download, get the honey: backup, new AGENTS.md, your project block kept, you say yes. Nothing is sent or overwritten without your yes" width="900"></p>

<p align="center"><a href="hive/prompts/upload.md">⬆️ Copy the upload prompt</a> · <a href="hive/prompts/download.md">⬇️ Copy the download prompt</a></p>

<p align="center"><a href=".github/CONTRIBUTING.md"><img src="hive/assets/contribute-flow.svg" alt="How to contribute: 1 file a lesson, 2 quarantine check, 3 rewritten, never pasted, 4 three projects confirm, 5 one in, one out under a 250-line cap, 6 credit. A good lesson: a real failure with numbers, a one or two line rule, no names, paths or secrets" width="900"></a></p>

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
3. Or let your agent do steps 1 and 2: paste [`hive/prompts/download.md`](hive/prompts/download.md). It backs up your file, keeps your own rules in the project block and writes only after your yes; run it again later to upgrade. Already have rules worth sharing? Paste [`hive/prompts/upload.md`](hive/prompts/upload.md) first.
4. Optional: `hive/pipeline/` for scheduled agents (see its README), and `hive/scripts/leak_check.py` as a leak guard.

## Leak guard limits
`hive/scripts/leak_check.py` blocks blocklisted terms, emails, home paths, tokens and session links in commits, PRs and files. It cannot catch:
- private terms missing from your blocklist, or a paraphrase, translation or description that identifies someone without naming them;
- text in images, binaries or archives (refused, not read), or encodings other than base64;
- issues, comments, wiki and releases, unless you run `--text` on them;
- fork and Dependabot PRs beyond the generic checks (they get no secrets, so no blocklist);
- anything already pushed: it reports, it cannot un-publish.

## Contribute a lesson
Easiest: paste [`hive/prompts/upload.md`](hive/prompts/upload.md) into your AI agent and say yes to the drafts it shows you. Or open an issue with the Lesson form yourself: what happened, the rule that changed, measured before and after, a link to the evidence. Redact private names first. The full flow is in [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md); the rules about rules are in [`hive/CONSTITUTION.md`](hive/CONSTITUTION.md).

## License
MIT. See [`LICENSE`](LICENSE).

</details>
