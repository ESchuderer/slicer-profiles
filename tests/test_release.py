"""Release files: reproducible zips, a manifest that validates and leaks nothing local."""

import json
import time
import zipfile
from pathlib import Path
from typing import cast

import jsonschema
import pytest

import release

EPOCH = 1_793_000_000
COMMIT = "a" * 40


@pytest.fixture
def out(tmp_path: Path) -> Path:
    presets = {
        "orca/process/0.20mm Strong MM-Support @U1 0.4.json": {
            "type": "process",
            "name": "0.20mm Strong MM-Support @U1 0.4",
        },
        "orca/machine/Snapmaker U1 (0.4 nozzle) (LAN).json": {
            "type": "machine",
            "name": "Snapmaker U1 (0.4 nozzle) (LAN)",
        },
        "orca/filament/SUNLU PLA+ 2.0 HQ.json": {"type": "filament", "name": "SUNLU PLA+ 2.0 HQ"},
        "bambu/process/0.12mm Detail @P2S 0.4.json": {"type": "process", "name": "0.12mm Detail @P2S 0.4"},
        "bambu/filament/SUNLU PLA+ 2.0 HQ.json": {"type": "filament", "name": "SUNLU PLA+ 2.0 HQ"},
        "qidi/process/0.24mm Standard @X-Max4 0.6.json": {"type": "process", "name": "0.24mm Standard @X-Max4 0.6"},
        "snapmaker/process/0.12mm Decor @U1 0.4.json": {"type": "process", "name": "0.12mm Decor @U1 0.4"},
    }
    for rel, preset in presets.items():
        path = tmp_path / "out" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(json.dumps(preset, indent=4), encoding="utf-8")
    return tmp_path / "out"


def test_two_builds_are_byte_identical(out: Path, tmp_path: Path) -> None:
    _ = release.build("v0.2.0", COMMIT, EPOCH, out, tmp_path / "a")
    _ = release.build("v0.2.0", COMMIT, EPOCH, out, tmp_path / "b")
    names = sorted(p.name for p in (tmp_path / "a").iterdir())
    assert names == sorted(p.name for p in (tmp_path / "b").iterdir())
    for name in names:
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes(), name


def test_zip_entries_are_normalized(out: Path, tmp_path: Path) -> None:
    _ = release.build("v0.2.0", COMMIT, EPOCH, out, tmp_path / "d")
    with zipfile.ZipFile(tmp_path / "d" / "slicer-profiles-orca-v0.2.0.zip") as z:
        infos = z.infolist()
    assert [i.filename for i in infos] == sorted(i.filename for i in infos)
    assert {i.date_time for i in infos} == {time.gmtime(EPOCH)[:6]}
    assert {i.external_attr >> 16 for i in infos} == {0o100644}


def test_manifest_validates_and_describes_presets(out: Path, tmp_path: Path) -> None:
    manifest = release.build("v0.2.0", COMMIT, EPOCH, out, tmp_path / "d")
    schema = cast("dict[str, object]", json.loads(release.SCHEMA.read_text(encoding="utf-8")))
    jsonschema.validate(manifest, schema)
    presets = {str(p["id"]): p for p in cast("list[release.Entry]", manifest["presets"])}
    strong = presets["orca/process/0.20mm Strong MM-Support @U1 0.4.json"]
    assert (strong["printer"], strong["nozzle"], strong["style"], strong["variant"]) == (
        "U1",
        "0.4",
        "Strong",
        "MM-Support",
    )
    machine = presets["orca-machines/machine/Snapmaker U1 (0.4 nozzle) (LAN).json"]
    assert (machine["printer"], machine["nozzle"], machine["license"]) == ("U1", "0.4", "AGPL-3.0-only")
    assert strong["license"] == "CC-BY-4.0"
    assert presets["bambu/filament/SUNLU PLA+ 2.0 HQ.json"]["printer"] == "P2S"
    decor = presets["snapmaker/process/0.12mm Decor @U1 0.4.json"]
    assert (decor["style"], decor["variant"]) == ("Detail", "Decor")
    assert manifest["printers"] == ["P2S", "U1", "X-Max4"]


def test_manifest_and_sums_hold_no_local_path(out: Path, tmp_path: Path) -> None:
    dist = tmp_path / "d"
    _ = release.build("v0.2.0", COMMIT, EPOCH, out, dist)
    for name in ("manifest.json", "SHA256SUMS"):
        text = (dist / name).read_text(encoding="utf-8")
        assert str(tmp_path) not in text
        assert "192.0.2." not in text
    sums = (dist / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    assert [line.split("  ")[1] for line in sums] == sorted(p.name for p in dist.iterdir() if p.name != "SHA256SUMS")


def test_catalog_check_reports_a_missing_preset(out: Path, tmp_path: Path) -> None:
    manifest = release.build("v0.2.0", COMMIT, EPOCH, out, tmp_path / "d")
    stale = release.catalog_differences(cast("list[release.Entry]", manifest["presets"]))
    assert {line.split(":", 1)[0] for line in stale} == {"orca", "orca-machines", "bambu", "qidi", "snapmaker"}


def test_notice_names_every_zip_and_the_agpl_source(out: Path, tmp_path: Path) -> None:
    _ = release.build("v0.2.0", COMMIT, EPOCH, out, tmp_path / "d")
    text = (tmp_path / "d" / "NOTICE.md").read_text(encoding="utf-8")
    assert "| `slicer-profiles-orca-machines-v0.2.0.zip` | AGPL-3.0-only |" in text
    assert f"https://github.com/ESchuderer/slicer-profiles/tree/{COMMIT}" in text
    assert (tmp_path / "d" / "LICENSE-AGPL-3.0-only.txt").is_file()


def test_build_file_outside_every_zip_stops_the_release(out: Path, tmp_path: Path) -> None:
    _ = (out / "bambu" / "stray.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match=r"build files in no release zip: \['bambu/stray.txt'\]"):
        _ = release.build("v0.2.0", COMMIT, EPOCH, out, tmp_path / "d")
