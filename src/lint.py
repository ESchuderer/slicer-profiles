#!/usr/bin/env python3
"""Refuse generated presets that run G-code, post-process, or carry a printer address.

Usage: lint.py OUT_DIR
The H3C presets set no G-code and no printer, so any `*_gcode` key, a non-empty `post_process` or an address
or credential key (`print_host*`, `printhost_*`) in a generated file fails the build (exit 1). Orca-family
slicers run G-code and post-processing scripts from a preset without asking.
"""

import json
import sys
from pathlib import Path
from typing import cast

from resolve import Preset

HOST_PREFIXES = ("print_host", "printhost_")


def findings(name: str, preset: Preset) -> list[str]:
    """Return one finding per forbidden key of one generated preset."""
    found: list[str] = []
    for key, value in preset.items():
        texts = value if isinstance(value, list) else [value]
        post_process = key == "post_process" and any(t.strip() for t in texts)
        if key.endswith("_gcode") or key.startswith(HOST_PREFIXES) or post_process:
            found.append(f"{name}: {key} is set")
    return found


def main(argv: list[str]) -> int:
    """Print the findings for every preset below OUT_DIR; exit 1 when there are any."""
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 64
    out = Path(argv[0])
    found = [
        f
        for path in sorted(out.rglob("*.json"))
        for f in findings(path.relative_to(out).as_posix(), cast("Preset", json.loads(path.read_text("utf-8"))))
    ]
    for line in found:
        print(f"lint: {line}", file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
