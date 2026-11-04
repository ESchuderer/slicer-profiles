#!/usr/bin/env python3
"""Flatten a preset into a standalone JSON that the slicer's command-line mode can load.

Usage: flat.py [--bambu|--qidi|--snapmaker] stock VENDOR "PRESET NAME" OUT.json   (a stock preset, e.g. a printer)
       flat.py [--bambu|--qidi|--snapmaker] file  VENDOR PRESET.json   OUT.json   (a generated user preset)
VENDOR is the stock folder of the parent (BBL, Snapmaker, Qidi, OrcaFilamentLibrary).
"""

import json
import sys
from pathlib import Path
from typing import cast

from resolve import Preset, resolve, source

ORCA_FORMAT = {"orca", "snapmaker"}


def orca_legacy(d: Preset, target: str) -> Preset:
    """Rename legacy keys the way Orca does when it loads each preset (child values then override the parent's).

    Without this, a parent's "chamber_temperatures" would beat the child's "chamber_temperature".
    """
    if target in ORCA_FORMAT and "chamber_temperatures" in d:
        d["chamber_temperature"] = d.pop("chamber_temperatures")
    return d


def flatten(mode: str, vendor: str, src: str, target: str) -> Preset:
    """Return the resolved settings of a stock preset (mode "stock") or a generated preset file (mode "file")."""
    root = source(target)
    if mode == "file":
        user = cast("Preset", json.loads(Path(src).read_text(encoding="utf-8")))
        inherits = user["inherits"]
        if not isinstance(inherits, str):
            msg = f"{src}: inherits is not a string"
            raise TypeError(msg)
        settings = orca_legacy(resolve(inherits, vendor, root), target)
        settings.update(orca_legacy(dict(user), target))
        if user.get("type") == "machine":
            # The CLI refuses printer names it does not ship (error -17); the GUI resolves user printers
            # through "inherits", so test under the parent's name.
            settings["name"] = settings["printer_settings_id"] = inherits
    else:
        settings = orca_legacy(resolve(src, vendor, root), target)
    _ = settings.pop("inherits", None)
    settings["from"] = "system"
    settings["instantiation"] = "true"
    return settings


def main(argv: list[str]) -> int:
    """Write the flattened preset to OUT.json."""
    target = "orca"
    if argv and argv[0] in {"--bambu", "--qidi", "--snapmaker"}:
        target, argv = argv[0][2:], argv[1:]
    if len(argv) != 4 or argv[0] not in {"stock", "file"}:  # noqa: PLR2004 (MODE VENDOR SRC OUT)
        print(__doc__, file=sys.stderr)
        return 64
    mode, vendor, src, out = argv
    _ = Path(out).write_text(json.dumps(flatten(mode, vendor, src, target), indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
