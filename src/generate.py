#!/usr/bin/env python3
"""Generate Bambu Studio user presets for the Bambu Lab H3C from config/h3c.json and config/filaments.json.

Usage: generate.py OUT_DIR   (writes OUT_DIR/bambu/filament/ and OUT_DIR/bambu/process/)
Every preset inherits a stock H3C preset by name and stores only the values set here. A value is written
once per slot of the parent's list (the H3C keeps one slot per hotend variant: Direct Drive Standard,
High Flow and TPU285), so every hotend gets it. A key the parent does not have stops the build, unless it
is in EXTRA_KEYS.
"""

import json
import sys
from pathlib import Path
from typing import TypedDict, cast

from resolve import Preset, Value, resolve, source
from targets import preset_version

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"
VENDOR = "BBL"
# Keys Bambu Studio reads although its stock files leave them out (checked in Bambu Studio 2.8.2's binary).
EXTRA_KEYS = frozenset({"filament_notes", "support_interface_not_for_body", "independent_support_layer_height"})
type Values = dict[str, str | int | float]


class Printer(TypedDict):
    """config/h3c.json: the printer, its nozzles and the stock parents to build on."""

    printer: str
    tag: str
    nozzles: list[str]
    processes: dict[str, str]  # nozzle -> stock default print preset
    materials: dict[str, dict[str, str]]  # material -> nozzle -> stock Generic filament preset
    styles: dict[str, dict[str, Values]]  # style -> nozzle -> changed keys
    variants: dict[str, Values]  # variant -> changed keys, on every nozzle and style


class Filament(TypedDict):
    """One entry of config/filaments.json."""

    material: str
    notes: str
    s: Values


def printer() -> Printer:
    """Read config/h3c.json."""
    return cast("Printer", json.loads((CONFIG / "h3c.json").read_text(encoding="utf-8")))


def filaments() -> dict[str, Filament]:
    """Read config/filaments.json."""
    return cast("dict[str, Filament]", json.loads((CONFIG / "filaments.json").read_text(encoding="utf-8")))


def process_jobs(p: Printer) -> list[tuple[str, str, str]]:
    """Return (nozzle, style, variant) for every print preset; "" means none. Stock alone is not repeated."""
    styles, variants = ["", *p["styles"]], ["", *p["variants"]]
    return [(n, s, v) for n in p["nozzles"] for s in styles for v in variants if s or v]


def process_name(p: Printer, nozzle: str, style: str, variant: str) -> str:
    """Return e.g. "0.20mm Strong MM-Support @H3C 0.4": the parent's layer height, then style and variant."""
    layer = p["processes"][nozzle].split()[0]
    return f"{layer} {' '.join(x for x in (style, variant) if x)} @{p['tag']} {nozzle}"


def filament_groups(p: Printer, material: str) -> dict[str, list[str]]:
    """Return stock parent -> the printer's nozzles it serves, for one material."""
    groups: dict[str, list[str]] = {}
    for nozzle in p["nozzles"]:
        parent = p["materials"][material].get(nozzle)
        if parent is None:
            msg = f"config/h3c.json: material {material!r} has no parent for the {nozzle} nozzle"
            raise ValueError(msg)
        groups.setdefault(parent, []).append(nozzle)
    return groups


def filament_name(name: str, nozzles: list[str]) -> str:
    """Return the preset name: the filament name for the group with the 0.4 nozzle, else with its nozzles."""
    return name if "0.4" in nozzles else f"{name} {'/'.join(nozzles)} nozzle"


def fit(key: str, value: object, parent: Preset, parent_name: str) -> Value:
    """Return VALUE as the parent stores KEY: one string per slot of the parent's list, or one string."""
    text = str(value)
    if key not in parent:
        if key not in EXTRA_KEYS:
            msg = f"{key!r} is not a key of the stock preset {parent_name!r}"
            raise ValueError(msg)
        return [text]
    slots = parent[key]
    return [text] * max(1, len(slots)) if isinstance(slots, list) else text


def compatible(parent: Preset, parent_name: str, printers: list[str]) -> None:
    """Stop when the stock parent is not made for every printer preset the user preset claims."""
    missing = [p for p in printers if p not in parent.get("compatible_printers", [])]
    if missing:
        msg = f"stock preset {parent_name!r} is not compatible with {missing}"
        raise ValueError(msg)


def make(kind: str, name: str, parent_name: str, values: Values, root: Path) -> Preset:
    """Return one user preset: header keys, then VALUES fitted to the parent."""
    parent = resolve(parent_name, VENDOR, root)
    out: Preset = {"type": kind, "from": "User", "name": name, "inherits": parent_name, "is_custom_defined": "0"}
    out["version"] = preset_version("bambu")
    out["print_settings_id" if kind == "process" else "filament_settings_id"] = name if kind == "process" else [name]
    for key, value in values.items():
        out[key] = fit(key, value, parent, parent_name)
    return out


def presets(root: Path) -> dict[str, Preset]:
    """Return every preset by its path below the output folder (bambu/<kind>/<name>.json)."""
    p = printer()
    out: dict[str, Preset] = {}
    for nozzle, style, variant in process_jobs(p):
        parent_name = p["processes"][nozzle]
        compatible(resolve(parent_name, VENDOR, root), parent_name, [f"{p['printer']} {nozzle} nozzle"])
        values = {**p["styles"].get(style, {}).get(nozzle, {}), **p["variants"].get(variant, {})}
        name = process_name(p, nozzle, style, variant)
        out[f"bambu/process/{name}.json"] = make("process", name, parent_name, values, root)
    for fname, f in filaments().items():
        for parent_name, nozzles in filament_groups(p, f["material"]).items():
            printers = [f"{p['printer']} {n} nozzle" for n in nozzles]
            compatible(resolve(parent_name, VENDOR, root), parent_name, printers)
            name = filament_name(fname, nozzles)
            preset = make("filament", name, parent_name, {**f["s"], "filament_notes": f["notes"]}, root)
            preset["compatible_printers"] = printers
            out[f"bambu/filament/{name}.json"] = preset
    return out


def main(argv: list[str]) -> int:
    """Write every preset below OUT_DIR."""
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 64
    built = presets(source("bambu"))
    for rel, preset in built.items():
        path = Path(argv[0]) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(json.dumps(preset, indent=4), encoding="utf-8")
    print(f"{len(built)} presets -> {argv[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
