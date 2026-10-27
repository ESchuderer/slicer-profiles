#!/usr/bin/env python3
"""Resolve OrcaSlicer / Bambu Studio preset inheritance from the installed stock profile library.

Usage: resolve.py [--bambu] VENDOR "PRESET NAME" [key ...]
  e.g. resolve.py BBL "0.16mm High Quality @BBL P2S" outer_wall_speed wall_loops
       resolve.py OrcaFilamentLibrary "Generic PETG @System" nozzle_temperature
       resolve.py --bambu BBL "Generic PLA @BBL P2S" nozzle_temperature
Prints the fully resolved value of each key (all keys if none given).
"""
import glob
import json
import os
import sys

ORCA_PROFILES = '/opt/orca-slicer/resources/profiles'
BAMBU_PROFILES = '/opt/bambustudio-bin/resources/profiles'
QIDI_APPIMAGE = '/opt/qidi-studio-appimage/qidi-studio-appimage.AppImage'
SNAPMAKER_APPIMAGE = '/opt/snapmaker-orca-appimage/snapmaker-orca-appimage.AppImage'
_index_cache = {}


def appimage_profiles(appimage):
    """Stock profile folder packed inside an AppImage, extracted once per AppImage version into ~/.cache."""
    import subprocess
    stamp = int(os.path.getmtime(appimage))
    dest = os.path.expanduser(f'~/.cache/slicer-profile/{os.path.basename(appimage)}-{stamp}')
    profiles = os.path.join(dest, 'squashfs-root', 'resources', 'profiles')
    if not os.path.isdir(profiles):
        os.makedirs(dest, exist_ok=True)
        subprocess.run([appimage, '--appimage-extract', 'resources/profiles/*'], cwd=dest, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return profiles


def _index(root):
    if root not in _index_cache:
        idx = {}
        for vendor in os.listdir(root):
            d = os.path.join(root, vendor)
            if not os.path.isdir(d):
                continue
            for f in glob.glob(d + '/**/*.json', recursive=True):
                try:
                    j = json.load(open(f))
                except Exception:
                    continue
                if isinstance(j, dict) and 'name' in j:
                    idx.setdefault((vendor, j['name']), j)
        _index_cache[root] = idx
    return _index_cache[root]


def _find(name, vendor, root):
    idx = _index(root)
    for v in (vendor, 'OrcaFilamentLibrary'):
        if (v, name) in idx:
            return v, idx[(v, name)]
    for (v, n), j in idx.items():
        if n == name:
            return v, j
    raise KeyError(f'stock preset not found: {name!r} (searched {root})')


def resolve(name, vendor, root=ORCA_PROFILES):
    """Fully resolved settings of a stock preset: parents first, each child overriding."""
    v, j = _find(name, vendor, root)
    out = dict(resolve(j['inherits'], v, root)) if j.get('inherits') else {}
    out.update(j)
    return out


if __name__ == '__main__':
    args = sys.argv[1:]
    root = ORCA_PROFILES
    if args and args[0] == '--bambu':
        root, args = BAMBU_PROFILES, args[1:]
    if len(args) < 2:
        sys.exit(__doc__)
    settings = resolve(args[1], args[0], root)
    for k in (' '.join(args[2:]).split() or sorted(settings)):
        print(k, '=', settings.get(k))
