#!/usr/bin/env bash
# Regenerate every preset from the tables in this folder and install them into OrcaSlicer, Bambu Studio,
# QIDI Studio and Snapmaker Orca.
#   scripts/build.sh               generate into ./out and install (all slicers must be closed)
#   scripts/build.sh --no-install  generate into ./out only
#   scripts/build.sh --force       install even over presets that were changed in a slicer since the last install
# Only presets listed in .installed/ (written by this script) are replaced or removed; presets you create
# yourself in the slicers are never touched. A preset changed in a slicer stops the install with a diff.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
[[ -f config/printers.json ]] || { cp config/printers.example.json config/printers.json; echo "Created config/printers.json from config/printers.example.json: put your printers' addresses in it and run again." >&2; exit 1; }
user_dir() {  # user_dir APP -> the preset folder the app loads: user/<account id> when logged in, else user/default
  local folder
  folder="$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["app"].get("preset_folder") or "default")' \
            "$HOME/.config/$1/$1.conf" 2>/dev/null || echo default)"
  echo "$HOME/.config/$1/user/$folder"
}
ORCA_USER="${ORCA_USER:-$(user_dir OrcaSlicer)}"
BAMBU_USER="${BAMBU_USER:-$(user_dir BambuStudio)}"
QIDI_USER="${QIDI_USER:-$(user_dir QIDIStudio)}"
SNAPMAKER_USER="${SNAPMAKER_USER:-$(user_dir Snapmaker_Orca)}"

install=1 force=()
for arg in "$@"; do
  case "$arg" in
    --no-install) install=0 ;;
    --force) force=(--force) ;;
    *) echo "unknown option: $arg" >&2; exit 64 ;;
  esac
done
APPS=(orca bambu qidi snapmaker)
if (( install )); then
  # Match on the binary path: Orca's process name is "orcaslicer_main", not "orca-slicer".
  # The AppImages run from /tmp/.mount_*; match their binaries by name.
  if pgrep -f '^/opt/orca-slicer/bin/' >/dev/null || pgrep -f '^/opt/bambustudio-bin/' >/dev/null \
     || pgrep -f '/bin/qidi-studio( |$)' >/dev/null || pgrep -f '/bin/snapmaker-orca( |$)' >/dev/null; then
    echo "Close OrcaSlicer, Bambu Studio, QIDI Studio and Snapmaker Orca first; they only read preset files at startup." >&2
    exit 1
  fi
  # Before out/ is removed: v0.1.0 install manifests have no checksums and compare with the last build.
  edited=0
  for app in "${APPS[@]}"; do python3 src/install.py check "$app" ${force[@]+"${force[@]}"} || edited=1; done
  (( ! edited )) || exit 1
fi

rm -rf out
python3 src/gen_process.py out/orca/process
python3 src/gen_filament.py out/orca/filament
python3 src/gen_machine.py out/orca/machine
python3 src/gen_bambu.py out/orca out/bambu bambu
python3 src/gen_bambu.py out/orca out/qidi qidi
python3 src/gen_snapmaker.py out/orca out/snapmaker
python3 src/lint.py out
if (( ! install )); then
  echo "Generated into ./out (not installed)."
  exit 0
fi
python3 src/install.py install orca out/orca "$ORCA_USER"
python3 src/install.py install bambu out/bambu "$BAMBU_USER"
python3 src/install.py install qidi out/qidi "$QIDI_USER"
python3 src/install.py install snapmaker out/snapmaker "$SNAPMAKER_USER"
echo "Restart the slicers to load the presets."
