"""The version lock and everything that must agree with it."""

from pathlib import Path

import pytest

import targets

ROOT = Path(__file__).resolve().parent.parent


def test_lock_has_every_target() -> None:
    assert tuple(targets.load()) == targets.NAMES


def test_readme_table_matches_the_lock() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert targets.readme_table(targets.load()) in readme, "README version table differs from upstream.lock.toml"


def test_empty_vendor_table_is_refused(tmp_path: Path) -> None:
    text = targets.LOCK.read_text(encoding="utf-8").replace('vendors = { BBL = "02.09.00.74" }', "vendors = {}")
    lock = tmp_path / "upstream.lock.toml"
    _ = lock.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match=r"\[targets.bambu\] needs exactly"):
        _ = targets.load(lock)


def test_missing_field_is_refused(tmp_path: Path) -> None:
    text = targets.LOCK.read_text(encoding="utf-8").replace('preset_version = "02.09.01.70"\n', "")
    lock = tmp_path / "upstream.lock.toml"
    _ = lock.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match=r"\[targets.bambu\] needs exactly"):
        _ = targets.load(lock)
