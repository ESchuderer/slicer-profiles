#!/usr/bin/env bash
# Smoke-test the generated presets with each slicer's command-line mode. Run ./build.sh first.
#   ./test_slice.sh        representative slices per printer (U1 and Max 4 through their "(LAN)" presets)
#   ./test_slice.sh --all  every generated print preset (takes a few minutes)
# Prints key values and the chamber / exhaust / purifier commands read back from the G-code.
# The CLI cannot test multi-filament supports or tool changes (interfaces are dropped even with stock
# presets), so check those in the GUI preview instead.
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1
HERE="$(cd "$(dirname "$0")" && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
cd "$T" || exit 1  # the CLI writes result.json into the current directory

KEYS='layer_height|wall_loops|sparse_infill_density|outer_wall_speed|nozzle_temperature|chamber_temperature|bed_temperature_formula|print_settings_id|filament_settings_id|printer_settings_id'
CMDS='^(M141 S|M191 S|M106 P3 S|SET_PURIFIER_MODE|WAIT_CHAMBER_TEMP|SM_PRINT_AUTO_FEED EXTRUDER=0)'
fails=0

slice() {  # slice SLICER(orca|bambu) MACHINE(stock name or generated .json) PROCESS_FILE FILAMENT_FILE [MODEL]
  local which="$1" machine="$2" proc="$3" fil="$4" model="${5:-$HERE/test_models/cube.stl}"
  local bin=orca-slicer flag='' vendor fvendor=OrcaFilamentLibrary mmode=stock
  case "$machine" in *P2S*) vendor=BBL ;; *Snapmaker*) vendor=Snapmaker ;; *) vendor=Qidi ;; esac
  if [[ "$machine" == *.json ]]; then mmode='file'; fi
  case "$which" in
    bambu) bin=bambu-studio; flag=--bambu; fvendor=BBL ;;
    qidi) bin=/opt/qidi-studio-appimage/qidi-studio-appimage.AppImage; flag=--qidi; vendor='X 4 Series'; fvendor='X 4 Series' ;;
    snapmaker) bin=/opt/snapmaker-orca-appimage/snapmaker-orca-appimage.AppImage; flag=--snapmaker ;;
  esac
  if ! { python3 "$HERE/flat.py" $flag "$mmode" "$vendor" "$machine" m.json &&
         python3 "$HERE/flat.py" $flag file "$vendor" "$proc" p.json &&
         python3 "$HERE/flat.py" $flag file "$fvendor" "$fil" f.json; }; then
    echo "FAIL flatten: $proc"; fails=$((fails + 1)); return
  fi
  python3 -c "import json; d = json.load(open('m.json')); d['curr_bed_type'] = 'Textured PEI Plate'; json.dump(d, open('m.json', 'w'))"
  rm -rf o && mkdir o
  if timeout 300 "$bin" --load-settings "m.json;p.json" --load-filaments "f.json" --slice 0 --outputdir o "$model" > log.txt 2>&1 \
     && [[ -f o/plate_1.gcode ]]; then
    printf 'OK   %-6s %s + %s\n' "$which" "$(basename "$proc" .json)" "$(basename "$fil" .json)"
    grep -E "^; ($KEYS) = " o/plate_1.gcode | sed 's/^; /       /' | tr '\n' ';'
    echo
    grep -E "$CMDS" o/plate_1.gcode | head -6 | sed 's/^/       > /'
  else
    printf 'FAIL %-6s %s + %s\n' "$which" "$(basename "$proc" .json)" "$(basename "$fil" .json)"
    grep -i -E 'error|not support' log.txt | head -3 | sed 's/^/       /'
    fails=$((fails + 1))
  fi
}

O="$HERE/out/orca"
B="$HERE/out/bambu"
M="$O/machine"
Q="$HERE/out/qidi"
SM="$HERE/out/snapmaker"
[[ -d "$O" && -d "$B" ]] || { echo "Run ./build.sh first." >&2; exit 1; }

if [[ "${1:-}" == "--all" ]]; then
  for p in "$O"/process/*.json; do
    n="${p##* }"; n="${n%.json}"
    case "$p" in
      *@P2S*) m="Bambu Lab P2S $n nozzle" ;;
      *@U1*) m="$M/Snapmaker U1 ($n nozzle) (LAN).json" ;;
      *) m="$M/Qidi X-Max 4 $n nozzle (LAN).json" ;;
    esac
    slice orca "$m" "$p" "$O/filament/SUNLU PLA+ 2.0 HQ.json"
  done
  for p in "$B"/process/*.json; do
    slice bambu "Bambu Lab P2S $(basename "${p##* }" .json) nozzle" "$p" "$B/filament/SUNLU PLA+ 2.0 HQ.json"
  done
else
  slice orca "Bambu Lab P2S 0.4 nozzle" "$O/process/0.20mm Strong @P2S 0.4.json" "$O/filament/SUNLU PETG 2.0 HQ.json"
  slice orca "Bambu Lab P2S 0.4 nozzle" "$O/process/0.20mm Standard @P2S 0.4.json" "$O/filament/SUNLU PLA+ 2.0 HQ.json"
  slice orca "Bambu Lab P2S 0.8 nozzle" "$O/process/0.36mm Strong @P2S 0.8.json" "$O/filament/SUNLU TPU 95A HQ.json"
  slice orca "$M/Snapmaker U1 (0.4 nozzle) (LAN).json" "$O/process/0.16mm Quality @U1 0.4.json" "$O/filament/SUNLU PLA+ 2.0 HQ.json"
  slice orca "$M/Snapmaker U1 (0.4 nozzle) (LAN).json" "$O/process/0.12mm Decor @U1 0.4.json" "$O/filament/SUNLU PLA Matte HQ.json"
  slice orca "$M/Snapmaker U1 (0.6 nozzle) (LAN).json" "$O/process/0.20mm Quality @U1 0.6.json" "$O/filament/SUNLU PETG 2.0 HQ.json"
  slice orca "$M/Snapmaker U1 (0.8 nozzle) (LAN).json" "$O/process/0.36mm Strong @U1 0.8.json" "$O/filament/SUNLU ASA HQ.json"
  slice orca "$M/Snapmaker U1 (0.8 nozzle) (LAN).json" "$O/process/0.32mm Standard @U1 0.8.json" "$O/filament/SUNLU PLA+ 2.0 HQ.json"
  slice orca "$M/Qidi X-Max 4 0.6 nozzle (LAN).json" "$O/process/0.28mm Strong @X-Max4 0.6.json" "$O/filament/SUNLU ASA HQ.json"
  slice orca "$M/Qidi X-Max 4 0.4 nozzle (LAN).json" "$O/process/0.16mm Quality @X-Max4 0.4.json" "$O/filament/SUNLU PLA+ 2.0 HQ.json"
  slice orca "$M/Qidi X-Max 4 0.4 nozzle (LAN).json" "$O/process/0.20mm Strong MM-Support @X-Max4 0.4.json" "$O/filament/eSUN PETG HQ.json" "$HERE/test_models/tshape.stl"
  slice bambu "Bambu Lab P2S 0.4 nozzle" "$B/process/0.16mm Quality MM-Support @P2S 0.4.json" "$B/filament/SUNLU ASA HQ.json" "$HERE/test_models/tshape.stl"
  slice bambu "Bambu Lab P2S 0.6 nozzle" "$B/process/0.24mm Standard @P2S 0.6.json" "$B/filament/SUNLU PETG 2.0 HQ.json"
  slice bambu "Bambu Lab P2S 0.8 nozzle" "$B/process/0.28mm Quality @P2S 0.8.json" "$B/filament/SUNLU HS Matte PETG HQ.json"
  slice qidi "X-Max 4 0.4 nozzle" "$Q/process/0.20mm Strong @X-Max4 0.4.json" "$Q/filament/SUNLU ASA HQ.json"
  slice qidi "X-Max 4 0.4 nozzle" "$Q/process/0.20mm Standard @X-Max4 0.4.json" "$Q/filament/SUNLU PETG 2.0 HQ.json"
  slice qidi "X-Max 4 0.6 nozzle" "$Q/process/0.20mm Quality @X-Max4 0.6.json" "$Q/filament/SUNLU PLA+ 2.0 HQ.json"
  slice snapmaker "$SM/machine/Snapmaker U1 (0.4 nozzle) (LAN).json" "$SM/process/0.16mm Quality @U1 0.4.json" "$SM/filament/SUNLU PLA+ 2.0 HQ.json"
  slice snapmaker "$SM/machine/Snapmaker U1 (0.4 nozzle) (LAN).json" "$SM/process/0.20mm Standard @U1 0.4.json" "$SM/filament/SUNLU PETG 2.0 HQ.json"
  slice snapmaker "$SM/machine/Snapmaker U1 (0.6 nozzle) (LAN).json" "$SM/process/0.28mm Strong @U1 0.6.json" "$SM/filament/SUNLU ASA HQ.json"
fi
echo "Failures: $fails"
exit $(( fails > 0 ))
