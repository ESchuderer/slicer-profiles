"""Docs drift test: the generated pages match the tables they come from."""

import docs


def test_generated_pages_are_up_to_date() -> None:
    assert docs.main(["--check"]) == 0, "run `uv run python src/docs.py` and commit the pages"


def test_zip_counts_follow_the_tables() -> None:
    counts = {slicer: {kind: len(names) for kind, names in c.items()} for slicer, c in docs.contents().items()}
    assert counts == {
        "orca": {"process": 61, "filament": 9, "machine": 6},
        "bambu": {"process": 20, "filament": 9, "machine": 0},
        "qidi": {"process": 20, "filament": 9, "machine": 0},
        "snapmaker": {"process": 21, "filament": 9, "machine": 3},
    }
