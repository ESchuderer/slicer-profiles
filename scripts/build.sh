#!/usr/bin/env bash
# Regenerate every preset from the tables in this folder and install them into OrcaSlicer, Bambu Studio,
# QIDI Studio and Snapmaker Orca.
#   scripts/build.sh               generate into ./out and install (all slicers must be closed)
#   scripts/build.sh --no-install  generate into ./out only
# Only presets listed in .installed/*.txt (written by this script) are replaced or removed;
# presets you create yourself in the slicers are never touched.
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

rm -rf out
python3 src/gen_process.py out/orca/process
python3 src/gen_filament.py out/orca/filament
python3 src/gen_machine.py out/orca/machine
python3 src/gen_bambu.py out/orca out/bambu bambu
python3 src/gen_bambu.py out/orca out/qidi qidi
python3 src/gen_snapmaker.py out/orca out/snapmaker
if [[ "${1:-}" == "--no-install" ]]; then
  echo "Generated into ./out (not installed)."
  exit 0
fi

# Match on the binary path: Orca's process name is "orcaslicer_main", not "orca-slicer".
# The AppImages run from /tmp/.mount_*; match their binaries by name.
if pgrep -f '^/opt/orca-slicer/bin/' >/dev/null || pgrep -f '^/opt/bambustudio-bin/' >/dev/null \
   || pgrep -f '/bin/qidi-studio( |$)' >/dev/null || pgrep -f '/bin/snapmaker-orca( |$)' >/dev/null; then
  echo "Close OrcaSlicer, Bambu Studio, QIDI Studio and Snapmaker Orca first; they only read preset files at startup." >&2
  exit 1
fi

install_set() {  # install_set SRC_DIR DEST_DIR MANIFEST
  local src="$1" dest="$2" manifest="$3" rel old="$2"
  if [[ -f "$manifest" ]]; then  # "#dest=" line: the folder of the last install (it moves when you log in or out)
    while IFS= read -r rel; do
      if [[ "$rel" == '#dest='* ]]; then old="${rel#\#dest=}"
      elif [[ -n "$rel" ]]; then rm -f -- "$old/$rel" "$old/${rel%.json}.info"; fi
    done < "$manifest"
  fi
  mkdir -p "$(dirname "$manifest")"
  echo "#dest=$dest" > "$manifest"
  while IFS= read -r rel; do
    mkdir -p "$dest/$(dirname "$rel")"
    cp -- "$src/$rel" "$dest/$rel"
    echo "$rel" >> "$manifest"
  done < <(cd "$src" && find . -name '*.json' -printf '%P\n' | sort)
  echo "Installed $(grep -vc "^#" "$manifest") presets into $dest"
}
install_set out/orca "$ORCA_USER" .installed/orca.txt
install_set out/bambu "$BAMBU_USER" .installed/bambu.txt
install_set out/qidi "$QIDI_USER" .installed/qidi.txt
install_set out/snapmaker "$SNAPMAKER_USER" .installed/snapmaker.txt
echo "Restart the slicers to load the presets."
