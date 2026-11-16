#!/bin/sh
# Install local leak-guard hooks. Private terms are read from ~/.thriae-blocklist.
set -eu
root=$(git rev-parse --show-toplevel)
hooks="$root/.git/hooks"
bl="$HOME/.thriae-blocklist"
[ -f "$bl" ] || { echo "missing $bl (one private term per line)"; exit 1; }

cat > "$hooks/pre-commit" <<'HOOK'
#!/bin/sh
root=$(git rev-parse --show-toplevel)
exec python "$root/scripts/leak_check.py" --staged --blocklist "$HOME/.thriae-blocklist"
HOOK

cat > "$hooks/pre-push" <<'HOOK'
#!/bin/sh
root=$(git rev-parse --show-toplevel)
zero=0000000000000000000000000000000000000000
while read -r local_ref local_sha remote_ref remote_sha; do
  [ "$local_sha" = "$zero" ] && continue
  if [ "$remote_sha" = "$zero" ]; then range="$local_sha"; else range="$remote_sha..$local_sha"; fi
  python "$root/scripts/leak_check.py" --range "$range" --blocklist "$HOME/.thriae-blocklist" || exit 1
done
exit 0
HOOK
chmod +x "$hooks/pre-commit" "$hooks/pre-push"
echo "hooks installed"
