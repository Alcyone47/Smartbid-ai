import pytest

from app.services.matching.normalization import (
    canonicalize_text,
    normalize_phrase,
    parse_boolean,
    parse_number,
    parse_value_unit,
    split_list,
)
from app.services.matching.units import (
    convert_to_base,
    normalize_unit,
    same_dimension,
    unit_dimension,
)


def test_canonicalize_text():
    assert canonicalize_text("  Three-Phase / 400V  ") == "three phase 400v"
    assert canonicalize_text(None) == ""


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Three-Phase", "3 phase"),
        ("3ph", "3 phase"),
        ("single phase", "1 phase"),
        ("three", "3"),
        ("Twenty ports", "20 ports"),
    ],
)
def test_normalize_phrase_synonyms_and_numbers(raw, expected):
    assert normalize_phrase(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [("20", 20.0), ("0.5", 0.5), ("1,024", 1024.0), ("three", 3.0), ("none", None), ("", None)],
)
def test_parse_number(raw, expected):
    assert parse_number(raw) == expected


@pytest.mark.parametrize(
    "raw,number,unit",
    [
        ("30 mins", 30.0, "mins"),
        ("2Gbps", 2.0, "Gbps"),
        ("0.5 hr", 0.5, "hr"),
        ("230", 230.0, None),
        ("no numbers", None, None),
    ],
)
def test_parse_value_unit(raw, number, unit):
    assert parse_value_unit(raw) == (number, unit)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Yes", True),
        ("Supported", True),
        ("Required", True),
        ("No", False),
        ("Not Available", False),
        ("N/A", False),
        ("unsupported", False),
        ("20 Mbps", None),
    ],
)
def test_parse_boolean(raw, expected):
    assert parse_boolean(raw) == expected


def test_split_list():
    assert split_list("OSPF, BGP and RIP") == ["ospf", "bgp", "rip"]
    assert split_list("A; B / C") == ["a", "b", "c"]
    assert split_list("only item") == ["only item"]
    assert split_list("") == []


def test_split_list_dedup():
    assert split_list("BGP, bgp, OSPF") == ["bgp", "ospf"]


# --- units ---


def test_time_equivalence_min_hr():
    assert convert_to_base(30, "min") == convert_to_base(0.5, "hr") == 1800.0


def test_data_rate_equivalence_mbps_gbps():
    # Binary (1024-based) prefixes: 2048 Mbps == 2 Gbps.
    assert convert_to_base(2048, "Mbps") == convert_to_base(2, "Gbps")


def test_data_size_equivalence_mb_gb():
    # The reported case: 2048 MB must equal 2 GB (binary/storage convention).
    assert convert_to_base(2048, "MB") == convert_to_base(2, "GB")


def test_voltage_kv_v():
    assert convert_to_base(1, "kV") == convert_to_base(1000, "V")


def test_temperature_offsets():
    assert convert_to_base(0, "C") == 0.0
    assert convert_to_base(273.15, "K") == pytest.approx(0.0)
    assert convert_to_base(32, "F") == pytest.approx(0.0)
    assert convert_to_base(212, "F") == pytest.approx(100.0)


def test_unit_aliases():
    assert normalize_unit("minutes") == "min"
    assert normalize_unit("Mbit/s") == "mbps"
    assert normalize_unit("kilograms") == "kg"


def test_unknown_unit_returns_none():
    assert normalize_unit("ports") is None
    assert convert_to_base(5, "ports") is None
    assert unit_dimension("ports") is None


def test_same_dimension():
    assert same_dimension("min", "hr") is True
    assert same_dimension("Mbps", "km") is False  # different known dimensions
    assert same_dimension("ports", "widgets") is True  # both unknown -> allowed
    assert same_dimension("V", None) is True  # one absent -> allowed
