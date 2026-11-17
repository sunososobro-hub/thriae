#!/usr/bin/env bash
# sync_agents.sh - refresh the shared part of a project's AGENTS.md (and the files it points at)
# from a Thriae checkout, keeping the project block untouched. Run from the project repo root.
#
# Usage: hive/pipeline/scripts/sync_agents.sh --core DIR [--source LABEL]
#   --core DIR      a checkout of the Thriae repo (any ref: a core-v tag, or the default branch)
#   --source LABEL  written into the start marker, e.g. owner/repo@<sha> (default: DIR's HEAD sha)
#
# The project's AGENTS.md must already have the markers (first install: hive/prompts/download.md):
#   <!-- thriae:start ... -->   shared part, replaced on every sync
#   <!-- thriae:end -->         everything after this line is the project block, never changed
# Also refreshed: hive/pipeline/roles/*.md (AGENTS.md points at them), and, only when the project
# has .agent/project.yml, the vendored pipeline core in .agent/core/ (core_version is not changed;
# that stays with sync_core.sh). Writes files only; committing and opening the PR is the caller's job.
# Exit 0 = files written (check `git status`), 2 = usage error or missing markers.
set -euo pipefail

CORE=""; SOURCE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --core) CORE="${2:-}"; shift 2 ;;
    --source) SOURCE="${2:-}"; shift 2 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[ -n "$CORE" ] && [ -f "$CORE/AGENTS.md" ] || { echo "need --core <Thriae checkout with AGENTS.md>" >&2; exit 2; }
[ -f AGENTS.md ] || { echo "no AGENTS.md here; first install with hive/prompts/download.md" >&2; exit 2; }
grep -q '^<!-- thriae:start' AGENTS.md && grep -q '^<!-- thriae:end -->' AGENTS.md || {
  echo "AGENTS.md has no <!-- thriae:start --> / <!-- thriae:end --> markers; add them around the shared part once" >&2; exit 2; }
[ -n "$SOURCE" ] || SOURCE="thriae@$(git -C "$CORE" rev-parse HEAD 2>/dev/null || echo unknown)"

TMP=$(mktemp)
{
  echo "<!-- thriae:start source=$SOURCE - synced by hive/pipeline/scripts/sync_agents.sh, do not edit here; change it in Thriae -->"
  sed -e 's/\r$//' "$CORE/AGENTS.md"
  echo
  # project block: from the end marker to the end of the file, byte for byte
  awk 'f || /^<!-- thriae:end -->/ {f=1; print}' AGENTS.md
} > "$TMP"
mv "$TMP" AGENTS.md

if [ -d "$CORE/hive/pipeline/roles" ]; then
  rm -rf hive/pipeline/roles; mkdir -p hive/pipeline/roles
  cp "$CORE"/hive/pipeline/roles/*.md hive/pipeline/roles/
fi
if [ -f .agent/project.yml ] && [ -d "$CORE/hive/pipeline/core" ]; then
  rm -rf .agent/core; mkdir -p .agent/core
  cp -R "$CORE/hive/pipeline/core/." .agent/core/
fi
echo "synced shared part from $SOURCE"
