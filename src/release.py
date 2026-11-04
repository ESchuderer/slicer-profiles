#!/usr/bin/env python3
"""Build the release files from a generated tree: the preset zip, manifest.json, NOTICE.md and SHA256SUMS.

Usage: release.py VERSION COMMIT EPOCH OUT_DIR DIST_DIR
  VERSION  release tag (vX.Y.Z), COMMIT the commit it is built from, EPOCH that commit's time
  (`git log -1 --format=%ct`), OUT_DIR the build output (out/), DIST_DIR where the files go.
Everything derives from the commit, so two builds of one commit give byte-identical files: zip entries
are sorted, dated EPOCH, mode 0644, and the manifest's time is EPOCH. The manifest holds no address and
no local path.
"""

import hashlib
import json
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, cast

from docs import APP_LICENSE, SLICER, contents
from generate import printer, process_jobs, process_name
from targets import load

if TYPE_CHECKING:
    from resolve import Preset

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "manifest.schema.json"
REPOSITORY = "ESchuderer/slicer-profiles"
FORMAT = "slicer-profiles-release"
type Entry = dict[str, str | int | None]
_PRINTER = printer()
# print preset name -> (nozzle, style, variant), from the generator's own job list
_JOBS = {process_name(_PRINTER, *job): job for job in process_jobs(_PRINTER)}


def sha256(data: bytes) -> str:
    """Return the hex SHA-256 of some bytes."""
    return hashlib.sha256(data).hexdigest()


def write_zip(src: Path, files: list[Path], dst: Path, epoch: int) -> None:
    """Zip FILES (below SRC) with sorted names, one fixed date and mode 0644."""
    stamp = time.gmtime(max(epoch, 315532800))[:6]  # zip dates start in 1980
    with zipfile.ZipFile(dst, "w") as z:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(src).as_posix(), date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            z.writestr(info, path.read_bytes(), compresslevel=9)


def describe(rel: str, data: bytes) -> Entry:
    """Return the manifest entry of one preset file of the zip."""
    preset = cast("Preset", json.loads(data))
    kind, name = str(preset.get("type", "")), str(preset.get("name", ""))
    entry: Entry = {"id": f"{SLICER}/{rel}", "type": kind, "name": name, "slicer": SLICER}
    entry |= {"printer": None, "nozzle": None, "style": None, "variant": None, "filament": None}
    if kind == "process" and (job := _JOBS.get(name)):
        nozzle, style, variant = job
        entry |= {"printer": _PRINTER["tag"], "nozzle": nozzle, "style": style or None, "variant": variant or None}
    elif kind == "filament":
        entry |= {"filament": name, "printer": _PRINTER["tag"]}
    return entry | {"path": rel, "sha256": sha256(data), "license": APP_LICENSE}


def build(version: str, commit: str, epoch: int, out: Path, dist: Path) -> dict[str, object]:
    """Write the preset zip, manifest.json, its schema, NOTICE.md and SHA256SUMS into DIST; return the manifest."""
    dist.mkdir(parents=True, exist_ok=True)
    name = f"slicer-profiles-{SLICER}-{version}.zip"
    src = out / SLICER
    files = sorted(src.rglob("*.json"), key=str)
    write_zip(src, files, dist / name, epoch)
    presets = [describe(p.relative_to(src).as_posix(), p.read_bytes()) for p in files]
    artifacts = [_artifact("presets", name, dist, version)]
    _ = shutil.copyfile(SCHEMA, dist / SCHEMA.name)
    artifacts.append(_artifact("schema", SCHEMA.name, dist, version))
    _ = (dist / "NOTICE.md").write_text(notice(version, commit), encoding="utf-8")
    artifacts.append(_artifact("notice", "NOTICE.md", dist, version))
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


def notice(version: str, commit: str) -> str:
    """Return NOTICE.md: the license of every release file."""
    return f"""# Licenses of slicer-profiles {version}

Built from https://github.com/{REPOSITORY} at commit `{commit}`.

| File | License |
|---|---|
| `slicer-profiles-{SLICER}-{version}.zip` | {APP_LICENSE} |
| `manifest.json`, `manifest.schema.json`, `SHA256SUMS`, this file | CC-BY-4.0 |

CC-BY-4.0 (https://creativecommons.org/licenses/by/4.0/): credit "slicer-profiles by ESchuderer,
https://github.com/{REPOSITORY}". The presets name a stock preset of each slicer as their parent and
hold only the values set by this project; values taken from makers' data sheets are cited facts.
"""


def catalog_differences(presets: list[Entry]) -> list[str]:
    """Return the preset kinds whose names differ from the generated catalog (docs/catalog.md)."""
    expected = contents()
    built = {k: sorted(str(p["name"]) for p in presets if p["type"] == k) for k in expected}
    return [f"{k}: built {built[k]}, catalog {expected[k]}" for k in expected if built[k] != expected[k]]


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
    print(f"{len(cast('list[object]', manifest['presets']))} presets -> {dist}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
