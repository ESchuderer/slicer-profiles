#!/usr/bin/env bash
# Build the downloadable preset zips (one per slicer, example printer addresses) into dist/.
#   scripts/release.sh v0.1.0             build only
#   scripts/release.sh v0.1.0 --publish   also create the GitHub release from main and attach the zips
# Needs the four slicers installed like scripts/build.sh does (the generators read their stock profiles).
set -euo pipefail
version=${1:?usage: scripts/release.sh vX.Y.Z [--publish]}
cd "$(dirname "$0")/.."
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
cp -r . "$tmp/w"
rm -rf "$tmp/w/out" "$tmp/w/dist" "$tmp/w/.git" "$tmp/w/.installed" "$tmp/w/config/printers.json"
cp config/printers.example.json "$tmp/w/config/printers.json"
(cd "$tmp/w" && scripts/build.sh --no-install >/dev/null)
rm -rf dist && mkdir dist
for s in orca bambu qidi snapmaker; do
  python3 - "$tmp/w/out/$s" "dist/slicer-profiles-$s-$version.zip" <<'PY'
import os, sys, zipfile
src, dst = sys.argv[1:]
with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, _, files in sorted(os.walk(src)):
        for f in sorted(files):
            z.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), src))
PY
done
ls -l dist
if [[ "${2:-}" == "--publish" ]]; then
  [[ "$(git branch --show-current)" == main && -z "$(git status --porcelain)" ]] || { echo "Publish from a clean main." >&2; exit 1; }
  gh release create "$version" dist/*.zip --target main --title "$version" \
    --notes "Presets for the slicer versions in the README table. Install: docs/install.md. The (LAN) printer presets carry the example address 192.0.2.x: set your printer's address after importing."
fi
