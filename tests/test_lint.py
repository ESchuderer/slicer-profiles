"""G-code, post_process and address lint on hand-written presets."""

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

import lint

if TYPE_CHECKING:
    from resolve import Preset

ALLOWED = frozenset({"G28", "G1", "M104", "SET_PURIFIER_MODE"})


def test_commands_resolve_template_syntax() -> None:
    gcode = "G28 ; home\n{if a > 1}M104 S[t]{else}G1 X{x}{endif}\n[custom]\n  set_purifier_mode MODE=1"
    assert lint.commands(gcode) == ["G28", "M104", "G1", "SET_PURIFIER_MODE"]


def test_comments_and_inline_values_are_not_commands() -> None:
    gcode = "M104 S200 ; heat {if fast}quick{endif}\nM141 S{if a <= 50}0{else}{t}{endif}\n{custom_gcode}"
    assert lint.commands(gcode) == ["M104", "M141"]


def test_template_value_inside_a_command_word_stays_visible() -> None:
    assert lint.commands("T{initial_tool}\nM50[n] S1") == ["T{}", "M50{}"]


def test_listed_commands_pass() -> None:
    preset: Preset = {"name": "p", "machine_start_gcode": "G28\nM104 S200", "layer_change_gcode": ["G1 Z1"]}
    assert lint.lint_preset("p", preset, ALLOWED, release=False) == []


def test_unlisted_command_fails() -> None:
    preset: Preset = {"name": "p", "machine_end_gcode": "G28\nBED_MESH_CALIBRATE"}
    assert lint.lint_preset("p", preset, ALLOWED, release=False) == [
        "p: machine_end_gcode runs BED_MESH_CALIBRATE, not in gcode-commands.txt"
    ]


@pytest.mark.parametrize("command", ["SAVE_CONFIG", "FIRMWARE_RESTART", "RESTART", "M500", "M504", "SAVE_VARIABLE"])
def test_always_fail_command_fails_even_when_listed(command: str) -> None:
    preset: Preset = {"name": "p", "machine_start_gcode": f"G28\n{command} VARIABLE=x"}
    found = lint.lint_preset("p", preset, ALLOWED | {command}, release=False)
    assert found == [f"p: machine_start_gcode runs {command}, which fails or rewrites printer state"]


def test_post_process_fails() -> None:
    assert lint.lint_preset("p", {"post_process": ["/usr/bin/true"]}, ALLOWED, release=False) == [
        "p: post_process is set"
    ]
    assert lint.lint_preset("p", {"post_process": [""]}, ALLOWED, release=False) == []


def test_address_only_in_lan_presets_and_never_in_releases() -> None:
    lan: Preset = {"name": "U1 (LAN)", "print_host": "10.0.0.5", "print_host_webui": ""}
    other: Preset = {"name": "0.20mm Standard", "printhost_apikey": "x", "printhost_authorization_type": "key"}
    assert lint.lint_preset("lan", lan, ALLOWED, release=False) == []
    assert lint.lint_preset("lan", lan, ALLOWED, release=True) == ["lan: print_host is set in a release preset"]
    assert lint.lint_preset("o", other, ALLOWED, release=False) == [
        "o: printhost_apikey is set in a preset outside (LAN)"
    ]


def test_tree_and_exit_code(tmp_path: Path) -> None:
    (tmp_path / "machine").mkdir()
    _ = (tmp_path / "machine" / "a.json").write_text(json.dumps({"name": "a", "post_process": "x"}), encoding="utf-8")
    assert lint.main([str(tmp_path)]) == 1
    _ = (tmp_path / "machine" / "a.json").write_text(json.dumps({"name": "a"}), encoding="utf-8")
    assert lint.main([str(tmp_path), "--release"]) == 0


def test_committed_allowlist_has_no_always_fail_command() -> None:
    assert not lint.load_allowlist() & lint.ALWAYS_FAIL
