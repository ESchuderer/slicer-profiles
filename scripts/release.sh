#!/usr/bin/env bash
# Build the release files of the current commit into dist/: one preset zip per slicer (no printer
# addresses), manifest.json with its schema, and SHA256SUMS. Two runs on one commit give identical files.
#   scripts/release.sh v0.2.0                              build only
#   scripts/release.sh v0.2.0 --publish NOTES.md           also create the GitHub release from a clean main
# Needs the stock profiles like scripts/build.sh does (installed slicers or SLICER_PROFILES_*).
set -euo pipefail
version=${1:?usage: scripts/release.sh vX.Y.Z [--publish NOTES.md]}
[[ "$version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "version must look like v1.2.3" >&2; exit 64; }
cd "$(dirname "$0")/.."
commit=$(git rev-parse HEAD)
epoch=$(git log -1 --format=%ct)
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
mkdir "$tmp/w"
git archive "$commit" | tar -x -C "$tmp/w"
cp config/printers.example.json "$tmp/w/config/printers.json"
(cd "$tmp/w" && scripts/build.sh --no-install >/dev/null)
python3 src/lint.py "$tmp/w/out" --release
rm -rf dist
python3 src/release.py "$version" "$commit" "$epoch" "$tmp/w/out" dist
ls -l dist
if [[ "${2:-}" == "--publish" ]]; then
  notes=${3:?--publish needs the release notes file}
  [[ "$(git branch --show-current)" == main && -z "$(git status --porcelain)" ]] || { echo "Publish from a clean main." >&2; exit 1; }
  [[ "$(git rev-parse origin/main)" == "$commit" ]] || { echo "Push main first: the release must match origin/main." >&2; exit 1; }
  gh release create "$version" dist/* --target "$commit" --title "$version" --notes-file "$notes"
fi
