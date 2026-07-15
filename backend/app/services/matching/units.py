"""Deterministic unit registry and conversion.

Each known unit maps to ``(dimension, factor, offset)`` where the value in the
dimension's base unit is ``value * factor + offset`` (offset is only non-zero for
temperature). This lets the numeric matcher compare, e.g., "30 mins" against
"0.5 hr" or "2 GB" against "2048 MB". Unknown units return ``None`` so callers
can fall back rather than guess.

Data-size AND data-rate prefixes (k/M/G/T) are treated as **binary** (1024-based),
matching hardware/memory/storage convention so that, e.g., 2048 MB == 2 GB and
2048 Mbps == 2 Gbps compare as exactly equal rather than off by ~2.4%.
"""

from __future__ import annotations

# Dimensions (base unit in parentheses)
DATA_RATE = "data_rate"  # bit/s
DATA_SIZE = "data_size"  # byte
TIME = "time"  # second
LENGTH = "length"  # meter
MASS = "mass"  # gram
VOLTAGE = "voltage"  # volt
CURRENT = "current"  # ampere
POWER = "power"  # watt
APPARENT_POWER = "apparent_power"  # volt-ampere
FREQUENCY = "frequency"  # hertz
ANGLE = "angle"  # degree
PRESSURE = "pressure"  # pascal
TEMPERATURE = "temperature"  # celsius
PERCENTAGE = "percentage"  # percent
LUMINANCE = "luminance"  # candela per square meter (nit)

# canonical token -> (dimension, factor_to_base, offset_to_base)
_UNITS: dict[str, tuple[str, float, float]] = {
    # data rate (base: bit/s) — binary (1024-based) prefixes
    "bps": (DATA_RATE, 1.0, 0.0),
    "kbps": (DATA_RATE, 1024.0, 0.0),
    "mbps": (DATA_RATE, 1024.0**2, 0.0),
    "gbps": (DATA_RATE, 1024.0**3, 0.0),
    "tbps": (DATA_RATE, 1024.0**4, 0.0),
    # data size (base: byte) — binary (1024-based) prefixes, so 2048 MB == 2 GB
    "byte": (DATA_SIZE, 1.0, 0.0),
    "kb": (DATA_SIZE, 1024.0, 0.0),
    "mb": (DATA_SIZE, 1024.0**2, 0.0),
    "gb": (DATA_SIZE, 1024.0**3, 0.0),
    "tb": (DATA_SIZE, 1024.0**4, 0.0),
    "kib": (DATA_SIZE, 1024.0, 0.0),
    "mib": (DATA_SIZE, 1024.0**2, 0.0),
    "gib": (DATA_SIZE, 1024.0**3, 0.0),
    "tib": (DATA_SIZE, 1024.0**4, 0.0),
    # time (base: second)
    "ms": (TIME, 1e-3, 0.0),
    "s": (TIME, 1.0, 0.0),
    "min": (TIME, 60.0, 0.0),
    "hr": (TIME, 3600.0, 0.0),
    "day": (TIME, 86400.0, 0.0),
    "week": (TIME, 604800.0, 0.0),
    "month": (TIME, 2592000.0, 0.0),  # 30 days (approx)
    "year": (TIME, 31536000.0, 0.0),  # 365 days (approx)
    # length (base: meter)
    "mm": (LENGTH, 1e-3, 0.0),
    "cm": (LENGTH, 1e-2, 0.0),
    "m": (LENGTH, 1.0, 0.0),
    "km": (LENGTH, 1e3, 0.0),
    "in": (LENGTH, 0.0254, 0.0),
    "ft": (LENGTH, 0.3048, 0.0),
    "mi": (LENGTH, 1609.344, 0.0),
    # mass (base: gram)
    "mg": (MASS, 1e-3, 0.0),
    "g": (MASS, 1.0, 0.0),
    "kg": (MASS, 1e3, 0.0),
    "tonne": (MASS, 1e6, 0.0),
    "lb": (MASS, 453.59237, 0.0),
    "oz": (MASS, 28.349523, 0.0),
    # voltage (base: volt)
    "mv": (VOLTAGE, 1e-3, 0.0),
    "v": (VOLTAGE, 1.0, 0.0),
    "kv": (VOLTAGE, 1e3, 0.0),
    # current (base: ampere)
    "ma": (CURRENT, 1e-3, 0.0),
    "a": (CURRENT, 1.0, 0.0),
    "ka": (CURRENT, 1e3, 0.0),
    # power (base: watt) — 'mw' is intentionally omitted (milliwatt vs megawatt ambiguity)
    "w": (POWER, 1.0, 0.0),
    "kw": (POWER, 1e3, 0.0),
    "megawatt": (POWER, 1e6, 0.0),
    # apparent power (base: volt-ampere)
    "va": (APPARENT_POWER, 1.0, 0.0),
    "kva": (APPARENT_POWER, 1e3, 0.0),
    "mva": (APPARENT_POWER, 1e6, 0.0),
    # frequency (base: hertz)
    "hz": (FREQUENCY, 1.0, 0.0),
    "khz": (FREQUENCY, 1e3, 0.0),
    "mhz": (FREQUENCY, 1e6, 0.0),
    "ghz": (FREQUENCY, 1e9, 0.0),
    # angle (base: degree)
    "deg": (ANGLE, 1.0, 0.0),
    "rad": (ANGLE, 57.29578, 0.0),
    # pressure (base: pascal)
    "pa": (PRESSURE, 1.0, 0.0),
    "kpa": (PRESSURE, 1e3, 0.0),
    "bar": (PRESSURE, 1e5, 0.0),
    "psi": (PRESSURE, 6894.757, 0.0),
    # temperature (base: celsius) — linear: base = value*factor + offset
    "c": (TEMPERATURE, 1.0, 0.0),
    "k": (TEMPERATURE, 1.0, -273.15),
    "f": (TEMPERATURE, 5.0 / 9.0, -160.0 / 9.0),
    # percentage (dimensionless family)
    "%": (PERCENTAGE, 1.0, 0.0),
    # luminance (base: candela per square meter, i.e. nit)
    "nit": (LUMINANCE, 1.0, 0.0),
}

# variant spelling -> canonical token
_ALIASES: dict[str, str] = {
    "bit/s": "bps", "bits/s": "bps", "bitpersecond": "bps",
    "kbit/s": "kbps", "kb/s": "kbps", "kbit": "kbps",
    "mbit/s": "mbps", "mb/s": "mbps", "mbit": "mbps", "megabitspersecond": "mbps",
    "gbit/s": "gbps", "gb/s": "gbps", "gbit": "gbps",
    "bytes": "byte", "b": "byte",
    "kilobyte": "kb", "kilobytes": "kb",
    "megabyte": "mb", "megabytes": "mb",
    "gigabyte": "gb", "gigabytes": "gb",
    "terabyte": "tb", "terabytes": "tb",
    "millisecond": "ms", "milliseconds": "ms", "msec": "ms", "msecs": "ms",
    "sec": "s", "secs": "s", "second": "s", "seconds": "s",
    "mins": "min", "minute": "min", "minutes": "min",
    "hrs": "hr", "hour": "hr", "hours": "hr",
    "days": "day", "weeks": "week", "months": "month", "years": "year", "yr": "year", "yrs": "year",
    "millimeter": "mm", "millimetre": "mm", "millimeters": "mm",
    "centimeter": "cm", "centimetre": "cm", "centimeters": "cm",
    "meter": "m", "metre": "m", "meters": "m", "metres": "m",
    "kilometer": "km", "kilometre": "km", "kilometers": "km",
    "inch": "in", "inches": "in",
    "foot": "ft", "feet": "ft",
    "mile": "mi", "miles": "mi",
    "milligram": "mg", "milligrams": "mg",
    "gram": "g", "grams": "g", "gm": "g",
    "kilogram": "kg", "kilograms": "kg", "kgs": "kg",
    "ton": "tonne", "tons": "tonne", "tonnes": "tonne",
    "lbs": "lb", "pound": "lb", "pounds": "lb",
    "ounce": "oz", "ounces": "oz",
    "millivolt": "mv", "millivolts": "mv",
    "volt": "v", "volts": "v",
    "kilovolt": "kv", "kilovolts": "kv",
    "milliamp": "ma", "milliampere": "ma", "milliamps": "ma", "milliamperes": "ma",
    "amp": "a", "amps": "a", "ampere": "a", "amperes": "a",
    "kiloamp": "ka", "kiloampere": "ka",
    "watt": "w", "watts": "w",
    "kilowatt": "kw", "kilowatts": "kw",
    "megawatts": "megawatt",
    "voltamp": "va", "voltampere": "va", "voltamperes": "va", "voltamps": "va",
    "kilovoltamp": "kva", "kilovoltampere": "kva", "kilovoltamperes": "kva", "kilovoltamps": "kva",
    "megavoltampere": "mva", "megavoltamperes": "mva",
    "hertz": "hz",
    "kilohertz": "khz", "megahertz": "mhz", "gigahertz": "ghz",
    "degree": "deg", "degrees": "deg", "°": "deg",
    "radian": "rad", "radians": "rad",
    "pascal": "pa", "pascals": "pa",
    "kilopascal": "kpa", "kilopascals": "kpa",
    "bars": "bar",
    "celsius": "c", "°c": "c", "degc": "c", "degreec": "c", "degreecelsius": "c",
    "kelvin": "k",
    "fahrenheit": "f", "°f": "f", "degf": "f", "degreef": "f", "degreefahrenheit": "f",
    "percent": "%", "percentage": "%", "pct": "%", "pc": "%",
    "nits": "nit", "cd/m2": "nit", "cd/m²": "nit", "candela/m2": "nit", "candelapersquaremeter": "nit",
}


def normalize_unit(unit: str | None) -> str | None:
    """Return the canonical unit token, or ``None`` if empty/unknown."""
    if not unit:
        return None
    token = unit.strip().lower().replace(" ", "").rstrip(".")
    if token in _UNITS:
        return token
    if token in _ALIASES:
        return _ALIASES[token]
    return None


def unit_dimension(unit: str | None) -> str | None:
    """Physical dimension for a unit, or ``None`` if unknown/dimensionless-empty."""
    token = normalize_unit(unit)
    if token is None:
        return None
    return _UNITS[token][0]


def is_unrecognized(unit: str | None) -> bool:
    """True when a unit string is present (non-empty) but not in the registry."""
    return bool(unit and unit.strip()) and normalize_unit(unit) is None


def same_dimension(unit_a: str | None, unit_b: str | None) -> bool:
    """Whether two units are comparable.

    Compatible when both share a dimension, when either side is absent (a bare
    number may share the other side's unit), or when both are unrecognized (we
    can't prove incompatibility). A *known* unit against a present-but-unrecognized
    unit is incompatible: the document explicitly states a quantity we cannot
    reconcile with the known dimension (e.g. "Hz" vs "nits" before nits was known).
    """
    dim_a = unit_dimension(unit_a)
    dim_b = unit_dimension(unit_b)
    if dim_a is not None and dim_b is not None:
        return dim_a == dim_b
    if dim_a is not None and is_unrecognized(unit_b):
        return False
    if dim_b is not None and is_unrecognized(unit_a):
        return False
    return True


def convert_to_base(value: float, unit: str | None) -> float | None:
    """Convert ``value`` in ``unit`` to its dimension's base unit.

    Returns the value unchanged when the unit is absent (dimensionless), or ``None``
    when the unit is present but unrecognised.
    """
    if unit is None or unit == "":
        return value
    token = normalize_unit(unit)
    if token is None:
        return None
    _, factor, offset = _UNITS[token]
    return value * factor + offset
