"""Resolver tests on small profile trees built in a temporary folder."""

import json
from pathlib import Path
from typing import cast

import pytest

import resolve
from resolve import ResolveError


def tree(root: Path, vendors: dict[str, dict[str, dict[str, object] | str]]) -> Path:
    """Write vendor indexes and preset files: {vendor: {sub_path: preset dict or raw file text}}."""
    for vendor, files in vendors.items():
        entries: list[dict[str, str]] = []
        for sub_path, content in files.items():
            path = root / vendor / sub_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, str):
                _ = path.write_bytes(content.encode())
                entries.append({"name": sub_path, "sub_path": sub_path})
            else:
                _ = path.write_text(json.dumps(content), encoding="utf-8")
                entries.append({"name": str(content.get("name")), "sub_path": sub_path})
        index = {"name": vendor, "version": "01.00.00.00", "process_list": entries}
        _ = (root / f"{vendor}.json").write_text(json.dumps(index), encoding="utf-8")
    return root


def test_child_overrides_parent(tmp_path: Path) -> None:
    root = tree(
        tmp_path,
        {
            "V": {
                "base.json": {"name": "base", "a": "1", "b": ["2", "2"]},
                "child.json": {"name": "child", "inherits": "base", "a": "9"},
            }
        },
    )
    assert resolve.resolve("child", "V", root) == {"name": "child", "inherits": "base", "a": "9", "b": ["2", "2"]}


def test_file_with_byte_order_mark_loads(tmp_path: Path) -> None:
    root = tree(tmp_path, {"V": {"bom.json": '﻿{"name": "bom", "a": "1"}'}})
    assert resolve.resolve("bom", "V", root)["a"] == "1"


def test_corrupt_file_fails_the_build(tmp_path: Path) -> None:
    root = tree(tmp_path, {"V": {"ok.json": {"name": "ok"}, "broken.json": '{"name": "broken",'}})
    with pytest.raises(ResolveError, match=r"fail to parse:\n  V/broken.json"):
        _ = resolve.resolve("ok", "V", root)


def test_allow_listed_failure_is_skipped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tree(tmp_path, {"V": {"ok.json": {"name": "ok"}, "broken.json": "{"}})
    monkeypatch.setattr(resolve, "PARSE_FAILURES_ALLOWED", frozenset({"V/broken.json"}))
    assert resolve.resolve("ok", "V", root) == {"name": "ok"}


def test_value_that_is_not_a_string_fails(tmp_path: Path) -> None:
    root = tree(tmp_path, {"V": {"odd.json": {"name": "odd", "n": 3}}})
    with pytest.raises(ResolveError, match="neither a string nor a list of strings"):
        _ = resolve.resolve("odd", "V", root)


def test_missing_parent_names_what_was_searched(tmp_path: Path) -> None:
    root = tree(
        tmp_path,
        {
            "V": {"child.json": {"name": "child", "inherits": "gone"}},
            "OrcaFilamentLibrary": {"lib.json": {"name": "lib"}},
        },
    )
    with pytest.raises(ResolveError, match=r"'gone' \(searched V, OrcaFilamentLibrary in "):
        _ = resolve.resolve("child", "V", root)


def test_same_name_in_two_vendors_follows_the_given_vendor(tmp_path: Path) -> None:
    root = tree(
        tmp_path,
        {
            "A": {"common.json": {"name": "common", "x": "a"}},
            "B": {"common.json": {"name": "common", "x": "b"}, "child.json": {"name": "child", "inherits": "common"}},
        },
    )
    assert resolve.resolve("child", "B", root)["x"] == "b"
    assert resolve.resolve("common", "A", root)["x"] == "a"


def test_no_fallback_to_other_vendors(tmp_path: Path) -> None:
    root = tree(tmp_path, {"A": {"only.json": {"name": "only"}}, "B": {"other.json": {"name": "other"}}})
    with pytest.raises(ResolveError, match=r"'only' \(searched B in "):
        _ = resolve.resolve("only", "B", root)


def test_library_fallback_is_reported(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tree(
        tmp_path,
        {"V": {"x.json": {"name": "x"}}, "OrcaFilamentLibrary": {"pla.json": {"name": "Generic PLA", "t": "210"}}},
    )
    assert resolve.resolve("Generic PLA", "V", root)["t"] == "210"
    _ = resolve.resolve("Generic PLA", "V", root)
    assert capsys.readouterr().err.count("taken from OrcaFilamentLibrary") == 1


def test_duplicate_name_in_one_vendor_fails(tmp_path: Path) -> None:
    root = tree(tmp_path, {"V": {"one.json": {"name": "same"}, "two.json": {"name": "same"}}})
    with pytest.raises(ResolveError, match=r"V/two\.json: missing or duplicate name 'same'"):
        _ = resolve.resolve("same", "V", root)


def test_same_file_listed_twice_loads_once(tmp_path: Path) -> None:
    root = tree(tmp_path, {"V": {"one.json": {"name": "one"}}})
    index = cast("dict[str, object]", json.loads((root / "V.json").read_text(encoding="utf-8")))
    index["filament_list"] = index["process_list"]
    _ = (root / "V.json").write_text(json.dumps(index), encoding="utf-8")
    assert resolve.resolve("one", "V", root) == {"name": "one"}


def test_file_outside_the_index_is_not_read(tmp_path: Path) -> None:
    root = tree(tmp_path, {"V": {"listed.json": {"name": "listed"}}})
    _ = (root / "V" / "unlisted.json").write_text('{"name": "unlisted"}', encoding="utf-8")
    with pytest.raises(ResolveError, match="'unlisted'"):
        _ = resolve.resolve("unlisted", "V", root)


def test_library_with_empty_index_loads_files_from_disk(tmp_path: Path) -> None:
    root = tree(tmp_path, {"OrcaFilamentLibrary": {}})
    folder = root / "OrcaFilamentLibrary" / "filament" / "SUNLU"
    folder.mkdir(parents=True)
    _ = (folder / "p.json").write_text('{"name": "SUNLU PLA @base", "t": "215"}', encoding="utf-8")
    assert resolve.resolve("SUNLU PLA @base", "OrcaFilamentLibrary", root)["t"] == "215"


def test_old_name_resolves_through_renamed_from(tmp_path: Path) -> None:
    root = tree(tmp_path, {"V": {"new.json": {"name": "new", "renamed_from": "old;older", "a": "1"}}})
    assert resolve.resolve("older", "V", root)["a"] == "1"


def test_source_prefers_the_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SLICER_PROFILES_QIDI", str(tmp_path))
    assert resolve.source("qidi") == tmp_path
