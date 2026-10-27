#!/usr/bin/env python3
"""Generate OrcaSlicer printer presets with the network connection from printers.json. Usage: gen_machine.py OUT_DIR

Orca keeps a printer's address inside a user printer preset, so each networked printer gets one
"<stock name> (LAN)" preset per nozzle that inherits everything else from the stock preset.
Print presets listing the stock printer stay compatible with these copies.
The same presets carry the printer-level fixes in FIXES below (from the 2026-10-01 verification,
see the playbook's "Verification log" tab).

Each printers.json entry:
  "host":    IP or hostname of the printer (Moonraker behind the web UI on port 80)
  "parent":  stock printer preset name, "{nozzle}" is replaced per nozzle
  "vendor":  Orca system folder the parent lives in
  "nozzles": nozzle sizes to generate
"""
import json
import os
import sys

from resolve import resolve

ORCA_VERSION = '2.4.2.0'

# --- Printer-level fixes -----------------------------------------------------------------------

# Multi-material jobs: the bed follows the filament printed first (PLA part -> PLA bed), as on the
# P2S, instead of Orca's default "hottest filament in the job".
COMMON_FIXES = {'bed_temperature_formula': 'by_first_filament'}

# Snapmaker Top Cover purifier mode, mirroring Snapmaker Orca (its chamber_cooling_mode uses the same
# softening thresholds: <= 50 C strong cooling, <= 70 C weak cooling, otherwise keep warm).
# Without the cover the firmware only answers "purifier not exist" and the print continues.
U1_PURIFIER = """;===== Top Cover purifier mode (ignored without the cover) =====
{if min_vitrification_temperature <= 50}
SET_PURIFIER_MODE MODE=1 DESIRE_TEMP=42 ALARM_TEMP=45 FAN_SPEED=0.6 DELAY_OFF=0
{elsif min_vitrification_temperature <= 70}
SET_PURIFIER_MODE MODE=3 DESIRE_TEMP=0 FAN_SPEED=0.6 DELAY_OFF=600
{else}
SET_PURIFIER_MODE MODE=3 DESIRE_TEMP=45 FAN_SPEED=0.6 DELAY_OFF=600
{endif}
"""
U1_GCODE_KEYS = ('change_filament_gcode', 'machine_start_gcode', 'machine_end_gcode',
                 'before_layer_change_gcode', 'layer_change_gcode')


def tools(value, n=4):  # one value per U1 toolhead
    return [str(value)] * n


def replace_once(text, old, new, count=1):
    found = text.count(old)
    if found != count:
        sys.exit(f'gen_machine.py: expected {count} x {old!r} in the stock G-code, found {found}; '
                 'the stock preset changed, review the fix')
    return text.replace(old, new)


def u1_start_gcode(stock):
    g = replace_once(stock, '\nG28 X Y\n', '\n' + U1_PURIFIER + 'G28 X Y\n')
    # Snapmaker's own profile waits (max 180 s) for the cover's chamber target before homing Z.
    return replace_once(g, 'G0 Z5 F10000\nG28 Z\n', 'G0 Z5 F10000\nWAIT_CHAMBER_TEMP TIMEOUT=180\nG28 Z\n')


def u1_fixes(nozzle):
    stock04 = resolve('Snapmaker U1 (0.4 nozzle)', 'Snapmaker')
    fixes = dict(COMMON_FIXES)
    fixes['adaptive_bed_mesh_margin'] = '5'  # probe 5 mm around the part (from the user's U1 profile)
    fixes['machine_start_gcode'] = u1_start_gcode(stock04['machine_start_gcode'])
    if nozzle == '0.4':
        # Snapmaker's current default (Snapmaker Orca since Nov 2025, Orca main after PR #15039)
        fixes.update(retraction_length=tools(1.5), retraction_speed=tools(30), deretraction_speed=tools(30))
        return fixes
    # Orca 2.4.2's U1 0.6/0.8 presets are a generic 5-tool toolchanger without Snapmaker's tool-change
    # G-code. Port of OrcaSlicer PR #15039: the 0.4 preset's G-code, 4 tools, Snapmaker's values.
    for k in U1_GCODE_KEYS:
        fixes.setdefault(k, stock04[k])
    fixes.update({
        'auxiliary_fan': '1', 'enable_filament_ramming': '0', 'support_multi_bed_types': '0',
        'extruder_clearance_height_to_rod': '27.5', 'extruder_clearance_radius': '72.5',
        'machine_load_filament_time': '0', 'machine_unload_filament_time': '0', 'machine_tool_change_time': '5',
        'machine_max_jerk_z': ['3', '0.4'], 'machine_max_speed_e': ['30', '25'], 'machine_max_speed_z': ['20', '12'],
        'machine_pause_gcode': 'M600', 'nozzle_volume': '143', 'thumbnails': '48x48/PNG, 300x300/PNG',
        'extruder_colour': tools('#FCE94F'), 'extruder_offset': tools('0x0'),
        'long_retractions_when_cut': tools(0), 'retraction_distances_when_cut': tools(18),
        'retraction_length': tools(1.4 if nozzle == '0.6' else 1.5), 'retraction_speed': tools(30),
        'deretraction_speed': tools(30), 'retract_before_wipe': tools('0%'), 'retract_length_toolchange': tools(10),
        'retract_lift_above': tools(0), 'retract_lift_below': tools(269), 'retract_lift_enforce': tools('All Surfaces'),
        'retract_restart_extra': tools(0), 'retract_restart_extra_toolchange': tools(0),
        'retract_when_changing_layer': tools(1), 'retraction_minimum_travel': tools(3 if nozzle == '0.6' else 1),
        'travel_slope': tools(3), 'wipe': tools(1), 'wipe_distance': tools(1 if nozzle == '0.6' else 2),
        'z_hop': tools(0.4), 'z_hop_types': tools('Auto Lift'),
    })
    if nozzle == '0.6':
        fixes['max_layer_height'] = tools(0.42)
    return fixes


def max4_fixes(nozzle):
    stock = resolve(f'Qidi X-Max 4 {nozzle} nozzle', 'Qidi')['machine_start_gcode']
    # Chamber target = hottest chamber value of all filaments in the job (stock: first filament only),
    # but never heat when PLA or TPU (softening <= 50 C) is in the job; run the exhaust instead.
    target = '{if min_vitrification_temperature <= 50}0{else}{overall_chamber_temperature}{endif}'
    g = replace_once(stock, 'M141 S[chamber_temperature]', 'M141 S' + target, count=2)
    g = replace_once(g, 'M191 S[chamber_temperature]', 'M191 S' + target)
    g = replace_once(g, '{if chamber_temperature[0] == 0}',
                     '{if overall_chamber_temperature == 0 or min_vitrification_temperature <= 50}')
    # QIDI's macro scales S/255: the raw percentage gave about 27 % exhaust; the _num value is 0-255.
    g = replace_once(g, 'M106 P3 S[during_print_exhaust_fan_speed]', 'M106 P3 S[during_print_exhaust_fan_speed_num]')
    fixes = dict(COMMON_FIXES)
    fixes['machine_start_gcode'] = g
    return fixes


FIXES = {'Snapmaker U1': u1_fixes, 'Qidi X-Max 4': max4_fixes}

# --- Generation -----------------------------------------------------------------------------------


def make(name, parent, d):
    resolve(parent, d['vendor'])  # fail early if the parent is missing
    return {'type': 'machine', 'from': 'User', 'name': name, 'inherits': parent,
            'printer_settings_id': name, 'is_custom_defined': '0', 'version': ORCA_VERSION,
            'host_type': 'octoprint', 'print_host': d['host'], 'print_host_webui': 'http://' + d['host']}


def main(out):
    os.makedirs(out, exist_ok=True)
    data = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'printers.json')))
    count = 0
    for model, d in data.items():
        for nozzle in d['nozzles']:
            parent = d['parent'].format(nozzle=nozzle)
            name = parent + ' (LAN)'
            preset = make(name, parent, d)
            if model in FIXES:
                preset.update(FIXES[model](nozzle))
            with open(os.path.join(out, name + '.json'), 'w') as f:
                json.dump(preset, f, indent=4)
            count += 1
    print(count, 'printer presets ->', out)


if __name__ == '__main__':
    main(sys.argv[1])
