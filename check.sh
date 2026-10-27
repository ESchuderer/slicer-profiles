#!/usr/bin/env bash
# Regenerate every preset with the example printer addresses and compare the SHA-256 sums with expected.sha256.
#   ./check.sh           compare (exit 1 on a difference)
#   ./check.sh --update  rewrite expected.sha256 after an intended change
set -euo pipefail
cd "$(dirname "$0")"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
cp -r . "$tmp/w"
rm -rf "$tmp/w/out" "$tmp/w/.git" "$tmp"/w/installed-*.txt
cp printers.example.json "$tmp/w/printers.json"
sums=$(cd "$tmp/w" && ./build.sh --no-install >/dev/null && find out -type f -print0 | sort -z | xargs -0 sha256sum)
if [[ "${1:-}" == "--update" ]]; then
  printf '%s\n' "$sums" > expected.sha256
  echo "expected.sha256 updated ($(wc -l < expected.sha256) files)"
elif diff <(printf '%s\n' "$sums") expected.sha256 >/dev/null; then
  echo "OK: output matches expected.sha256"
else
  diff <(printf '%s\n' "$sums") expected.sha256 | head -20; echo "FAIL: output differs from expected.sha256" >&2; exit 1
fi
