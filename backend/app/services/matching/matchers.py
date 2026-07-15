"""Typed comparison functions. Each returns a MatchResult(status, credit, rationale).

status is one of "match" / "partial" / "no_match"; credit is the 0..1 compliance
credit used by scoring. All comparisons are deterministic.
"""

from __future__ import annotations

from typing import NamedTuple

from rapidfuzz import fuzz

from app.services.matching import config
from app.services.matching.units import convert_to_base, is_unrecognized, unit_dimension

_LIST_ITEM_SIMILARITY = 85.0


class MatchResult(NamedTuple):
    status: str
    credit: float
    rationale: str


NO_MATCH = "no_match"
PARTIAL = "partial"
MATCH = "match"


def _normalize_operator(operator: str | None) -> str:
    op = (operator or "").strip()
    if op in ("=", "=="):
        return "=="
    return op


def _compare(operator: str, expected: float, actual: float) -> bool:
    if operator == ">=":
        return actual >= expected
    if operator == "<=":
        return actual <= expected
    if operator == "==":
        return actual == expected
    if operator == ">":
        return actual > expected
    if operator == "<":
        return actual < expected
    # no/blank operator: treat as equality
    return actual == expected


def _common_base(
    expected: float, expected_unit: str | None, actual: float, actual_unit: str | None
) -> tuple[float, float] | None:
    """Convert both operands to a shared base unit, or None if dimensions conflict."""
    edim = unit_dimension(expected_unit)
    adim = unit_dimension(actual_unit)
    if edim and adim:
        if edim != adim:
            return None
        return convert_to_base(expected, expected_unit), convert_to_base(actual, actual_unit)  # type: ignore[return-value]
    if edim and not adim:
        if is_unrecognized(actual_unit):  # vendor stated a unit we can't reconcile
            return None
        # unit absent: assume the actual value shares the requirement's unit
        return convert_to_base(expected, expected_unit), convert_to_base(actual, expected_unit)  # type: ignore[return-value]
    if adim and not edim:
        if is_unrecognized(expected_unit):
            return None
        return convert_to_base(expected, actual_unit), convert_to_base(actual, actual_unit)  # type: ignore[return-value]
    return expected, actual  # neither unit recognised: compare raw magnitudes


def match_numeric(
    operator: str | None,
    expected: float | None,
    expected_unit: str | None,
    actual: float | None,
    actual_unit: str | None,
) -> MatchResult:
    if expected is None or actual is None:
        return MatchResult(NO_MATCH, config.NO_MATCH_CREDIT, "Vendor did not state a comparable numeric value.")

    common = _common_base(expected, expected_unit, actual, actual_unit)
    if common is None:
        return MatchResult(
            NO_MATCH,
            config.NO_MATCH_CREDIT,
            f"Vendor value is measured in a different quantity ({actual_unit}) than the requirement ({expected_unit}).",
        )
    exp_base, act_base = common
    op = _normalize_operator(operator)
    unit_txt = f" {expected_unit}" if expected_unit else ""
    req_txt = f"{op} {_fmt(expected)}{unit_txt}".strip()

    if _compare(op, exp_base, act_base):
        return MatchResult(MATCH, config.MATCH_CREDIT, f"Vendor value {_fmt(actual)}{_ustr(actual_unit)} satisfies {req_txt}.")

    if exp_base != 0:
        gap = abs(act_base - exp_base) / abs(exp_base)
        directional_ok = (
            (op in (">=", ">") and act_base >= exp_base * (1 - config.NUMERIC_TOLERANCE))
            or (op in ("<=", "<") and act_base <= exp_base * (1 + config.NUMERIC_TOLERANCE))
            or (op == "==")
        )
        if gap <= config.NUMERIC_TOLERANCE and directional_ok:
            credit = round(0.9 - 0.4 * (gap / config.NUMERIC_TOLERANCE), 3)
            return MatchResult(
                PARTIAL, credit, f"Vendor value {_fmt(actual)}{_ustr(actual_unit)} is within {int(config.NUMERIC_TOLERANCE*100)}% of {req_txt}."
            )

    return MatchResult(NO_MATCH, config.NO_MATCH_CREDIT, f"Vendor value {_fmt(actual)}{_ustr(actual_unit)} does not satisfy {req_txt}.")


def match_boolean(required: bool | None, provided: bool | None) -> MatchResult:
    if provided is None:
        return MatchResult(NO_MATCH, config.NO_MATCH_CREDIT, "Vendor did not state whether this capability is provided.")
    if required is None:
        required = True  # a boolean requirement with no explicit polarity means "must be present"
    if required == provided:
        return MatchResult(MATCH, config.MATCH_CREDIT, f"Requirement expects {_yn(required)}; vendor states {_yn(provided)}.")
    return MatchResult(NO_MATCH, config.NO_MATCH_CREDIT, f"Requirement expects {_yn(required)}; vendor states {_yn(provided)}.")


def match_list(required: list[str], provided: list[str]) -> MatchResult:
    if not required:
        return MatchResult(NO_MATCH, config.NO_MATCH_CREDIT, "No list items were specified in the requirement.")
    missing = [item for item in required if not _item_present(item, provided)]
    matched = len(required) - len(missing)
    fraction = matched / len(required)
    if fraction >= 1.0:
        return MatchResult(MATCH, config.MATCH_CREDIT, f"All {len(required)} required items are offered by the vendor.")
    if matched == 0:
        return MatchResult(NO_MATCH, config.NO_MATCH_CREDIT, f"None of the {len(required)} required items are offered by the vendor.")
    return MatchResult(
        PARTIAL,
        round(fraction, 3),
        f"{matched} of {len(required)} required items offered; missing: {', '.join(missing)}.",
    )


def match_text(required_phrase: str, provided_phrase: str) -> MatchResult:
    if not required_phrase or not provided_phrase:
        return MatchResult(NO_MATCH, config.NO_MATCH_CREDIT, "No comparable vendor text was found.")
    if required_phrase == provided_phrase:
        return MatchResult(MATCH, config.MATCH_CREDIT, "Vendor text matches the requirement.")
    score = max(
        fuzz.token_sort_ratio(required_phrase, provided_phrase),
        fuzz.token_set_ratio(required_phrase, provided_phrase),
    )
    if score >= config.TEXT_STRONG_SIMILARITY:
        return MatchResult(MATCH, config.MATCH_CREDIT, f"Vendor text closely matches the requirement (similarity {score:.0f}%).")
    if score >= config.TEXT_PARTIAL_SIMILARITY:
        return MatchResult(PARTIAL, round(score / 100, 3), f"Vendor text is a plausible but uncertain match (similarity {score:.0f}%).")
    return MatchResult(NO_MATCH, config.NO_MATCH_CREDIT, f"Vendor text does not match the requirement (similarity {score:.0f}%).")


def _item_present(item: str, provided: list[str]) -> bool:
    if item in provided:
        return True
    return any(fuzz.token_set_ratio(item, candidate) >= _LIST_ITEM_SIMILARITY for candidate in provided)


def _fmt(number: float) -> str:
    return str(int(number)) if number == int(number) else str(number)


def _ustr(unit: str | None) -> str:
    return f" {unit}" if unit else ""


def _yn(value: bool) -> str:
    return "yes" if value else "no"
