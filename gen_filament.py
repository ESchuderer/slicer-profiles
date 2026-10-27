#!/usr/bin/env python3
"""Generate OrcaSlicer filament presets from filaments.json. Usage: gen_filament.py OUT_DIR

Each filaments.json entry:
  "inherits": stock parent (Orca library brand preset, else "Generic <type> @System")
  "notes":    maker specs / handling, shown in the preset's Notes tab
  "s":        Orca setting overrides as single values, plus convenience keys:
              "bed", "bed_l1" = bed temp (normal / first layer) on the smooth PEI, textured PEI
                                and engineering plates; Cool and SuperTack keep the parent's value
              "bed_plates"    = per-plate exceptions, e.g. {"eng": [35, 35], "cool": [0, 0]}
                                (plates: hot, textured, eng, cool, supertack; 0 = not supported)
              "chamber"       = chamber target used by the X-Max 4 start G-code (M141/M191).
                                Chamber control stays off: it would also send M191 to the P2S and U1.
  "bambu":    Bambu Studio parent + extra overrides for the P2S copy (used by gen_bambu.py)
"""
import json
import os
import sys

from resolve import resolve

ORCA_VERSION = '2.4.2.0'
PLATE_KEYS = {'hot': 'hot_plate_temp', 'textured': 'textured_plate_temp', 'eng': 'eng_plate_temp',
              'cool': 'cool_plate_temp', 'supertack': 'supertack_plate_temp'}
BED_PLATES = ('hot', 'textured', 'eng')


def make(name, d):
    resolve(d['inherits'], 'OrcaFilamentLibrary')  # fail early if the parent is missing
    p = {'type': 'filament', 'from': 'User', 'name': name, 'inherits': d['inherits'],
         'filament_settings_id': [name], 'is_custom_defined': '0', 'version': ORCA_VERSION,
         'compatible_printers': [], 'filament_notes': [d.get('notes', '')]}
    s = dict(d['s'])
    bed = s.pop('bed', None)
    bed_l1 = s.pop('bed_l1', bed)
    plates = {plate: (bed, bed_l1) for plate in BED_PLATES} if bed is not None else {}
    plates.update({plate: tuple(t) for plate, t in s.pop('bed_plates', {}).items()})
    for plate, (temp, temp_l1) in plates.items():
        p[PLATE_KEYS[plate]] = [str(temp)]
        p[PLATE_KEYS[plate] + '_initial_layer'] = [str(temp_l1)]
    chamber = s.pop('chamber', None)
    if chamber is not None:
        # Orca renames a parent's legacy "chamber_temperatures" on load, so this key alone wins.
        s['chamber_temperature'] = chamber
        s['activate_chamber_temp_control'] = 0
    for k, v in s.items():
        p[k] = [str(x) for x in v] if isinstance(v, list) else [str(v)]
    return p


def main(out):
    os.makedirs(out, exist_ok=True)
    data = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'filaments.json')))
    for name, d in data.items():
        with open(os.path.join(out, name + '.json'), 'w') as f:
            json.dump(make(name, d), f, indent=4)
    print(len(data), 'filament presets ->', out)


if __name__ == '__main__':
    main(sys.argv[1])
