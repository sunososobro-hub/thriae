#!/usr/bin/env bash
# sync_core.sh - vendor the Thriae pipeline core/ at a tag into a project repo as a PR.
#
# Usage: THRIAE_CORE_REPO=<owner>/<repo> hive/pipeline/scripts/sync_core.sh --tag core-vX.Y.Z --project owner/name --base DEV [--issue N] [--project-yml FILE] [--dry-run|--apply]
# --project-yml FILE: first sync only (the project has no .agent/project.yml on --base yet). FILE is a local
#   project.yml; it is added to the same sync PR (core_version is set to the tag). Not needed afterwards.
# --base BRANCH is required: the project's dev branch. Never main / the default branch.
# --apply needs --issue N (the project issue to track the sync): head is feat/N, body says Refs #N
# Default is --dry-run. Products read only their vendored copy (.agent/core/), never the pipeline's tip.
# Needs: git, gh. The core repo is read via a fresh clone at the tag (read-only).
# In project repos .agent/core/** and .agent/project.yml are protected paths: the PR needs a strong review PASS.
set -euo pipefail

MODE=dry; TAG=""; PRODUCT=""; ISSUE=""; BASE=""; PYML=""; CORE_REPO="${THRIAE_CORE_REPO:-}"
while [ $# -gt 0 ]; do
  case "$1" in
    --tag) TAG="${2:-}"; shift 2 ;;
    --project) PRODUCT="${2:-}"; shift 2 ;;
    --base) BASE="${2:-}"; shift 2 ;;
    --project-yml) PYML="${2:-}"; shift 2 ;;
    --issue) ISSUE="${2:-}"; shift 2 ;;
    --apply) MODE=apply; shift ;;
    --dry-run) MODE=dry; shift ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[[ "$TAG" =~ ^core-v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "--tag must look like core-vX.Y.Z" >&2; exit 2; }
[ -n "$CORE_REPO" ] || { echo "set THRIAE_CORE_REPO=<owner>/<repo> (the repo holding hive/pipeline/core)" >&2; exit 2; }
[ -n "$PRODUCT" ] || { echo "need --project owner/name" >&2; exit 2; }
[ -n "$BASE" ] || { echo "need --base <dev branch> (never main)" >&2; exit 2; }
if [ -n "$PYML" ]; then
  [ -f "$PYML" ] || { echo "--project-yml: file not found: $PYML" >&2; exit 2; }
  PYML=$(cd "$(dirname "$PYML")" && pwd)/$(basename "$PYML")
fi
# private repos over https: run `gh auth setup-git` first

WORK=$(mktemp -d); trap 'rm -rf "$WORK"' EXIT
git clone -q --depth 1 --branch "$TAG" "https://github.com/$CORE_REPO.git" "$WORK/core-src"
[ -d "$WORK/core-src/hive/pipeline/core" ] || { echo "no core/ at $TAG" >&2; exit 1; }
git clone -q --depth 1 "https://github.com/$PRODUCT.git" "$WORK/project"
cd "$WORK/project"

DEFAULT=$(git rev-parse --abbrev-ref origin/HEAD | sed 's|^origin/||')
git fetch -q --depth 1 origin "+refs/heads/$BASE:refs/remotes/origin/$BASE" || { echo "base branch $BASE not found" >&2; exit 1; }
HAVE_YML=0; git cat-file -e "origin/$BASE:.agent/project.yml" 2>/dev/null && HAVE_YML=1
if [ "$HAVE_YML" = 0 ] && [ -z "$PYML" ]; then
  echo "error: $PRODUCT has no .agent/project.yml on $BASE (first sync). Write one from hive/pipeline/project.template.yml in the core repo and pass --project-yml <file>; it is added to the sync PR." >&2
  exit 2
fi
if [ "$HAVE_YML" = 1 ] && [ -n "$PYML" ]; then
  echo "error: $PRODUCT already has .agent/project.yml on $BASE; --project-yml is for the first sync only. Edit project.yml in its own PR." >&2
  exit 2
fi
yml() { { if [ -n "$PYML" ]; then cat "$PYML"; else git show "origin/$BASE:.agent/project.yml"; fi; } 2>/dev/null | awk -v k="$1:" 'index($0,k)==1 {sub(/^[^:]*:[ ]*/,""); sub(/[ ]*#.*/,""); gsub(/["'"'"' ]/,""); print; exit}' || true; }
MAIN=$(yml main_branch || true); DEVCFG=$(yml dev_branch || true)
if [ "$BASE" = "$DEFAULT" ] || [ "$BASE" = "${MAIN:-main}" ] || [ "$BASE" = main ] || [ "$BASE" = master ]; then
  echo "refusing: base $BASE is the project's default/main branch" >&2; exit 2
fi
if [ -n "$DEVCFG" ] && [ "$DEVCFG" != "$BASE" ]; then
  echo "refusing: --base $BASE differs from dev_branch $DEVCFG in project.yml" >&2; exit 2
fi
DEV="$BASE"
git checkout -q -B "sync-core" "origin/$DEV"

[ -z "$PYML" ] || { mkdir -p .agent; cp "$PYML" .agent/project.yml; }
OLD=$(awk 'index($0,"core_version:")==1 {sub(/^[^:]*:[ ]*/,""); sub(/[ ]*#.*/,""); gsub(/["'"'"' ]/,""); print; exit}' .agent/project.yml 2>/dev/null || true)
echo "project=$PRODUCT dev=$DEV core_version: ${OLD:-none} -> $TAG"

rm -rf .agent/core; mkdir -p .agent/core
cp -R "$WORK/core-src/hive/pipeline/core/." .agent/core/
if [ -f .agent/project.yml ]; then
  if grep -q '^core_version:' .agent/project.yml; then
    sed -i.bak "s/^core_version:.*/core_version: $TAG/" .agent/project.yml && rm -f .agent/project.yml.bak
  else
    echo "core_version: $TAG" >> .agent/project.yml
  fi
else
  echo "error: no .agent/project.yml after checkout" >&2; exit 1
fi

CHANGED_ROUTINES=""
if [ -n "$OLD" ] && git -C "$WORK/core-src" fetch -q --depth 1 origin "tag" "$OLD" 2>/dev/null; then
  CHANGED_ROUTINES=$(git -C "$WORK/core-src" diff --name-only "$OLD" "$TAG" -- hive/pipeline/routines 2>/dev/null || true)
fi

git add -A .agent
git status --short
if git diff --cached --quiet; then echo "already at $TAG, nothing to do"; exit 0; fi

if [ "$MODE" != apply ]; then
  echo "[dry-run] would push branch feat/${ISSUE:-N} and open a PR to $DEV. Re-run with --apply."
  git diff --cached --stat
  exit 0
fi

git config user.name  "${GIT_AUTHOR_NAME:?set GIT_AUTHOR_NAME}"
git config user.email "${GIT_AUTHOR_EMAIL:?set GIT_AUTHOR_EMAIL}"
[[ "$ISSUE" =~ ^[0-9]+$ ]] || { echo "--apply needs --issue N" >&2; exit 2; }
BR="feat/$ISSUE"
git checkout -q -b "$BR"
git commit -q -m "chore: vendor the pipeline $TAG into .agent/core"
git push -q origin "$BR"
PREFIX=$(awk 'index($0,"usage_line_prefix:")==1 {sub(/^[^:]*:[ ]*/,""); sub(/[ ]*#.*/,""); gsub(/["` ]/,""); print; exit}' .agent/project.yml 2>/dev/null | tr -d "'" || true)
BODY="Refs #$ISSUE

${PYML:+First sync: adds \`.agent/project.yml\`.
}Vendors the pipeline \`$TAG\` (was \`${OLD:-none}\`) into \`.agent/core/\` and bumps \`core_version\`.
Protected paths (.agent/core/**, .agent/project.yml): needs \`Strong review: PASS\`.
Routine templates changed since $OLD (re-paste into cloud routines): ${CHANGED_ROUTINES:-none or unknown}
Rollback: revert this PR (not during an open release snapshot).

${PREFIX:-usage}: sync minutes=0"
gh pr create -R "$PRODUCT" --base "$DEV" --head "$BR" --title "chore: vendor the pipeline $TAG" --body "$BODY"
