"""Unit tests for the printer-fix helpers that need no stock profiles."""

import pytest

from gen_machine import replace_once, tools


def test_replace_once_replaces_the_expected_count() -> None:
    assert replace_once("a\nG28 X Y\nb", "G28 X Y", "G28") == "a\nG28\nb"
    assert replace_once("M141 S1 M141 S1", "M141 S1", "M141 S0", count=2) == "M141 S0 M141 S0"


def test_replace_once_stops_when_the_stock_gcode_changed() -> None:
    with pytest.raises(SystemExit, match="expected 1 x 'G28 X Y'"):
        _ = replace_once("G28\n", "G28 X Y", "G28")
    with pytest.raises(SystemExit, match="found 2"):
        _ = replace_once("G28 X Y G28 X Y", "G28 X Y", "G28")


def test_tools_writes_one_string_per_u1_toolhead() -> None:
    assert tools(1.5) == ["1.5", "1.5", "1.5", "1.5"]
