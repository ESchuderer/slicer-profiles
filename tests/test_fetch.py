"""Fetch verification against the lock, on a small local git repository."""

import subprocess
from pathlib import Path

import pytest

import fetch
from targets import Target


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()  # noqa: S603, S607


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    profiles = tmp_path / "resources" / "profiles"
    profiles.mkdir(parents=True)
    _ = (profiles / "V.json").write_text('{"name": "V", "version": "01.02.03.04"}', encoding="utf-8")
    _ = git("init", "-q", cwd=tmp_path)
    _ = git("add", ".", cwd=tmp_path)
    _ = git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "t", cwd=tmp_path)
    return tmp_path


def lock_entry(checkout: Path, **change: str) -> Target:
    entry = Target(
        app="A",
        version="1",
        preset_version="1",
        repository="o/r",
        tag="v1",
        commit=git("rev-parse", "HEAD", cwd=checkout),
        tree=git("rev-parse", "HEAD:resources/profiles", cwd=checkout),
        vendors={"V": "01.02.03.04"},
    )
    return entry | change  # pyright: ignore[reportReturnType]


def test_matching_checkout_has_no_problems(checkout: Path) -> None:
    assert fetch.problems(lock_entry(checkout), checkout) == []


def test_moved_tag_or_changed_tree_is_reported(checkout: Path) -> None:
    found = fetch.problems(lock_entry(checkout, commit="0" * 40, tree="1" * 40), checkout)
    assert [f.split()[0] for f in found] == ["commit", "tree"]


def test_vendor_index_version_is_checked(checkout: Path) -> None:
    entry = lock_entry(checkout)
    entry["vendors"] = {"V": "09.09.09.09"}
    assert fetch.problems(entry, checkout) == ["V.json version 01.02.03.04, lock 09.09.09.09"]
