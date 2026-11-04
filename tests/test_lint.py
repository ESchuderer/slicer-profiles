"""The preset lint refuses G-code, post-processing and printer addresses."""

import json
from pathlib import Path

import pytest

import lint


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("machine_start_gcode", "G28"),
        ("filament_start_gcode", [""]),
        ("post_process", ["/usr/bin/true"]),
        ("print_host", ""),
        ("printhost_apikey", "x"),
    ],
)
def test_forbidden_key_is_reported(key: str, value: str | list[str]) -> None:
    assert lint.findings("p", {"name": "p", key: value}) == [f"p: {key} is set"]


def test_ordinary_keys_and_empty_post_process_pass() -> None:
    assert lint.findings("p", {"name": "p", "wall_loops": "5", "post_process": [""]}) == []


def test_tree_and_exit_code(tmp_path: Path) -> None:
    (tmp_path / "process").mkdir()
    path = tmp_path / "process" / "a.json"
    _ = path.write_text(json.dumps({"name": "a", "layer_change_gcode": "G1"}), encoding="utf-8")
    assert lint.main([str(tmp_path)]) == 1
    _ = path.write_text(json.dumps({"name": "a"}), encoding="utf-8")
    assert lint.main([str(tmp_path)]) == 0
