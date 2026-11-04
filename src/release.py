#!/usr/bin/env python3
"""Build the release files from a generated tree: one zip per slicer, manifest.json and SHA256SUMS.

Usage: release.py VERSION COMMIT EPOCH OUT_DIR DIST_DIR
  VERSION  release tag (vX.Y.Z), COMMIT the commit it is built from, EPOCH that commit's time
  (`git log -1 --format=%ct`), OUT_DIR the build output (out/), DIST_DIR where the files go.
Everything derives from the commit, so two builds of one commit give byte-identical files: zip entries
are sorted, dated EPOCH, mode 0644, and the manifest's time is EPOCH. The manifest holds no address and
no local path.
"""

import hashlib
import json
import re
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, cast

from docs import contents
from gen_process import jobs, preset_name
from targets import load

if TYPE_CHECKING:
    from resolve import Preset

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "manifest.schema.json"
REPOSITORY = "ESchuderer/slicer-profiles"
FORMAT = "slicer-profiles-release"
SLICERS = ("orca", "bambu", "qidi", "snapmaker")
PRINTERS = {"Bambu Lab P2S": "P2S", "Snapmaker U1": "U1", "Qidi X-Max 4": "X-Max4", "X-Max 4": "X-Max4"}
TARGET_PRINTER = {"bambu": "P2S", "qidi": "X-Max4", "snapmaker": "U1"}
_NOZZLE = re.compile(r"(\d\.\d) nozzle")
type Entry = dict[str, str | int | None]
# print preset name -> (printer tag, nozzle, style, variant suffix), from the generator's own job list
_JOBS = {preset_name(t, n, s, x): (t, n, s, x) for t, n, s, x, _ in jobs()}


def sha256(data: bytes) -> str:
    """Return the hex SHA-256 of some bytes."""
    return hashlib.sha256(data).hexdigest()


def license_of(_slicer: str, _rel: str) -> str:
    """Return the SPDX license of a generated preset in the release."""
    return "MIT"


def write_zip(src: Path, dst: Path, epoch: int) -> None:
    """Zip every file below SRC with sorted names, one fixed date and mode 0644."""
    stamp = time.gmtime(max(epoch, 315532800))[:6]  # zip dates start in 1980
    with zipfile.ZipFile(dst, "w") as z:
        for path in sorted(p for p in src.rglob("*") if p.is_file()):
            info = zipfile.ZipInfo(path.relative_to(src).as_posix(), date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            z.writestr(info, path.read_bytes(), compresslevel=9)


def describe(slicer: str, rel: str, data: bytes) -> Entry:
    """Return the manifest entry of one preset file of a slicer's zip."""
    preset = cast("Preset", json.loads(data))
    kind, name = str(preset.get("type", "")), str(preset.get("name", ""))
    entry: Entry = {"id": f"{slicer}/{rel}", "type": kind, "name": name, "slicer": slicer}
    entry |= {"printer": None, "nozzle": None, "style": None, "variant": None, "filament": None}
    if kind == "process" and (job := _JOBS.get(name)):
        tag, nozzle, style, suffix = job
        entry |= {"printer": tag, "nozzle": nozzle, "style": style, "variant": suffix or None}
    elif kind == "machine":
        entry["printer"] = next((tag for prefix, tag in PRINTERS.items() if name.startswith(prefix)), None)
        entry["nozzle"] = m[1] if (m := _NOZZLE.search(name)) else None
    elif kind == "filament":
        entry |= {"filament": name, "printer": TARGET_PRINTER.get(slicer)}
    return entry | {"path": rel, "sha256": sha256(data), "license": license_of(slicer, rel)}


def build(version: str, commit: str, epoch: int, out: Path, dist: Path) -> dict[str, object]:
    """Write the zips, manifest.json, its schema and SHA256SUMS into DIST; return the manifest."""
    dist.mkdir(parents=True, exist_ok=True)
    presets: list[Entry] = []
    artifacts: list[Entry] = []
    for slicer in SLICERS:
        name = f"slicer-profiles-{slicer}-{version}.zip"
        write_zip(out / slicer, dist / name, epoch)
        presets += [
            describe(slicer, p.relative_to(out / slicer).as_posix(), p.read_bytes())
            for p in sorted((out / slicer).rglob("*.json"))
        ]
        artifacts.append(_artifact("presets", name, dist, version))
    _ = shutil.copyfile(SCHEMA, dist / SCHEMA.name)
    artifacts.append(_artifact("schema", SCHEMA.name, dist, version))
    manifest: dict[str, object] = {
        "format": FORMAT,
        "schema_version": 1,
        "version": version,
        "commit": commit,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch)),
        "slicers": [{"target": k, **v} for k, v in load().items()],
        "printers": sorted({str(p["printer"]) for p in presets if p["printer"]}),
        "artifacts": artifacts,
        "presets": presets,
    }
    _ = (dist / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    files = sorted(p for p in dist.iterdir() if p.name != "SHA256SUMS")
    sums = "".join(f"{sha256(p.read_bytes())}  {p.name}\n" for p in files)
    _ = (dist / "SHA256SUMS").write_text(sums, encoding="utf-8")
    return manifest


def _artifact(kind: str, name: str, dist: Path, version: str) -> Entry:
    data = (dist / name).read_bytes()
    url = f"https://github.com/{REPOSITORY}/releases/download/{version}/{name}"
    return {"kind": kind, "name": name, "url": url, "sha256": sha256(data), "size": len(data)}


def catalog_differences(presets: list[Entry]) -> list[str]:
    """Return the zips whose preset names differ from the generated catalog (docs/catalog.md)."""
    found: list[str] = []
    for slicer, expected in contents().items():
        built = {
            k: sorted(str(p["name"]) for p in presets if p["slicer"] == slicer and p["type"] == k) for k in expected
        }
        if built != expected:
            found.append(f"{slicer}: built {built}, catalog {expected}")
    return found


def main(argv: list[str]) -> int:
    """Build the release files."""
    if len(argv) != 5 or not argv[2].isdigit():  # noqa: PLR2004 (VERSION COMMIT EPOCH OUT DIST)
        print(__doc__, file=sys.stderr)
        return 64
    version, commit, epoch, out, dist = argv
    manifest = build(version, commit, int(epoch), Path(out), Path(dist))
    if stale := catalog_differences(cast("list[Entry]", manifest["presets"])):
        print("docs/catalog.md does not match the build:\n  " + "\n  ".join(stale), file=sys.stderr)
        return 1
    print(f"{len(cast('list[object]', manifest['presets']))} presets in {len(SLICERS)} zips -> {dist}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
