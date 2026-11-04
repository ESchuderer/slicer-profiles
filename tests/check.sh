#!/usr/bin/env bash
# Regenerate every preset from config/printers.example.json and compare it with the golden files in tests/golden/.
#   tests/check.sh           compare; on a difference, show it and exit 1
#   tests/check.sh --update  replace tests/golden/ after an intended change, then review `git diff tests/golden`
# The stock profiles come from the trees src/fetch.py pinned (upstream.lock.toml), unless SLICER_PROFILES_* point
# elsewhere, so a difference is a change of this repository, not of an installed slicer.
set -euo pipefail
cd "$(dirname "$0")/.."
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
mkdir "$tmp/w"
# tracked and new files that exist (a tracked file deleted without `git rm` is skipped)
git ls-files -z --cached --others --exclude-standard \
  | python3 -c 'import os, sys; sys.stdout.write("".join(p + "\0" for p in sys.stdin.read().split("\0") if p and os.path.lexists(p)))' \
  | tar --null -T - -cf - | tar -xf - -C "$tmp/w"
# Use the pinned stock profiles (a no-op when cached); SLICER_PROFILES_* still win when set.
python3 src/fetch.py >/dev/null
rm -rf "$tmp/w/out" "$tmp/w/tests/golden"
cp config/printers.example.json "$tmp/w/config/printers.json"
(cd "$tmp/w" && scripts/build.sh --no-install >/dev/null)
if [[ "${1:-}" == "--update" ]]; then
  rm -rf tests/golden
  cp -R "$tmp/w/out" tests/golden
  echo "tests/golden updated ($(find tests/golden -type f | wc -l | tr -d ' ') files)"
elif diff -r "$tmp/w/out" tests/golden >"$tmp/diff"; then
  echo "OK: output matches tests/golden ($(find tests/golden -type f | wc -l | tr -d ' ') files)"
else
  head -40 "$tmp/diff"; echo "FAIL: output differs from tests/golden (< generated, > golden)" >&2; exit 1
fi
