#!/usr/bin/env bash
# bootstrap.sh - prepare a product repo for the Thriae pipeline.
# Idempotently creates labels, the throttle and ledger issues, and a minimal ci.yml.
#
# Usage: pipeline/scripts/bootstrap.sh --project path/to/.agent/project.yml [--dry-run|--apply]
# Default is --dry-run: prints what would be done, changes nothing.
# Needs: gh (authenticated), awk, sed. Reads simple project.yml (scalars, one nesting level, block lists).
set -euo pipefail

MODE=dry
PROJECT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --project) PROJECT="${2:-}"; shift 2 ;;
    --apply) MODE=apply; shift ;;
    --dry-run) MODE=dry; shift ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[ -n "$PROJECT" ] && [ -f "$PROJECT" ] || { echo "need --project <project.yml>" >&2; exit 2; }

strip() { sed -e 's/[[:space:]]#.*$//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'\$/\1/"; }

# yget key            -> top-level scalar
# yget parent.child   -> one-level nested scalar
yget() {
  local key="$1"
  if [[ "$key" == *.* ]]; then
    awk -v p="${key%%.*}" -v c="${key#*.}" '
      $0 ~ "^"p":" {in_p=1; next}
      in_p && /^[^ #]/ {in_p=0}
      in_p { line=$0; sub(/^[ ]+/,"",line); if (index(line,c":")==1) { sub(/^[^:]*:[ ]*/,"",line); print line; exit } }
    ' "$PROJECT" | strip
  else
    awk -v k="$key" 'index($0,k":")==1 { sub(/^[^:]*:[ ]*/,""); print; exit }' "$PROJECT" | strip
  fi
}

# ylist key -> block list items or inline [a, b]
ylist() {
  local key="$1" inline
  inline=$(yget "$key")
  if [[ "$inline" == \[* ]]; then
    echo "$inline" | sed -e 's/^\[//' -e 's/\]$//' | tr ',' '\n' | strip | sed '/^$/d'
  else
    awk -v k="$key" '
      index($0,k":")==1 {f=1; next}
      f && /^[ ]*-[ ]/ { sub(/^[ ]*-[ ]*/,""); print; next }
      f && /^[ ]*#/ {next}
      f {exit}
    ' "$PROJECT" | strip | sed '/^$/d'
  fi
}

REPO=$(yget repo)
DEV=$(yget dev_branch)
TEST_CMD=$(yget verify.test)
TEST_JOB=$(yget ci.test_job)
WORKFLOW=$(yget ci.workflow)
RUNNER=$(yget ci.runner)
SETUP=$(yget ci.setup)
[ -n "$REPO" ] && [ "$REPO" != "owner/name" ] || { echo "project.yml: set repo" >&2; exit 2; }
[ -n "$TEST_CMD" ] || { echo "project.yml: set verify.test" >&2; exit 2; }
: "${DEV:=dev}"; : "${TEST_JOB:=test}"; : "${WORKFLOW:=ci.yml}"; : "${RUNNER:=ubuntu-latest}"

run() { # run a gh command, or print it in dry mode
  if [ "$MODE" = apply ]; then "$@"; else printf '[dry-run] '; printf '%q ' "$@"; echo; fi
}

echo "== bootstrap $REPO mode=$MODE =="

# ---- labels ----
declare -a LABELS=()
add() { LABELS+=("$1|$2|$3"); }   # name|color|description
for s in todo doing review blocked frozen proposal; do add "status:$s" "ededed" "pipeline status"; done
for p in P0 P1 P2 P3; do add "$p" "d93f0b" "priority"; done
for m in light strong; do add "model:$m" "5319e7" "worker model"; done
for t in bug enhancement eval documentation maint; do add "$t" "0e8a16" "issue type"; done
for l in ok-to-work infra needs-strong needs-owner lesson lesson-accepted; do add "$l" "fbca04" "pipeline"; done
while IFS= read -r a; do [ -n "$a" ] && add "area:$a" "1d76db" "area lock unit"; done < <(ylist areas)
while IFS= read -r m; do [ -n "$m" ] && add "mode:$m" "c5def5" "mode"; done < <(ylist mode_labels)

EXISTING=""
if [ "$MODE" = apply ]; then EXISTING=$(gh label list -R "$REPO" --limit 500 --json name --jq '.[].name'); fi
for entry in "${LABELS[@]}"; do
  IFS='|' read -r name color desc <<<"$entry"
  if [ "$MODE" = apply ] && grep -Fxq "$name" <<<"$EXISTING"; then echo "label exists: $name"; continue; fi
  run gh label create "$name" -R "$REPO" --color "$color" --description "$desc"
done

# ---- throttle and ledger issues ----
find_or_create() { # title body
  local title="$1" body="$2" n=""
  if [ "$MODE" = apply ]; then
    n=$(gh issue list -R "$REPO" --state open --search "\"$title\" in:title" --json number,title --jq ".[] | select(.title==\"$title\") | .number" | head -1)
    if [ -z "$n" ]; then
      n=$(gh issue create -R "$REPO" --title "$title" --body "$body" | sed 's|.*/||')
    fi
    LAST_N="$n"; echo "$title -> #$n   (put in project.yml)"
  else
    echo "[dry-run] ensure issue \"$title\" exists (body: ${body%%$'\n'*})"
  fi
}
find_or_create "[pipeline] throttle (faucet)" $'level: 2\nfocus:\n\nLevels: 0 off, 1 low, 2 normal, 3 high, 4 max. See .agent/core/rules.md section 5.'
find_or_create "[health] pipeline check log" $'Ledger and health comments are posted here by S-hard. Pin this issue.'

# ---- minimal ci.yml (proposed as a PR, never pushed to dev) ----
CI_PATH=".github/workflows/$WORKFLOW"
CI_BODY="name: ci
on:
  push:
    branches: [$DEV]
  pull_request:
    branches: [$DEV]
jobs:
  $TEST_JOB:
    runs-on: $RUNNER
    steps:
      - uses: actions/checkout@v4
${SETUP:+      - run: $SETUP
}      - run: $TEST_CMD
"
if [ "$MODE" = apply ]; then
  if gh api "repos/$REPO/contents/$CI_PATH?ref=$DEV" >/dev/null 2>&1; then
    echo "ci workflow exists on $DEV: $CI_PATH (not touched)"
  else
    BR="feat/${LAST_N:?ledger issue number unknown}"   # head must be feat/N (rules s2)
    sha=$(gh api "repos/$REPO/git/ref/heads/$DEV" --jq .object.sha)
    gh api -X POST "repos/$REPO/git/refs" -f ref="refs/heads/$BR" -f sha="$sha" >/dev/null
    b64=$(printf '%s
' "$CI_BODY" | base64 | tr -d '
')
    gh api -X PUT "repos/$REPO/contents/$CI_PATH" -f message="chore: add minimal ci (bootstrap)" -f content="$b64" -f branch="$BR" >/dev/null
    gh pr create -R "$REPO" --base "$DEV" --head "$BR" --title "chore: add minimal ci (bootstrap)" --body "Refs #$LAST_N

Adds the \`$TEST_JOB\` job that gates merges to $DEV. Review before merging."
  fi
else
  echo "[dry-run] would open a PR (head feat/<ledger issue>) adding $CI_PATH to $DEV if missing:"
  echo "$CI_BODY" | sed 's/^/    /'
fi
echo "== done =="
