"""H3C generator rules that need no stock profiles."""

from typing import TYPE_CHECKING

import pytest

import generate

if TYPE_CHECKING:
    from resolve import Preset

PRINTER = generate.Printer(
    printer="Bambu Lab H3C",
    tag="H3C",
    nozzles=["0.2", "0.4", "0.6"],
    processes={"0.2": "0.10mm Standard @BBL H3C 0.2 nozzle", "0.4": "0.20mm Standard @BBL H3C"},
    materials={"PLA": {"0.2": "Generic PLA 0.2", "0.4": "Generic PLA", "0.6": "Generic PLA"}, "TPU": {}},
    styles={"Strong": {"0.4": {"wall_loops": 5}}},
    variants={"MM-Support": {"enable_support": "1"}},
)


def test_jobs_skip_the_bare_stock_preset() -> None:
    jobs = generate.process_jobs(PRINTER)
    assert ("0.4", "", "") not in jobs
    assert [j for j in jobs if j[0] == "0.4"] == [
        ("0.4", "", "MM-Support"),
        ("0.4", "Strong", ""),
        ("0.4", "Strong", "MM-Support"),
    ]


def test_process_name_takes_the_parent_layer_height() -> None:
    assert generate.process_name(PRINTER, "0.4", "Strong", "MM-Support") == "0.20mm Strong MM-Support @H3C 0.4"
    assert generate.process_name(PRINTER, "0.2", "", "MM-Support") == "0.10mm MM-Support @H3C 0.2"


def test_nozzles_that_share_a_parent_share_a_preset() -> None:
    pla = generate.Filament(material="PLA", notes="", s={})
    assert generate.filament_groups(PRINTER, pla) == {"Generic PLA 0.2": ["0.2"], "Generic PLA": ["0.4", "0.6"]}
    assert generate.filament_name("SUNLU PLA+", ["0.4", "0.6"]) == "SUNLU PLA+"
    assert generate.filament_name("SUNLU PLA+", ["0.2"]) == "SUNLU PLA+ 0.2 nozzle"


def test_a_nozzle_without_a_parent_stops_the_build() -> None:
    tpu = generate.Filament(material="TPU", notes="", s={})
    with pytest.raises(ValueError, match=r"'TPU' has no parent for the 0.2 nozzle"):
        _ = generate.filament_groups(PRINTER, tpu)


def test_a_filament_may_name_its_own_nozzles() -> None:
    pla = generate.Filament(material="PLA", notes="", s={}, nozzles=["0.4"])
    assert generate.filament_groups(PRINTER, pla) == {"Generic PLA": ["0.4"]}
    pla["nozzles"] = ["0.8"]
    with pytest.raises(ValueError, match=r"nozzles \['0.8'\] are not in config/h3c.json"):
        _ = generate.filament_groups(PRINTER, pla)


def test_values_fill_every_slot_of_the_parent() -> None:
    parent: Preset = {"nozzle_temperature": ["220", "220", "220"], "wall_loops": "2"}
    assert generate.fit("nozzle_temperature", 215, parent, "P") == ["215", "215", "215"]
    assert generate.fit("wall_loops", 5, parent, "P") == "5"
    assert generate.fit("filament_notes", "dry first", parent, "P") == ["dry first"]


def test_a_key_the_parent_lacks_stops_the_build() -> None:
    with pytest.raises(ValueError, match="'bed_temperature_formula' is not a key of the stock preset 'P'"):
        _ = generate.fit("bed_temperature_formula", "by_first_filament", {}, "P")


def test_parent_must_serve_every_claimed_printer() -> None:
    parent: Preset = {"compatible_printers": ["Bambu Lab H3C 0.4 nozzle"]}
    generate.compatible(parent, "P", ["Bambu Lab H3C 0.4 nozzle"])
    with pytest.raises(ValueError, match=r"not compatible with \['Bambu Lab H3C 0.2 nozzle'\]"):
        generate.compatible(parent, "P", ["Bambu Lab H3C 0.4 nozzle", "Bambu Lab H3C 0.2 nozzle"])


def test_committed_config_names_a_parent_for_every_filament_and_nozzle() -> None:
    p = generate.printer()
    for f in generate.filaments().values():
        assert sum(len(n) for n in generate.filament_groups(p, f).values()) == len(f.get("nozzles", p["nozzles"]))
