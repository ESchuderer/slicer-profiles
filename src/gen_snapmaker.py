#!/usr/bin/env python3
"""Port the generated U1 presets to Snapmaker Orca (Snapmaker's OrcaSlicer fork). Usage: gen_snapmaker.py ORCA_OUT_DIR OUT_DIR

Same preset format as Orca. Print presets get the fork's stock parents (it names them differently);
filaments use the same Orca filament library. The fork's own U1 printers already carry Snapmaker's
tool-change G-code, purifier logic and retraction, so its "(LAN)" printers add only the address
(from config/printers.json) and the shared printer settings below.
"""
import json
import os
import sys

from resolve import SNAPMAKER_APPIMAGE, appimage_profiles, resolve

VERSION = '2.3.3.3'  # the fork's profile version (Snapmaker.json 02.03.03.03)
# Orca 2.4.2 parent -> Snapmaker Orca parent
PARENTS = {
    '0.16 High Quality @Snapmaker U1 (0.4 nozzle)': '0.16mm Standard @Snapmaker U1 (0.4 nozzle)',
    '0.24 Standard @Snapmaker U1 (0.6 nozzle)': '0.24mm Standard @Snapmaker U1 (0.6 nozzle)',
    '0.32 Standard @Snapmaker U1 (0.8 nozzle)': '0.32mm Standard @Snapmaker U1 (0.8 nozzle)',
}
PRINTER_SETTINGS = {
    'bed_temperature_formula': 'by_first_filament',  # PLA part -> PLA bed in multi-material jobs
    'adaptive_bed_mesh_margin': '5',  # probe 5 mm around the part (from the user's U1 profile)
}


def write(path, preset):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(preset, f, indent=4)


def main(orca_out, out):
    fork = appimage_profiles(SNAPMAKER_APPIMAGE)
    n = {'process': 0, 'filament': 0, 'machine': 0}
    for f in sorted(os.listdir(os.path.join(orca_out, 'process'))):
        if '@U1' not in f:
            continue
        p = json.load(open(os.path.join(orca_out, 'process', f)))
        p['inherits'] = PARENTS[p['inherits']]
        resolve(p['inherits'], 'Snapmaker', fork)  # fail early if the fork renamed it
        p['version'] = VERSION
        write(os.path.join(out, 'process', f), p)
        n['process'] += 1
    for f in sorted(os.listdir(os.path.join(orca_out, 'filament'))):
        p = json.load(open(os.path.join(orca_out, 'filament', f)))
        resolve(p['inherits'], 'OrcaFilamentLibrary', fork)
        p['version'] = VERSION
        write(os.path.join(out, 'filament', f), p)
        n['filament'] += 1
    printers = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'printers.json')))
    u1 = printers['Snapmaker U1']
    for nozzle in u1['nozzles']:
        parent = u1['parent'].format(nozzle=nozzle)
        resolve(parent, 'Snapmaker', fork)
        name = parent + ' (LAN)'
        p = {'type': 'machine', 'from': 'User', 'name': name, 'inherits': parent, 'printer_settings_id': name,
             'is_custom_defined': '0', 'version': VERSION, 'host_type': 'octoprint', 'print_host': u1['host'],
             'print_host_webui': 'http://' + u1['host']}
        p.update(PRINTER_SETTINGS)
        write(os.path.join(out, 'machine', name + '.json'), p)
        n['machine'] += 1
    print(f"{n['process']} process + {n['filament']} filament + {n['machine']} printer presets -> {out}")


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
