#!/usr/bin/env python3
"""Resolve stock preset inheritance in a slicer's profile tree.

Usage: resolve.py VENDOR "PRESET NAME" [key ...]   (Bambu Studio's stock profiles)
  e.g. resolve.py BBL "0.20mm Standard @BBL H3C" outer_wall_speed wall_loops
       resolve.py BBL "Generic PLA @BBL H3C" nozzle_temperature
Prints the fully resolved value of each key (all keys if none given).

The resolver reads what the slicer reads: the presets each vendor index (`<vendor>.json`) lists, UTF-8 with
or without a byte order mark. A file that fails to parse, a duplicate name or an inheritance cycle stops the
build; a name is looked up in the given vendor only. Old names listed in a preset's `renamed_from` resolve to
that preset.
"""

import json
import os
import sys
from pathlib import Path
from typing import cast

type Value = str | list[str]
type Preset = dict[str, Value]

# Profile folders of the installed slicers (the owner's machine). SLICER_PROFILES_<TARGET> overrides each,
# for example with a stock profile tree checked out at the slicer's release tag.
INSTALLED = {"bambu": "/opt/bambustudio-bin/resources/profiles"}
INDEX_LISTS = ("machine_model_list", "process_list", "filament_list", "machine_list")


class ResolveError(Exception):
    """A preset cannot be resolved, or the profile tree cannot be read as the slicer reads it."""


class _Vendor:
    """The presets one vendor index lists, by name and by former name."""

    def __init__(self, root: Path, vendor: str) -> None:
        self.presets: dict[str, Preset] = {}
        self.seen: set[str] = set()
        self.renamed: dict[str, str] = {}
        self.failures: list[str] = []
        index = _load(root / f"{vendor}.json")
        for list_name in INDEX_LISTS:
            entries = index.get(list_name, [])
            if not isinstance(entries, list):
                msg = f"{vendor}.json: {list_name} is not a list"
                raise ResolveError(msg)
            for entry in cast("list[object]", entries):
                self._add(root, vendor, entry)

    def _add(self, root: Path, vendor: str, entry: object) -> None:
        sub_path = cast("dict[object, object]", entry).get("sub_path") if isinstance(entry, dict) else None
        if not isinstance(sub_path, str):
            self.failures.append(f"{vendor}.json: index entry without sub_path: {entry!r}")
            return
        rel = f"{vendor}/{sub_path}"
        if rel in self.seen:
            return  # the same file listed twice (Snapmaker's index does this), harmless
        self.seen.add(rel)
        try:
            preset = _preset(_load(root / rel))
        except (OSError, ValueError) as e:
            self.failures.append(f"{rel}: {e}")
            return
        name = preset.get("name")
        if not isinstance(name, str) or name in self.presets:
            self.failures.append(f"{rel}: missing or duplicate name {name!r}")
            return
        self.presets[name] = preset
        old = preset.get("renamed_from", "")
        for old_name in old.split(";") if isinstance(old, str) else old:
            if old_name:
                self.renamed[old_name] = name

    def get(self, name: str) -> Preset | None:
        exact = self.presets.get(name)
        return exact if exact is not None else self.presets.get(self.renamed.get(name, ""))


def _load(path: Path) -> dict[str, object]:
    data = cast("object", json.loads(path.read_text(encoding="utf-8-sig")))
    if not isinstance(data, dict):
        msg = "not a JSON object"
        raise ValueError(msg)  # noqa: TRY004 (a parse failure, collected like the JSON errors)
    return cast("dict[str, object]", data)


def _preset(data: dict[str, object]) -> Preset:
    preset: Preset = {}
    for key, value in data.items():
        items = cast("list[object]", value) if isinstance(value, list) else None
        if isinstance(value, str):
            preset[key] = value
        elif items is not None and all(isinstance(x, str) for x in items):
            preset[key] = [str(x) for x in items]
        else:
            msg = f"key {key!r} is neither a string nor a list of strings"
            raise ValueError(msg)
    return preset


_vendors: dict[tuple[Path, str], _Vendor] = {}


def _vendor(root: Path, vendor: str) -> _Vendor:
    key = (root, vendor)
    if key not in _vendors:
        if not (root / f"{vendor}.json").is_file():
            msg = f"no vendor index {vendor}.json in {root}"
            raise ResolveError(msg)
        v = _Vendor(root, vendor)
        if v.failures:
            raise ResolveError("profile files that fail to parse:\n  " + "\n  ".join(v.failures))
        _vendors[key] = v
    return _vendors[key]


def _find(name: str, vendor: str, root: Path) -> tuple[str, Preset]:
    if (preset := _vendor(root, vendor).get(name)) is not None:
        return vendor, preset
    msg = f"stock preset not found: {name!r} (searched {vendor} in {root})"
    raise ResolveError(msg)


def source(target: str) -> Path:
    """Stock profile folder of a target slicer: SLICER_PROFILES_<TARGET>, else the installed app."""
    override = os.environ.get(f"SLICER_PROFILES_{target.upper()}")
    if override:
        return Path(override)
    return Path(INSTALLED[target])


def resolve(name: str, vendor: str, root: Path | str | None = None) -> Preset:
    """Fully resolved settings of a stock preset: parents first, each child overriding."""
    base = Path(root) if root is not None else source("bambu")
    chain: list[Preset] = []
    seen: list[str] = []
    while True:
        vendor, preset = _find(name, vendor, base)
        seen.append(name)
        chain.append(preset)
        parent = preset.get("inherits")
        if not isinstance(parent, str) or not parent:
            break
        if parent in seen:
            msg = f"inheritance cycle: {' -> '.join([*seen, parent])}"
            raise ResolveError(msg)
        name = parent
    out: Preset = {}
    for preset in reversed(chain):
        out.update(preset)
    return out


def main(argv: list[str]) -> int:
    """Print resolved values of one stock preset."""
    target = "bambu"
    if len(argv) < 2:  # noqa: PLR2004 (VENDOR and NAME)
        print(__doc__, file=sys.stderr)
        return 64
    settings = resolve(argv[1], argv[0], source(target))
    for k in " ".join(argv[2:]).split() or sorted(settings):
        print(k, "=", settings.get(k))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
