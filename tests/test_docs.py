"""Docs drift test: the generated pages match the tables they come from."""

from pathlib import Path

import pytest

import docs


def test_generated_pages_are_up_to_date() -> None:
    assert docs.main(["--check"]) == 0, "run `uv run python src/docs.py` and commit the pages"


def test_zip_counts_follow_the_tables() -> None:
    assert {kind: len(names) for kind, names in docs.contents().items()} == {"process": 12, "filament": 17}


def test_unknown_block_is_named(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    page = tmp_path / "profiles.md"
    _ = page.write_text("<!-- generated: style -->\n<!-- end generated -->\n", encoding="utf-8")
    monkeypatch.setattr(docs, "PROFILES", page)
    with pytest.raises(ValueError, match="unknown or repeated block <!-- generated: style -->"):
        _ = docs.render()
