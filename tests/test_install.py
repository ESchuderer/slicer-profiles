"""Install guard: a preset changed in the app stops the next install."""

from pathlib import Path

import pytest

import install


@pytest.fixture
def dirs(tmp_path: Path) -> tuple[Path, Path, Path]:
    src, dest, state = tmp_path / "out" / "orca", tmp_path / "user" / "default", tmp_path / ".installed"
    (src / "filament").mkdir(parents=True)
    _ = (src / "filament" / "PLA.json").write_text('{\n "nozzle_temperature": ["215"]\n}\n', encoding="utf-8")
    state.mkdir()
    return src, dest, state


def test_untouched_install_passes(dirs: tuple[Path, Path, Path]) -> None:
    src, dest, state = dirs
    assert install.install("orca", src, dest, state) == 0
    manifest = install.read_manifest("orca", state)
    assert manifest is not None
    assert manifest["files"] == {"filament/PLA.json": install.sha256(src / "filament" / "PLA.json")}
    assert install.edited("orca", state) == []


def test_edit_in_the_app_is_reported_with_a_diff(dirs: tuple[Path, Path, Path]) -> None:
    src, dest, state = dirs
    _ = install.install("orca", src, dest, state)
    _ = (dest / "filament" / "PLA.json").write_text('{\n "nozzle_temperature": ["220"]\n}\n', encoding="utf-8")
    [report] = install.edited("orca", state)
    assert '- "nozzle_temperature": ["215"]' in report
    assert '+ "nozzle_temperature": ["220"]' in report


def test_check_stops_without_force(
    dirs: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    src, dest, state = dirs
    _ = install.install("orca", src, dest, state)
    _ = (dest / "filament" / "PLA.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(install, "STATE", state)
    assert install.main(["check", "orca"]) == 1
    assert "1 orca presets were changed in the app" in capsys.readouterr().err
    assert install.main(["check", "orca", "--force"]) == 0


def test_deleted_preset_is_not_an_edit(dirs: tuple[Path, Path, Path]) -> None:
    src, dest, state = dirs
    _ = install.install("orca", src, dest, state)
    (dest / "filament" / "PLA.json").unlink()
    assert install.edited("orca", state) == []


def test_reinstall_removes_old_files_and_info_sidecars(dirs: tuple[Path, Path, Path]) -> None:
    src, dest, state = dirs
    _ = install.install("orca", src, dest, state)
    _ = (dest / "filament" / "PLA.info").write_text("sync", encoding="utf-8")
    _ = (src / "filament" / "PLA.json").rename(src / "filament" / "PETG.json")
    _ = install.install("orca", src, dest, state)
    assert sorted(p.name for p in (dest / "filament").iterdir()) == ["PETG.json"]


def test_v010_manifest_compares_with_the_last_build(dirs: tuple[Path, Path, Path]) -> None:
    src, dest, state = dirs
    (dest / "filament").mkdir(parents=True)
    _ = (dest / "filament" / "PLA.json").write_bytes((src / "filament" / "PLA.json").read_bytes())
    _ = (state / "orca.txt").write_text(f"#dest={dest}\nfilament/PLA.json\n", encoding="utf-8")
    assert install.edited("orca", state, src.parent) == []
    _ = (dest / "filament" / "PLA.json").write_text("{}", encoding="utf-8")
    assert len(install.edited("orca", state, src.parent)) == 1
    assert install.install("orca", src, dest, state) == 0
    assert not (state / "orca.txt").exists()


def test_account_folder_warns_about_cloud_sync(
    dirs: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    src, _, state = dirs
    _ = install.install("orca", src, src.parent.parent / "user" / "123456", state)
    assert "may sync these presets to the vendor's cloud" in capsys.readouterr().err


def test_v010_manifest_without_folder_removes_from_the_new_folder(dirs: tuple[Path, Path, Path]) -> None:
    src, dest, state = dirs
    (dest / "filament").mkdir(parents=True)
    _ = (dest / "filament" / "Old.json").write_text("{}", encoding="utf-8")
    _ = (state / "orca.txt").write_text("filament/Old.json\n", encoding="utf-8")
    assert install.edited("orca", state) == []
    _ = install.install("orca", src, dest, state)
    assert sorted(p.name for p in (dest / "filament").iterdir()) == ["PLA.json"]
