#!/usr/bin/env bash
# Regenerate every Bambu Lab H3C preset from config/ and install it into Bambu Studio.
#   scripts/build.sh               generate into ./out and install (Bambu Studio must be closed)
#   scripts/build.sh --no-install  generate into ./out only
#   scripts/build.sh --force       install even over presets that were changed in Bambu Studio since the last install
# Only presets listed in .installed/ (written by this script) are replaced or removed; presets you create
# yourself in the slicer are never touched. A preset changed in the slicer stops the install with a diff.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
user_dir() {  # user_dir APP -> the preset folder the app loads: user/<account id> when logged in, else user/default
  local folder
  folder="$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["app"].get("preset_folder") or "default")' \
            "$HOME/.config/$1/$1.conf" 2>/dev/null || echo default)"
  echo "$HOME/.config/$1/user/$folder"
}
BAMBU_USER="${BAMBU_USER:-$(user_dir BambuStudio)}"

install=1 force=()
for arg in "$@"; do
  case "$arg" in
    --no-install) install=0 ;;
    --force) force=(--force) ;;
    *) echo "unknown option: $arg" >&2; exit 64 ;;
  esac
done
if (( install )); then
  if pgrep -f '^/opt/bambustudio-bin/' >/dev/null; then
    echo "Close Bambu Studio first; it only reads preset files at startup." >&2
    exit 1
  fi
  # Before out/ is removed: v0.1.0 install manifests have no checksums and compare with the last build.
  python3 src/install.py check bambu ${force[@]+"${force[@]}"}
fi

rm -rf out
python3 src/generate.py out
python3 src/lint.py out
if (( ! install )); then
  echo "Generated into ./out (not installed)."
  exit 0
fi
python3 src/install.py install bambu out/bambu "$BAMBU_USER"
echo "Restart Bambu Studio to load the presets."
