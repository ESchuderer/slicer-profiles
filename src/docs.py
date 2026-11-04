#!/usr/bin/env python3
"""Generate the preset catalog and the tables of the profile page from the generator's data.

Usage: docs.py           rewrite docs/catalog.md and the generated blocks of docs/profiles.md
       docs.py --check   exit 1 when a committed page differs (the drift test runs this too)
Needs no stock profiles: names come from the tables in src/gen_process.py and the files in config/.
A block of docs/profiles.md starts with `<!-- generated: NAME -->` and ends with `<!-- end generated -->`.
"""

import json
import re
import sys
from pathlib import Path
from typing import cast

from gen_process import SPEED, STYLES, jobs, preset_name

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "docs" / "catalog.md"
PROFILES = ROOT / "docs" / "profiles.md"
PRINTER_NAMES = {"P2S": "Bambu Lab P2S", "U1": "Snapmaker U1", "X-Max4": "Qidi X-Max 4"}
MATERIALS = ("PLA", "PETG", "HIPS", "ASA", "TPU")
# slicer key: (app, print presets of these printer tags, printer models with "(LAN)" presets)
ZIPS = {
    "orca": ("OrcaSlicer", ("P2S", "U1", "X-Max4"), ("Qidi X-Max 4", "Snapmaker U1")),
    "bambu": ("Bambu Studio", ("P2S",), ()),
    "qidi": ("QIDI Studio", ("X-Max4",), ()),
    "snapmaker": ("Snapmaker Orca", ("U1",), ("Snapmaker U1",)),
}
CATALOG_INTRO = """# Preset catalog

Every preset in the release zips, generated from the tables by `src/docs.py`. What the presets set:
[profiles.md](profiles.md). Install: [install.md](install.md).
"""
_BLOCK = re.compile(r"(<!-- generated: (\w+) -->\n).*?(<!-- end generated -->)", re.DOTALL)
type Contents = dict[str, list[str]]


def _json(path: Path) -> dict[str, dict[str, object]]:
    return cast("dict[str, dict[str, object]]", json.loads(path.read_text(encoding="utf-8")))


def contents() -> dict[str, Contents]:
    """Return the preset names of every zip: {slicer: {"process": [...], "filament": [...], "machine": [...]}}."""
    filaments = sorted(_json(ROOT / "config" / "filaments.json"))
    printers = _json(ROOT / "config" / "printers.example.json")
    out: dict[str, Contents] = {}
    for slicer, (_, tags, models) in ZIPS.items():
        process = sorted(
            preset_name(tag, nozzle, style, suffix) for tag, nozzle, style, suffix, _ in jobs() if tag in tags
        )
        machine = sorted(
            f"{str(printers[m]['parent']).format(nozzle=n)} (LAN)"
            for m in models
            for n in cast("list[str]", printers[m]["nozzles"])
        )
        out[slicer] = {"process": process, "filament": filaments, "machine": machine}
    return out


def _table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return "\n".join(lines + ["| " + " | ".join(r) + " |" for r in rows]) + "\n"


def _material(name: str) -> str:
    return next((m for m in MATERIALS if re.search(rf"\b{m}", name)), "other")


def blocks() -> dict[str, str]:
    """Return the generated tables of docs/profiles.md by block name."""
    zips = contents()
    rows: list[list[str]] = []
    for slicer, (app, tags, _) in ZIPS.items():
        names = zips[slicer]["process"]
        per = [f"{PRINTER_NAMES[t]} {sum(f'@{t} ' in n for n in names)}" for t in tags]
        machine = zips[slicer]["machine"]
        rows.append(
            [
                f"`{slicer}` ({app})",
                f"{len(names)}: {', '.join(per)}",
                str(len(zips[slicer]["filament"])),
                f'{len(machine)} "(LAN)"' if machine else "none",
            ]
        )
    styles = [
        [nozzle, style, f"{lh:.2f}", str(walls), f"{infill} %", f"{top}", f"{bottom}"]
        for nozzle, row in STYLES.items()
        for style, lh, walls, infill, top, bottom in row
    ]
    speeds = [[nozzle, *(str(v) for v in values)] for nozzle, values in SPEED.items()]
    by_material: dict[str, list[str]] = {}
    for name in zips["orca"]["filament"]:
        by_material.setdefault(_material(name), []).append(name)
    return {
        "zips": _table(["Zip", "Print presets", "Filament presets", "Printer presets"], rows),
        "styles": _table(
            ["Nozzle", "Style", "Layer mm", "Walls", "Gyroid infill", "Top shell mm", "Bottom shell mm"], styles
        ),
        "speeds": _table(
            [
                "Nozzle",
                "Outer wall",
                "Inner wall",
                "Sparse infill",
                "Solid infill",
                "Top surface",
                "Gap fill",
                "Bridge",
            ],
            speeds,
        ),
        "filaments": _table(
            ["Material", "Presets"], [[m, ", ".join(by_material[m])] for m in MATERIALS if m in by_material]
        ),
    }


def catalog() -> str:
    """Return docs/catalog.md."""
    parts = [CATALOG_INTRO]
    for slicer, (app, _, _) in ZIPS.items():
        zip_contents = contents()[slicer]
        parts.append(f"\n## {app}: `slicer-profiles-{slicer}-<version>.zip`\n")
        parts.append(f"\n### Print presets ({len(zip_contents['process'])})\n\n")
        rows = [[n, PRINTER_NAMES[_tag(n)], n[-3:]] for n in zip_contents["process"]]
        parts.append(_table(["Preset", "Printer", "Nozzle"], rows))
        parts.append(f"\n### Filament presets ({len(zip_contents['filament'])})\n\n")
        parts.append("".join(f"- {n}\n" for n in zip_contents["filament"]))
        if zip_contents["machine"]:
            parts.append(f'\n### "(LAN)" printer presets ({len(zip_contents["machine"])})\n\n')
            parts.append("".join(f"- {n}\n" for n in zip_contents["machine"]))
    return "".join(parts)


def _tag(name: str) -> str:
    return name.rsplit("@", 1)[1].split(maxsplit=1)[0]


def render() -> dict[Path, str]:
    """Return the full expected text of every generated page."""
    page = PROFILES.read_text(encoding="utf-8")
    generated = blocks()
    pieces: list[str] = []
    done = 0
    for m in _BLOCK.finditer(page):
        start, name, end = (cast("str", m.group(i)) for i in (1, 2, 3))
        pieces += [page[done : m.start()], start, "\n", generated.pop(name), "\n", end]
        done = m.end()
    if generated:
        msg = f"{PROFILES.name} lacks the generated blocks {sorted(generated)}"
        raise ValueError(msg)
    page = "".join([*pieces, page[done:]])
    return {CATALOG: catalog(), PROFILES: page}


def main(argv: list[str]) -> int:
    """Write the pages, or with --check report the stale ones."""
    stale = [path for path, text in render().items() if not path.is_file() or path.read_text(encoding="utf-8") != text]
    if "--check" in argv:
        for path in stale:
            print(f"{path.relative_to(ROOT)} is out of date: run src/docs.py", file=sys.stderr)
        return 1 if stale else 0
    for path, text in render().items():
        _ = path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
