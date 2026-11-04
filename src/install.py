#!/usr/bin/env python3
"""Install generated presets into a slicer's user folder without losing changes made in the app.

Usage: install.py check APP [--force]          before a build: stop if an installed preset was edited
       install.py install APP SRC_DIR DEST_DIR  after the build: replace the last install with SRC_DIR

The manifest .installed/APP.json lists every installed file with its SHA-256, and .installed/APP/ keeps
a copy of what was installed. `check` compares the files in the slicer folder with it and prints a diff
for each one that changed since (a value saved in the app), then stops unless --force is given.
v0.1.0 manifests (.installed/APP.txt, no checksums) are compared with the last build in out/APP instead,
which is why `check` runs before the build removes out/.
"""

import difflib
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import TypedDict, cast

STATE = Path(__file__).resolve().parent.parent / ".installed"
LAST_BUILD = Path(__file__).resolve().parent.parent / "out"


class Manifest(TypedDict):
    """What one install wrote: the folder and a SHA-256 per file relative to it."""

    format: str
    schema_version: int
    dest: str
    files: dict[str, str]


def sha256(path: Path) -> str:
    """Return the hex SHA-256 of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_manifest(app: str, state: Path = STATE) -> Manifest | None:
    """Return the last install of APP, also from a v0.1.0 text manifest (files without checksums)."""
    path = state / f"{app}.json"
    if path.is_file():
        return cast("Manifest", json.loads(path.read_text(encoding="utf-8")))
    legacy = state / f"{app}.txt"
    if not legacy.is_file():
        return None
    lines = legacy.read_text(encoding="utf-8").splitlines()
    dest = next((line.removeprefix("#dest=") for line in lines if line.startswith("#dest=")), "")
    files = {line: "" for line in lines if line and not line.startswith("#")}
    return Manifest(format="slicer-profiles-install", schema_version=1, dest=dest, files=files)


def _diff(before: str, after: str, rel: str) -> str:
    lines = difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True), f"installed/{rel}", f"in the app/{rel}"
    )
    return "".join(lines)


def edited(app: str, state: Path = STATE, last_build: Path = LAST_BUILD) -> list[str]:
    """Return a report per installed preset that differs from what was installed (deleted files are fine)."""
    manifest = read_manifest(app, state)
    if manifest is None:
        return []
    dest = Path(manifest["dest"])
    found: list[str] = []
    for rel, digest in sorted(manifest["files"].items()):
        current = dest / rel
        if not current.is_file():
            continue
        copy = state / app / rel if digest else last_build / app / rel
        if digest and sha256(current) == digest:
            continue
        if not copy.is_file():
            found.append(f"{current}: no copy of the installed version to compare with")
        elif copy.read_bytes() != current.read_bytes():
            text = current.read_text(encoding="utf-8")
            found.append(f"{current}:\n{_diff(copy.read_text(encoding='utf-8'), text, rel)}")
    return found


def install(app: str, src: Path, dest: Path, state: Path = STATE) -> int:
    """Remove the files of the last install (and the apps' .info sidecars), copy SRC, write the manifest."""
    old = read_manifest(app, state)
    if old is not None:
        for rel in old["files"]:
            for path in (Path(old["dest"]) / rel, (Path(old["dest"]) / rel).with_suffix(".info")):
                path.unlink(missing_ok=True)
    shutil.rmtree(state / app, ignore_errors=True)
    files: dict[str, str] = {}
    for path in sorted(src.rglob("*.json")):
        rel = path.relative_to(src).as_posix()
        for target in (dest / rel, state / app / rel):
            target.parent.mkdir(parents=True, exist_ok=True)
            _ = shutil.copyfile(path, target)
        files[rel] = sha256(path)
    manifest = Manifest(format="slicer-profiles-install", schema_version=1, dest=str(dest), files=files)
    _ = (state / f"{app}.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (state / f"{app}.txt").unlink(missing_ok=True)
    if dest.name != "default":
        note = "the app may sync these presets to the vendor's cloud"
        print(f"warning: {dest} is the folder of a logged-in account; {note}", file=sys.stderr)
    print(f"Installed {len(files)} presets into {dest}")
    return 0


def main(argv: list[str]) -> int:
    """Run `check` or `install`."""
    if len(argv) >= 2 and argv[0] == "check":  # noqa: PLR2004 (check APP)
        found = edited(argv[1], STATE, LAST_BUILD)
        if not found:
            return 0
        print(f"{len(found)} {argv[1]} presets were changed in the app since the last install:", file=sys.stderr)
        print("\n".join(found), file=sys.stderr)
        if "--force" in argv:
            print("--force: overwriting them.", file=sys.stderr)
            return 0
        print(
            "Move the changes into config/ or src/, or run scripts/build.sh --force to overwrite them.",
            file=sys.stderr,
        )
        return 1
    if len(argv) == 4 and argv[0] == "install":  # noqa: PLR2004 (install APP SRC DEST)
        STATE.mkdir(exist_ok=True)
        return install(argv[1], Path(argv[2]), Path(argv[3]))
    print(__doc__, file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
