#!/usr/bin/env bash
# Regenerate every preset and compare the SHA-256 sums with tests/expected.sha256.
#   tests/check.sh           compare (exit 1 on a difference)
#   tests/check.sh --update  rewrite tests/expected.sha256 after an intended change
set -euo pipefail
cd "$(dirname "$0")/.."
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
cp -r . "$tmp/w"
rm -rf "$tmp/w/out" "$tmp/w/.git" "$tmp/w/.installed"
sums=$(cd "$tmp/w" && scripts/build.sh --no-install >/dev/null && find out -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum)
if [[ "${1:-}" == "--update" ]]; then
  printf '%s\n' "$sums" > tests/expected.sha256
  echo "tests/expected.sha256 updated ($(wc -l < tests/expected.sha256) files)"
elif diff <(printf '%s\n' "$sums") tests/expected.sha256 >/dev/null; then
  echo "OK: output matches tests/expected.sha256"
else
  diff <(printf '%s\n' "$sums") tests/expected.sha256 | head -20; echo "FAIL: output differs from tests/expected.sha256" >&2; exit 1
fi
