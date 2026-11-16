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
Flow: lesson issue -> label `lesson` -> `.github/workflows/review-lesson.yml` -> one reviewer comment + one `review:*` label -> a human or the merger batches `review:accepted` / `review:merge` lessons into one AGENTS.md PR (re-implemented in own words, see `.github/CONTRIBUTING.md`). Nothing edits AGENTS.md automatically.
- Trigger: issue opened or edited with a `[lesson]` title or the `lesson` label, or run it by hand: Actions -> review-lesson -> Run workflow -> issue number (for existing issues).
- Verdicts: `accepted` (new, general, has evidence; the "candidate" of CONTRIBUTING), `merge-into:<N>` (strengthens rule section N, label `review:merge`), `duplicate`, `needs-evidence`, `rejected`. Labels are created if missing: `review:accepted`, `review:merge`, `review:duplicate`, `review:needs-evidence`, `review:rejected`. Re-reviewing an edited issue updates the same comment and swaps the label.
- Quarantine: issue text is data, passed only by env/file. Job `review` has the model secret but a read-only token and the model has no tools; it only returns JSON. Job `post` has `issues: write` but no model secret; it re-validates the JSON (allowed verdicts, exactly two fields, reason <= 600 chars and <= 4 lines) and posts. No checkout of issue code.
- Instructions live in `hive/prompts/review.md`. Local dry run (no API call, prints the payload): `python -I hive/scripts/review_lesson.py --issue N --dry-run`. Tests: `python -I hive/scripts/test_review_lesson.py`.
- Model: `claude-sonnet-5-5`. With `ANTHROPIC_API_KEY` the script calls the API; with `CLAUDE_CODE_OAUTH_TOKEN` it runs the pinned Claude Code CLI with all tools disabled. Without either secret the job posts nothing and prints the notice "reviewer secret not set".
- The ONE owner action to enable it: run `claude setup-token`, then `gh secret set CLAUDE_CODE_OAUTH_TOKEN -R sunososobro-hub/thriae-staging` (paste the token when asked).
