#!/usr/bin/env python3
"""Port generated Orca presets to a Bambu Studio-family slicer.
Usage: gen_bambu.py ORCA_OUT_DIR OUT_DIR [bambu|qidi]   (default: bambu)

  bambu: Bambu Studio, the P2S presets
  qidi:  QIDI Studio, the X-Max 4 presets

Process presets keep their stock parent (both apps ship presets with the same names as Orca).
Filaments inherit the "<target>.inherits" parent from config/filaments.json, because these apps have no
Orca filament library. Keys the app does not know are dropped (and listed); arrays are sized like the parent's.
"""
import json
import os
import sys

from resolve import BAMBU_PROFILES, QIDI_APPIMAGE, appimage_profiles, resolve

TARGETS = {
    'bambu': {'profiles': lambda: BAMBU_PROFILES, 'vendor': 'BBL', 'version': '02.08.02.61', 'tag': '@P2S',
              'filament_suffix': '',
              # Bambu splits some generic parents by nozzle (e.g. Generic PETG HF); list all P2S nozzles.
              'printers': ['Bambu Lab P2S 0.4 nozzle', 'Bambu Lab P2S 0.6 nozzle', 'Bambu Lab P2S 0.8 nozzle']},
    'qidi': {'profiles': lambda: appimage_profiles(QIDI_APPIMAGE), 'vendor': 'X 4 Series', 'version': '02.07.02.60',
             'tag': '@X-Max4',
             # QIDI's filaments exist once per nozzle; inherit the 0.4 one and allow all three nozzles.
             'filament_suffix': ' @Qidi X-Max 4 0.4 nozzle',
             'printers': ['X-Max 4 0.4 nozzle', 'X-Max 4 0.6 nozzle', 'X-Max 4 0.8 nozzle']},
}
# Supported by Bambu Studio 2.8.2 and QIDI Studio 2.07 (checked in their binaries) but absent from parent files.
BS_EXTRA_KEYS = {'wall_sequence', 'precise_outer_wall', 'ensure_vertical_shell_thickness', 'internal_solid_infill_pattern',
                 'support_interface_not_for_body', 'independent_support_layer_height', 'filament_notes'}
# Orca enum value -> Bambu Studio enum value
ENUM_MAP = {('ensure_vertical_shell_thickness', 'ensure_all'): 'enabled'}
SKIP = {'type', 'from', 'name', 'inherits', 'is_custom_defined', 'version', 'print_settings_id',
        'filament_settings_id', 'compatible_printers', 'activate_chamber_temp_control',
        # Only the Orca Max 4 start G-code reads it; QIDI Studio keeps QIDI's own air-filtration settings.
        'during_print_exhaust_fan_speed'}
dropped = {}


def port(preset, parent, kind, t, extra=None):
    base = resolve(parent, t['vendor'], t['profiles']())
    out = {'type': kind, 'from': 'User', 'name': preset['name'], 'inherits': parent,
           'is_custom_defined': '0', 'version': t['version']}
    if kind == 'process':
        out['print_settings_id'] = preset['name']
    else:
        out['filament_settings_id'] = [preset['name']]
    src = dict(preset)
    src.update(extra or {})
    for k, v in src.items():
        if k in SKIP:
            continue
        if k == 'only_one_wall_top':  # ignored as a legacy key by Bambu Studio 2.8; its option is top_one_wall_type
            out['top_one_wall_type'] = 'all top' if (v[0] if isinstance(v, list) else str(v)) == '1' else 'not apply'
            continue
        if k == 'chamber_temperature':  # these apps still use the plural key
            k = 'chamber_temperatures'
        if k not in base and k not in BS_EXTRA_KEYS:
            dropped[k] = dropped.get(k, 0) + 1
            continue
        one = v[0] if isinstance(v, list) else str(v)
        one = ENUM_MAP.get((k, one), one)
        pv = base.get(k, v)
        out[k] = [one] * max(1, len(pv)) if isinstance(pv, list) else one
    return out


def main(orca_out, out, target='bambu'):
    t = TARGETS[target]
    os.makedirs(os.path.join(out, 'process'), exist_ok=True)
    os.makedirs(os.path.join(out, 'filament'), exist_ok=True)
    n_proc = 0
    for f in sorted(os.listdir(os.path.join(orca_out, 'process'))):
        if t['tag'] not in f:
            continue
        p = json.load(open(os.path.join(orca_out, 'process', f)))
        with open(os.path.join(out, 'process', f), 'w') as fh:
            json.dump(port(p, p['inherits'], 'process', t), fh, indent=4)
        n_proc += 1
    data = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'filaments.json')))
    for name, d in data.items():
        p = json.load(open(os.path.join(orca_out, 'filament', name + '.json')))
        q = port(p, d[target]['inherits'] + t['filament_suffix'], 'filament', t, d[target].get('s'))
        # On the P2S the chamber value only selects the airflow mode (>= 40 C: heating mode); the Max 4 heats to it.
        q['compatible_printers'] = t['printers']
        with open(os.path.join(out, 'filament', name + '.json'), 'w') as fh:
            json.dump(q, fh, indent=4)
    print(f'{n_proc} process + {len(data)} filament presets -> {out}')
    if dropped:
        print(f'  not in {target}, dropped:', ', '.join(sorted(dropped)))


if __name__ == '__main__':
    main(*sys.argv[1:4])
