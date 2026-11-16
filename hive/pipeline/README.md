# Thriae pipeline (optional)

Layout:
- `core/` rules (`rules.md`) and optional profiles (`release-lane.md`, `public-repo.md`). Vendored into a project at `.agent/core/`.
- `project.template.yml` copy to `.agent/project.yml` and fill in.
- `routines/` prompt templates for scheduled agents (worker, hard-worker, merger, reviewer, supervisor).
- `scripts/bootstrap.sh` creates labels, control issues and a minimal CI workflow (default dry run).
- Label `lesson`: `.github/workflows/lesson-label.yml` adds it to any issue whose title starts with "[lesson]" (create the label once; the sender never sets labels).
- `scripts/sync_core.sh` vendors a tagged core into a project as a PR (default dry run; needs THRIAE_CORE_REPO).

Start with `AGENTS.md` at the repo root; adopt this directory only when you want scheduled agents.
Schedules, caps and budget numbers in these files are example defaults from one deployment. Tune them in `project.yml`.

## Lesson reviewer (quarantine reviewer)
Flow: lesson issue on the target repo -> label `lesson` -> hourly run of `.github/workflows/review-lesson.yml` (private keeper repo) -> one reviewer comment + one `review:*` label per issue -> a human or the merger batches lessons labelled `quorum` into one AGENTS.md PR (re-implemented in own words, see `.github/CONTRIBUTING.md`). Nothing edits AGENTS.md automatically.
- Why scheduled: the Claude key must never live in the public repo. The reviewer runs from the PRIVATE keeper repo on a schedule (`17 * * * *`, hourly) and reads/writes issues on the target repo. It is not triggered by issue events; a lesson is reviewed within about an hour.
- Target: repo variable `THRIAE_TARGET_REPO` (default: the repo the workflow runs in, i.e. staging itself for now). Target == this repo uses `GITHUB_TOKEN` (issues: write). A different target uses secret `THRIAE_TARGET_TOKEN` (fine-grained PAT, Issues read/write on the target only); if missing nothing is posted and the run prints "target token not set".
- Each run: open issues with label `lesson` (or title starting `[lesson]`) that have no `review:*` label, no reviewer comment, or were updated more than 2 minutes after the reviewer's last comment (an edit, or any later comment). At most 5 per run, oldest first; none -> exit quietly. Manual run: Actions -> review-lesson -> Run workflow, optional issue number (reviews that issue even if already reviewed).
- Verdicts: `evidence:<N>` (supports an existing / seed rule, section N), `candidate:<slug>` (new general lesson; an existing slug is reused), `duplicate` (same project already reported it), `needs-evidence`, `rejected`. Labels (created if missing): `review:evidence`, `review:candidate`, `review:duplicate`, `review:needs-evidence`, `review:rejected`, plus `quorum`. Old `review:accepted` / `review:merge` labels on early issues are tolerated and never set again. Re-reviewing updates the same comment (it carries a "Reviewed <time>" line) and swaps the label. Only comments with the marker from a bot or an owner/member/collaborator count as the reviewer's own.
- Tally (CONSTITUTION Art. 3, CONTRIBUTING step 4): every lesson body carries `Project-ID: <12 hex>` (sha256 of the git remote URL or repo path; anonymous). The reviewer counts DISTINCT Project-IDs per `evidence:<rule>` / `candidate:<slug>` over all lesson issues, open and closed: two reports from one project are 1, votes do not count, an issue without Project-ID is its own unknown project (a lone one is downgraded to `needs-evidence`). Every comment shows `evidence: n/3 projects`. At 3/3 the post step labels those issues `quorum` and says "ready for an AGENTS.md PR"; nothing edits AGENTS.md by itself. Seed rules stay grandfathered until 3 projects confirm them or they are retired. Show it: `python -I hive/scripts/review_lesson.py --tally` (needs `GITHUB_REPOSITORY` and a token, or `--issues-file F`).
- The existing 17 lesson issues (numbers 1 to 17) all come from one project, so at most they give 1/3.
- Quarantine (three jobs): `select` has the target token but no model secret and writes `issues.json`; `review` has the model secret but no target token, a read-only repo token, and the model has no tools, it only returns JSON; `post` has `issues: write` but no model secret, re-validates the JSON (allowed verdicts, exactly two fields, reason <= 600 chars and <= 4 lines) and posts. Issue text is data, passed only by file. No checkout of issue code.
- Instructions live in `hive/prompts/review.md`. Local dry run (no API call, prints the payload): `python -I hive/scripts/review_lesson.py --issue N --dry-run`. Tests: `python -I hive/scripts/test_review_lesson.py` (includes the issue-selection logic).
- Model: `claude-sonnet-5-5`. With `ANTHROPIC_API_KEY` the script calls the API; with `CLAUDE_CODE_OAUTH_TOKEN` it runs the pinned Claude Code CLI with all tools disabled. Without either secret nothing is posted and the run prints the notice "reviewer secret not set".
- Owner one-time setup (now): run `claude setup-token`, then `gh secret set CLAUDE_CODE_OAUTH_TOKEN -R sunososobro-hub/thriae-staging` (paste the token when asked).
- After publishing the public repo: also set the repo variable `THRIAE_TARGET_REPO` (the public repo, `owner/name`) and the secret `THRIAE_TARGET_TOKEN` on the keeper repo (`gh variable set THRIAE_TARGET_REPO -R sunososobro-hub/thriae-staging`, `gh secret set THRIAE_TARGET_TOKEN -R sunososobro-hub/thriae-staging`).

## Publishing (keeper-only files)
There is no export script or exclude list yet; the public repo is exported by hand as an orphan commit. Leave these paths OUT of that export (they hold or depend on the private reviewer key, or are keeper operations):
- `.github/workflows/review-lesson.yml` (the scheduled reviewer; must never be in the public repo)
- `hive/prompts/review.md` (the reviewer's instructions; keep them private)
- `hive/scripts/review_lesson.py` and `hive/scripts/test_review_lesson.py` (only useful with the workflow)
- the "Lesson reviewer" and this "Publishing" section of this README, if the pipeline directory is published

Keep in the public repo: `AGENTS.md`, `.github/ISSUE_TEMPLATE/`, `.github/CONTRIBUTING.md`, `.github/workflows/lesson-label.yml`. Run `hive/scripts/leak_check.py --tree` on the export before pushing it.
