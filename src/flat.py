#!/usr/bin/env python3
"""Flatten a preset into a standalone JSON that the slicer's command-line mode can load.

Usage: flat.py [--bambu|--qidi|--snapmaker] stock VENDOR "PRESET NAME" OUT.json   (a stock preset, e.g. a printer)
       flat.py [--bambu|--qidi|--snapmaker] file  VENDOR PRESET.json   OUT.json   (a generated user preset)
VENDOR is the stock folder of the parent (BBL, Snapmaker, Qidi, OrcaFilamentLibrary).
"""
import json
import sys

from resolve import BAMBU_PROFILES, ORCA_PROFILES, QIDI_APPIMAGE, SNAPMAKER_APPIMAGE, appimage_profiles, resolve

args = sys.argv[1:]
root, orca_format = ORCA_PROFILES, True
if args and args[0] in ('--bambu', '--qidi', '--snapmaker'):
    root = {'--bambu': lambda: BAMBU_PROFILES, '--qidi': lambda: appimage_profiles(QIDI_APPIMAGE),
            '--snapmaker': lambda: appimage_profiles(SNAPMAKER_APPIMAGE)}[args[0]]()
    orca_format, args = args[0] == '--snapmaker', args[1:]
if len(args) != 4:
    sys.exit(__doc__)
mode, vendor, src, out = args


def orca_legacy(d):
    # Orca renames legacy keys when it loads each preset (child values then override the parent's).
    # Without this, a parent's "chamber_temperatures" would beat the child's "chamber_temperature".
    if orca_format and 'chamber_temperatures' in d:
        d['chamber_temperature'] = d.pop('chamber_temperatures')
    return d


if mode == 'file':
    user = json.load(open(src))
    settings = orca_legacy(resolve(user['inherits'], vendor, root))
    settings.update(orca_legacy(dict(user)))
    if user.get('type') == 'machine':
        # The CLI refuses printer names it does not ship (error -17); the GUI resolves user printers
        # through "inherits", so test under the parent's name.
        settings['name'] = settings['printer_settings_id'] = user['inherits']
else:
    settings = orca_legacy(resolve(src, vendor, root))
settings.pop('inherits', None)
settings['from'] = 'system'
settings['instantiation'] = 'true'
json.dump(settings, open(out, 'w'), indent=1)
