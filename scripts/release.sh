#!/usr/bin/env bash
# Build the release files of the current commit into dist/: the preset zips (no printer addresses), NOTICE.md,
# manifest.json with its schema, and SHA256SUMS. Two runs on one commit give identical files.
#   scripts/release.sh v0.2.0                              build only
#   scripts/release.sh v0.2.0 --publish NOTES.md           also create the GitHub release from a clean main
# Builds from the stock tree pinned in upstream.lock.toml, fetched by src/fetch.py (network on the first run).
set -euo pipefail
version=${1:?usage: scripts/release.sh vX.Y.Z [--publish NOTES.md]}
[[ "$version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "version must look like v1.2.3" >&2; exit 64; }
cd "$(dirname "$0")/.."
commit=$(git rev-parse HEAD)
epoch=$(git log -1 --format=%ct)
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
mkdir "$tmp/w"
git archive "$commit" | tar -x -C "$tmp/w"
# Everything below runs from the archive of the commit, never from the working tree, and from the stock tree
# pinned in its upstream.lock.toml, which is what manifest.json records: no override, no installed slicer.
unset SLICER_PROFILES_BAMBU
python3 "$tmp/w/src/fetch.py" >/dev/null
(cd "$tmp/w" && scripts/build.sh --no-install >/dev/null)
python3 "$tmp/w/src/lint.py" "$tmp/w/out"
rm -rf dist
python3 "$tmp/w/src/release.py" "$version" "$commit" "$epoch" "$tmp/w/out" dist
ls -l dist
if [[ "${2:-}" == "--publish" ]]; then
  notes=${3:?--publish needs the release notes file}
  [[ "$(git branch --show-current)" == main && -z "$(git status --porcelain)" ]] || { echo "Publish from a clean main." >&2; exit 1; }
  git fetch --quiet origin main
  [[ "$(git rev-parse origin/main)" == "$commit" ]] || { echo "The release must be built from the tip of origin/main." >&2; exit 1; }
  gh release create "$version" dist/* --target "$commit" --title "$version" --notes-file "$notes"
fi
