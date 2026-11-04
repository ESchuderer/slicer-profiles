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

from docs import ZIPS, Zip, contents
from gen_process import jobs, preset_name
from targets import load

if TYPE_CHECKING:
    from resolve import Preset

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "manifest.schema.json"
AGPL_TEXT = ROOT / "release" / "LICENSE-AGPL-3.0-only.txt"
REPOSITORY = "ESchuderer/slicer-profiles"
FORMAT = "slicer-profiles-release"
PRINTERS = {"Bambu Lab P2S": "P2S", "Snapmaker U1": "U1", "Qidi X-Max 4": "X-Max4", "X-Max 4": "X-Max4"}
TARGET_PRINTER = {"bambu": "P2S", "qidi": "X-Max4", "snapmaker": "U1"}
_NOZZLE = re.compile(r"(\d\.\d) nozzle")
type Entry = dict[str, str | int | None]
# print preset name -> (printer tag, nozzle, style, variant suffix), from the generator's own job list
_JOBS = {preset_name(t, n, s, x): (t, n, s, x) for t, n, s, x, _ in jobs()}


def sha256(data: bytes) -> str:
    """Return the hex SHA-256 of some bytes."""
    return hashlib.sha256(data).hexdigest()


def zip_files(src: Path, folders: tuple[str, ...]) -> list[Path]:
    """Return the files of FOLDERS below SRC, sorted by their path in the zip."""
    return sorted((p for f in folders if (src / f).is_dir() for p in (src / f).rglob("*") if p.is_file()), key=str)


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


def describe(stem: str, z: Zip, rel: str, data: bytes) -> Entry:
    """Return the manifest entry of one preset file of a zip."""
    preset = cast("Preset", json.loads(data))
    kind, name = str(preset.get("type", "")), str(preset.get("name", ""))
    slicer = z.source
    entry: Entry = {"id": f"{stem}/{rel}", "type": kind, "name": name, "slicer": slicer, "zip": stem}
    entry |= {"printer": None, "nozzle": None, "style": None, "variant": None, "filament": None}
    if kind == "process" and (job := _JOBS.get(name)):
        tag, nozzle, style, suffix = job
        entry |= {"printer": tag, "nozzle": nozzle, "style": style, "variant": suffix or None}
    elif kind == "machine":
        entry["printer"] = next((tag for prefix, tag in PRINTERS.items() if name.startswith(prefix)), None)
        entry["nozzle"] = m[1] if (m := _NOZZLE.search(name)) else None
    elif kind == "filament":
        entry |= {"filament": name, "printer": TARGET_PRINTER.get(slicer)}
    return entry | {"path": rel, "sha256": sha256(data), "license": z.license}


def build(version: str, commit: str, epoch: int, out: Path, dist: Path) -> dict[str, object]:
    """Write the zips, manifest.json, its schema and SHA256SUMS into DIST; return the manifest."""
    dist.mkdir(parents=True, exist_ok=True)
    presets: list[Entry] = []
    artifacts: list[Entry] = []
    for stem, z in ZIPS.items():
        name = f"slicer-profiles-{stem}-{version}.zip"
        src = out / z.source
        files = zip_files(src, z.folders)
        write_zip(src, files, dist / name, epoch)
        presets += [describe(stem, z, p.relative_to(src).as_posix(), p.read_bytes()) for p in files]
        artifacts.append(_artifact("presets", name, dist, version))
    _ = shutil.copyfile(SCHEMA, dist / SCHEMA.name)
    artifacts.append(_artifact("schema", SCHEMA.name, dist, version))
    _ = shutil.copyfile(AGPL_TEXT, dist / AGPL_TEXT.name)
    artifacts.append(_artifact("license", AGPL_TEXT.name, dist, version))
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
    """Return NOTICE.md: the license of every release file and, for the AGPL zip, its source."""
    orca = load()["orca"]
    rows = "".join(f"| `slicer-profiles-{stem}-{version}.zip` | {z.license} |\n" for stem, z in ZIPS.items())
    agpl = next(stem for stem, z in ZIPS.items() if z.license == "AGPL-3.0-only")
    return f"""# Licenses of slicer-profiles {version}

Built from https://github.com/{REPOSITORY} at commit `{commit}`.

| File | License |
|---|---|
{rows}| `manifest.json`, `manifest.schema.json`, this file | CC-BY-4.0 |

CC-BY-4.0 (https://creativecommons.org/licenses/by/4.0/): credit "slicer-profiles by ESchuderer,
https://github.com/{REPOSITORY}". The presets name a stock preset of each slicer as their parent and
hold only the values set by this project; values taken from makers' data sheets are cited facts.

AGPL-3.0-only (`slicer-profiles-{agpl}-{version}.zip`): the "(LAN)" printer presets for the Snapmaker U1
and the Qidi X-Max 4 hold start G-code copied from OrcaSlicer's stock profiles and changed by this
project ({version}). OrcaSlicer licenses them under the GNU Affero General Public License version 3;
the text is `{AGPL_TEXT.name}` beside this file. Source: the JSON presets are their own source form;
the generator that writes them is https://github.com/{REPOSITORY}/tree/{commit} (`src/gen_machine.py`,
changes described in `docs/profiles.md`), and the stock profiles it starts from are
https://github.com/{orca["repository"]}/tree/{orca["commit"]}/resources/profiles ({orca["tag"]}).
"""


def catalog_differences(presets: list[Entry]) -> list[str]:
    """Return the zips whose preset names differ from the generated catalog (docs/catalog.md)."""
    found: list[str] = []
    for slicer, expected in contents().items():
        built = {k: sorted(str(p["name"]) for p in presets if p["zip"] == slicer and p["type"] == k) for k in expected}
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
    print(f"{len(cast('list[object]', manifest['presets']))} presets in {len(ZIPS)} zips -> {dist}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
