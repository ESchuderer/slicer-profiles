#!/usr/bin/env python3
"""Generate OrcaSlicer print (process) presets for the P2S, U1 and X-Max 4.

Every preset inherits the printer's stock preset for its nozzle and stores only the values set here;
Orca shows everything else as inherited. Edit the tables, then run ./build.sh.
Usage: gen_process.py OUT_DIR
"""
import json
import math
import os
import sys

from resolve import resolve

ORCA_VERSION = '2.4.2.0'

# printer tag -> (Orca vendor folder, stock parent preset per nozzle, extruder variants)
# P2S presets hold 2 values per speed/acceleration key (Direct Drive Standard / High Flow hotend).
PRINTERS = {
    'P2S': ('BBL', {'0.4': '0.16mm High Quality @BBL P2S',
                    '0.6': '0.24mm Balanced Quality @BBL P2S 0.6 nozzle',
                    '0.8': '0.32mm Balanced Quality @BBL P2S 0.8 nozzle'}, 2),
    'U1': ('Snapmaker', {'0.4': '0.16 High Quality @Snapmaker U1 (0.4 nozzle)',
                         '0.6': '0.24 Standard @Snapmaker U1 (0.6 nozzle)',
                         '0.8': '0.32 Standard @Snapmaker U1 (0.8 nozzle)'}, 1),
    'X-Max4': ('Qidi', {'0.4': '0.16mm Balanced Quality @X-Max 4',
                        '0.6': '0.24mm Balanced Strength @X-Max 4 0.6 nozzle',
                        '0.8': '0.32mm Balanced Strength @X-Max 4 0.8 nozzle'}, 1),
}

# Base styles per nozzle: (style, layer height mm, walls, gyroid %, top shell mm, bottom shell mm)
# Standard is the everyday default: Quality's walls, widths and speeds at a taller layer with lighter infill.
STYLES = {
    '0.4': [('Detail', 0.12, 3, 15, 1.0, 0.8), ('Quality', 0.16, 3, 20, 1.0, 0.8), ('Standard', 0.20, 3, 15, 1.0, 0.8),
            ('Strong', 0.20, 5, 40, 1.4, 1.2)],
    '0.6': [('Quality', 0.20, 3, 20, 1.2, 1.0), ('Standard', 0.24, 3, 15, 1.2, 1.0), ('Strong', 0.28, 4, 40, 1.6, 1.2)],
    '0.8': [('Quality', 0.28, 2, 20, 1.4, 1.1), ('Standard', 0.32, 2, 15, 1.4, 1.1), ('Strong', 0.36, 3, 40, 1.8, 1.4)],
}

# Line widths mm: (outer wall, inner wall, sparse infill, internal solid). Strong uses wider inner/infill lines.
WIDTH = {'0.4': (0.42, 0.45, 0.45, 0.42), '0.6': (0.62, 0.65, 0.68, 0.62), '0.8': (0.82, 0.85, 0.90, 0.82)}
WIDTH_STRONG = {'0.4': (0.42, 0.48, 0.50, 0.45), '0.6': (0.62, 0.68, 0.72, 0.65), '0.8': (0.82, 0.88, 0.95, 0.85)}

# Speeds mm/s: (outer, inner, sparse infill, internal solid, top, gap, bridge).
# Strong: outer +10, inner +20. Detail: outer 40, top 60. The filament's max volumetric speed caps all of them.
SPEED = {'0.4': (50, 100, 150, 120, 80, 50, 30), '0.6': (50, 90, 120, 100, 70, 40, 25), '0.8': (40, 70, 100, 80, 60, 30, 20)}

# Identical in every preset (plain values)
COMMON = {
    'sparse_infill_pattern': 'gyroid', 'top_surface_pattern': 'monotonicline', 'bottom_surface_pattern': 'monotonic',
    'internal_solid_infill_pattern': 'monotonic', 'wall_generator': 'arachne', 'wall_sequence': 'inner wall/outer wall',
    'precise_outer_wall': '1', 'reduce_crossing_wall': '1', 'seam_position': 'aligned', 'staggered_inner_seams': '1',
    'ensure_vertical_shell_thickness': 'ensure_all', 'detect_overhang_wall': '1', 'slowdown_for_curled_perimeters': '1',
    'enable_support': '0', 'ironing_type': 'no ironing',
    'enable_arc_fitting': '0',  # Orca advises off on Klipper; the U1 0.4 parent had it on
    'infill_wall_overlap': '15%',  # every vendor parent uses 15 %; more bulges top surfaces without measured strength gain
}
# Identical in every preset (speed/acceleration keys, written per extruder variant)
COMMON_MOTION = {
    'small_perimeter_speed': '50%', 'small_perimeter_threshold': 4,  # threshold 0 (P2S/U1 parents) disables the slowdown
    'internal_bridge_speed': '150%', 'support_speed': 80, 'travel_speed': 400,
    'default_acceleration': 5000, 'inner_wall_acceleration': 4000, 'top_surface_acceleration': 2000,
    'sparse_infill_acceleration': 6000, 'internal_solid_infill_acceleration': 4000,
    'initial_layer_acceleration': 500, 'travel_acceleration': 8000, 'bridge_acceleration': 1000,
}

# Multi-material supports: support base in the model filament (slot 1), interface from slot/tool 2
# (PLA under PETG or PETG under PLA), zero Z gap. Normal supports: Bambu Studio tree styles never put
# interface material under branches, and Orca organic trees missed it on some geometries.
MM_SUPPORT = {
    'enable_support': '1', 'support_type': 'normal(auto)', 'support_style': 'default', 'support_threshold_angle': '30',
    'support_top_z_distance': '0', 'support_bottom_z_distance': '0',
    'support_interface_top_layers': '3', 'support_interface_bottom_layers': '3', 'support_interface_spacing': '0',
    'support_bottom_interface_spacing': '0', 'support_interface_pattern': 'rectilinear_interlaced',
    'support_interface_filament': '2', 'support_filament': '1', 'support_interface_not_for_body': '1',
    'support_base_pattern': 'rectilinear-grid', 'support_base_pattern_spacing': '2.5',
    'support_object_xy_distance': '0.3', 'independent_support_layer_height': '0', 'max_bridge_length': '0',
    'enable_prime_tower': '1', 'support_interface_speed': 60,
}
# U1 multicolour decor: scarf seam, ironed top surfaces, Snapmaker's prime tower values for 0.12 mm layers.
DECOR = {
    'seam_slope_type': 'external', 'seam_slope_conditional': '1', 'ironing_type': 'top', 'ironing_speed': '30',
    'ironing_flow': '10%', 'ironing_spacing': '0.15', 'enable_prime_tower': '1', 'prime_tower_width': '30',
    'prime_volume': '27', 'prime_tower_brim_width': '5', 'wipe_tower_extra_rib_length': '8',
}
# Extra overrides for one printer's variant: (printer tag, suffix) -> overrides
PER_PRINTER = {
    # U1 type-2 tower: shell in the model filament, wider brim (Snapmaker: PLA+PETG towers delaminate)
    ('U1', 'MM-Support'): {'wipe_tower_filament': '1', 'prime_tower_brim_width': '5'},
}

# Variants built on a base style: (printer tags, nozzle, base style, name suffix, overrides)
EXTRA = [(('P2S', 'U1', 'X-Max4'), nozzle, style[0], 'MM-Support', MM_SUPPORT)
         for nozzle in STYLES for style in STYLES[nozzle]]  # every base style gets an MM-Support variant
EXTRA += [
    (('U1',), '0.4', 'Detail', 'Decor', DECOR),
]

# Keys stored per extruder variant (arrays) — detected from a P2S stock preset.
VECTOR_KEYS = {k for k, v in resolve('0.16mm High Quality @BBL P2S', 'BBL').items() if isinstance(v, list)}


def val(key, value, variants):
    value = str(value)
    return [value] * variants if key in VECTOR_KEYS else value


def make(tag, nozzle, style, suffix='', overrides=None):
    vendor, parents, variants = PRINTERS[tag]
    parent = parents[nozzle]
    resolve(parent, vendor)  # fail early if the stock parent is missing
    _, lh, walls, infill, top_mm, bot_mm = next(s for s in STYLES[nozzle] if s[0] == style)
    strong = style == 'Strong'
    ow, iw, fw, sw = (WIDTH_STRONG if strong else WIDTH)[nozzle]
    so, si, ss, sis, st, sg, sb = SPEED[nozzle]
    if strong:
        so, si = so + 10, si + 20
    if style == 'Detail':
        so, st = 40, 60
    n = float(nozzle)
    label = suffix if suffix == 'Decor' else f'{style} {suffix}'.strip()
    name = f'{lh:.2f}mm {label} @{tag} {nozzle}'

    s = dict(COMMON)
    s.update({
        'layer_height': f'{lh}',
        'initial_layer_print_height': '0.2' if nozzle == '0.4' else f'{min(max(lh, n * 0.5), n * 0.6):.2f}',
        'wall_loops': str(walls),
        'top_shell_thickness': f'{top_mm}', 'bottom_shell_thickness': f'{bot_mm}',
        'top_shell_layers': str(math.ceil(top_mm / lh - 1e-6)), 'bottom_shell_layers': str(math.ceil(bot_mm / lh - 1e-6)),
        'sparse_infill_density': f'{infill}%',
        'elefant_foot_compensation': '0.2' if nozzle == '0.8' else '0.15',  # P2S 0.6/0.8 parents have 0
        'only_one_wall_top': '0' if strong else '1',
        'line_width': f'{ow}', 'outer_wall_line_width': f'{ow}', 'inner_wall_line_width': f'{iw}',
        'sparse_infill_line_width': f'{fw}', 'internal_solid_infill_line_width': f'{sw}', 'top_surface_line_width': f'{ow}',
        'initial_layer_line_width': f'{round(n * 1.25, 2)}',
    })
    motion = dict(COMMON_MOTION)
    motion.update({
        'outer_wall_speed': so, 'inner_wall_speed': si, 'sparse_infill_speed': ss, 'internal_solid_infill_speed': sis,
        'top_surface_speed': st, 'gap_infill_speed': sg, 'bridge_speed': sb,
        'initial_layer_speed': 35 if nozzle == '0.4' else 30, 'initial_layer_infill_speed': 60 if nozzle == '0.4' else 45,
        'outer_wall_acceleration': 2500 if strong else 2000,
    })
    extra = PER_PRINTER.get((tag, suffix), {})
    for k, v in list(motion.items()) + list((overrides or {}).items()) + list(extra.items()):
        s[k] = val(k, v, variants)

    preset = {'type': 'process', 'from': 'User', 'name': name, 'inherits': parent,
              'print_settings_id': name, 'is_custom_defined': '0', 'version': ORCA_VERSION}
    preset.update(s)
    return preset


def main(out):
    os.makedirs(out, exist_ok=True)
    jobs = [(tag, nozzle, style[0], '', None) for tag in PRINTERS for nozzle in STYLES for style in STYLES[nozzle]]
    jobs += [(tag, nozzle, style, suffix, ov) for tags, nozzle, style, suffix, ov in EXTRA for tag in tags]
    for job in jobs:
        preset = make(*job)
        with open(os.path.join(out, preset['name'] + '.json'), 'w') as f:
            json.dump(preset, f, indent=4)
    print(len(jobs), 'process presets ->', out)


if __name__ == '__main__':
    main(sys.argv[1])
