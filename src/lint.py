#!/usr/bin/env python3
"""Lint generated presets: G-code commands, post-processing scripts and printer addresses.

Usage: lint.py OUT_DIR [--release]
Fails (exit 1) on
  - a G-code command that is not in config/gcode-commands.txt (review the stock change, then add it),
  - a command that always fails or rewrites printer state (SAVE_CONFIG, FIRMWARE_RESTART, RESTART,
    M500 to M504, SAVE_VARIABLE), even when listed,
  - any non-empty post_process (Orca-family apps run it without asking),
  - a printer address or credential key outside "(LAN)" presets, and with --release in any preset.
Only the keys a generated preset writes are checked; inherited stock values are the vendor's.
"""

import json
import re
import sys
from pathlib import Path
from typing import cast

from resolve import Preset, Value

ALLOWLIST = Path(__file__).resolve().parent.parent / "config" / "gcode-commands.txt"
ALWAYS_FAIL = frozenset({"SAVE_CONFIG", "FIRMWARE_RESTART", "RESTART", "SAVE_VARIABLE"}) | {
    f"M{n}" for n in range(500, 505)
}
HOST_PREFIXES = ("print_host", "printhost_")
_CONTROL = re.compile(r"\{\s*(?:(?:if|elsif)\b[^{}]*|else\s*|endif\s*)\}")
_PLACEHOLDER = re.compile(r"\{[^{}]*\}|\[[^\[\]]*\]")


def _texts(value: Value) -> list[str]:
    return value if isinstance(value, list) else [value]


def commands(gcode: str) -> list[str]:
    """Return the command word of every G-code line, with the slicer's template syntax resolved away.

    `{if}`, `{elsif}`, `{else}` and `{endif}` end a line; `{expression}` and `[variable]` count as values.
    """
    text = _PLACEHOLDER.sub("0", _CONTROL.sub("\n", gcode))
    out: list[str] = []
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        if line.strip("0 "):
            out.append(line.split()[0].upper())
    return out


def lint_preset(name: str, preset: Preset, allowed: frozenset[str], *, release: bool) -> list[str]:
    """Return one finding per problem in one generated preset."""
    found: list[str] = []
    lan = str(preset.get("name", "")).endswith("(LAN)")
    for key, value in preset.items():
        if key.endswith("_gcode"):
            for command in sorted({c for t in _texts(value) for c in commands(t)}):
                if command in ALWAYS_FAIL:
                    found.append(f"{name}: {key} runs {command}, which fails or rewrites printer state")
                elif command not in allowed:
                    found.append(f"{name}: {key} runs {command}, not in {ALLOWLIST.name}")
        elif key == "post_process" and any(t.strip() for t in _texts(value)):
            found.append(f"{name}: post_process is set")
        elif key.startswith(HOST_PREFIXES) and any(t.strip() for t in _texts(value)) and (release or not lan):
            where = "a release preset" if release else "a preset outside (LAN)"
            found.append(f"{name}: {key} is set in {where}")
    return found


def load_allowlist(path: Path = ALLOWLIST) -> frozenset[str]:
    """Read the reviewed command words, one per line, `#` starts a comment."""
    lines = (line.split("#", 1)[0].strip() for line in path.read_text(encoding="utf-8").splitlines())
    return frozenset(line.upper() for line in lines if line)


def lint_tree(out: Path, *, release: bool) -> list[str]:
    """Lint every preset file below OUT_DIR."""
    allowed = load_allowlist()
    found: list[str] = []
    for path in sorted(out.rglob("*.json")):
        preset = cast("Preset", json.loads(path.read_text(encoding="utf-8")))
        found += lint_preset(path.relative_to(out).as_posix(), preset, allowed, release=release)
    return found


def main(argv: list[str]) -> int:
    """Print findings; exit 1 when there are any."""
    release = "--release" in argv
    paths = [a for a in argv if a != "--release"]
    if len(paths) != 1:
        print(__doc__, file=sys.stderr)
        return 64
    found = lint_tree(Path(paths[0]), release=release)
    for line in found:
        print(f"lint: {line}", file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
