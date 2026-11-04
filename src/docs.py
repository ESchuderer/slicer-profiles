#!/usr/bin/env python3
"""Generate the preset catalog and the tables of the profile page from the generator's data.

Usage: docs.py           rewrite docs/catalog.md and the generated blocks of docs/profiles.md
       docs.py --check   exit 1 when a committed page differs (the drift test runs this too)
Needs no stock profiles: names and parents come from config/h3c.json and config/filaments.json.
A block of docs/profiles.md starts with `<!-- generated: NAME -->` and ends with `<!-- end generated -->`.
"""

import re
import sys
from functools import cache
from pathlib import Path
from typing import cast

from generate import filament_groups, filament_name, filaments, printer, process_jobs, process_name

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "docs" / "catalog.md"
PROFILES = ROOT / "docs" / "profiles.md"


SLICER, APP, APP_LICENSE = "bambu", "Bambu Studio", "CC-BY-4.0"
CATALOG_INTRO = """# Preset catalog

Every preset in the release zips, generated from the tables by `src/docs.py`. What the presets set:
[profiles.md](profiles.md). Install: [install.md](install.md).
"""
_BLOCK = re.compile(r"(<!-- generated: (\w+) -->\n).*?(<!-- end generated -->)", re.DOTALL)


@cache
def contents() -> dict[str, list[str]]:
    """Return the preset names of the zip: {"process": [...], "filament": [...]}."""
    p = printer()
    process = sorted(process_name(p, *job) for job in process_jobs(p))
    filament = sorted(
        filament_name(name, nozzles) for name, f in filaments().items() for nozzles in filament_groups(p, f).values()
    )
    return {"process": process, "filament": filament}


def _table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return "\n".join(lines + ["| " + " | ".join(r) + " |" for r in rows]) + "\n"


def blocks() -> dict[str, str]:
    """Return the generated tables of docs/profiles.md by block name."""
    p, zips = printer(), contents()
    zip_rows = [[f"`{SLICER}` ({APP})", str(len(zips["process"])), str(len(zips["filament"])), APP_LICENSE]]
    parents = [[n, f"`{p['processes'][n]}`"] for n in p["nozzles"]]
    styles = [
        [name, n, ", ".join(f"`{k}` {v}" for k, v in by_nozzle[n].items())]
        for name, by_nozzle in p["styles"].items()
        for n in p["nozzles"]
    ]
    styles += [[name, "all", ", ".join(f"`{k}` {v}" for k, v in keys.items())] for name, keys in p["variants"].items()]
    filament_rows = [
        [filament_name(name, nozzles), f["material"], f"`{parent}`", ", ".join(nozzles)]
        for name, f in filaments().items()
        for parent, nozzles in filament_groups(p, f).items()
    ]
    return {
        "zips": _table(["Zip", "Print presets", "Filament presets", "License"], zip_rows),
        "parents": _table(["Nozzle", "Stock print preset the styles build on"], parents),
        "styles": _table(["Style or variant", "Nozzle", "Changed keys"], styles),
        "filaments": _table(["Preset", "Material", "Stock parent", "Nozzles"], filament_rows),
    }


def catalog() -> str:
    """Return docs/catalog.md."""
    parts = [CATALOG_INTRO]
    zips = contents()
    parts.append(f"\n## {APP}: `slicer-profiles-{SLICER}-<version>.zip` ({APP_LICENSE})\n")
    for kind, title in (("process", "Print presets"), ("filament", "Filament presets")):
        parts.append(f"\n### {title} ({len(zips[kind])})\n\n")
        parts.append("".join(f"- {n}\n" for n in zips[kind]))
    return "".join(parts)


def render() -> dict[Path, str]:
    """Return the full expected text of every generated page."""
    page = PROFILES.read_text(encoding="utf-8")
    generated = blocks()
    pieces: list[str] = []
    done = 0
    for m in _BLOCK.finditer(page):
        start, name, end = (cast("str", m.group(i)) for i in (1, 2, 3))
        if name not in generated:
            msg = f"{PROFILES.name}: unknown or repeated block <!-- generated: {name} -->"
            raise ValueError(msg)
        pieces += [page[done : m.start()], start, "\n", generated.pop(name), "\n", end]
        done = m.end()
    if generated:
        msg = f"{PROFILES.name} lacks the generated blocks {sorted(generated)}"
        raise ValueError(msg)
    page = "".join([*pieces, page[done:]])
    return {CATALOG: catalog(), PROFILES: page}


def main(argv: list[str]) -> int:
    """Write the pages, or with --check report the stale ones."""
    pages = render()
    stale = [path for path, text in pages.items() if not path.is_file() or path.read_text(encoding="utf-8") != text]
    if "--check" in argv:
        for path in stale:
            print(f"{path.relative_to(ROOT)} is out of date: run src/docs.py", file=sys.stderr)
        return 1 if stale else 0
    for path, text in pages.items():
        _ = path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
