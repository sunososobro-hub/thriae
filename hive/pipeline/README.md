# Thriae pipeline (optional)

Layout:
- `core/` rules (`rules.md`) and optional profiles (`release-lane.md`, `public-repo.md`). Vendored into a project at `.agent/core/`.
- `project.template.yml` copy to `.agent/project.yml` and fill in.
- `routines/` prompt templates for scheduled agents (worker, hard-worker, merger, reviewer, supervisor).
- `scripts/bootstrap.sh` creates labels, control issues and a minimal CI workflow (default dry run).
- `scripts/sync_core.sh` vendors a tagged core into a project as a PR (default dry run; needs THRIAE_CORE_REPO).

Start with `AGENTS.md` at the repo root; adopt this directory only when you want scheduled agents.
Schedules, caps and budget numbers in these files are example defaults from one deployment. Tune them in `project.yml`.
