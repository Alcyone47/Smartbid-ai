"""Parameter type inference and operand extraction.

Decides whether a requirement is numeric / boolean / list / text from the shape of
its extracted JSON (operator + value + text), and pulls the comparable operands
out of a requirement/spec pair — reading structured ``value``/``expected_value``
first and falling back to the free-text field when the structured value is empty.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.matching.normalization import (
    parse_boolean,
    parse_number,
    parse_value_unit,
    normalize_phrase,
    split_list,
)

if TYPE_CHECKING:  # avoid a hard import; matchers only read attributes
    from app.models.extraction import ExtractedSpecification, RequirementParameter  # type-only

NUMERIC = "numeric"
BOOLEAN = "boolean"
LIST = "list"
TEXT = "text"

NUMERIC_OPERATORS = {">", ">=", "<", "<=", "==", "="}
_MAX_LIST_ITEM_WORDS = 4  # guard so prose sentences aren't misread as lists


def infer_type(requirement: "RequirementParameter") -> str:
    """Classify a requirement's comparison type deterministically."""
    expected = requirement.expected_value
    operator = (requirement.operator or "").strip()

    if operator in NUMERIC_OPERATORS and parse_number(expected or requirement.requirement_text) is not None:
        return NUMERIC

    if expected and parse_number(expected) is None and parse_boolean(expected) is not None:
        return BOOLEAN

    if _looks_like_list(expected) or (not expected and _looks_like_list(requirement.requirement_text)):
        return LIST

    if expected and parse_number(expected) is not None:
        # a bare number with no operator — still compare numerically
        return NUMERIC

    return TEXT


def _looks_like_list(value: str | None) -> bool:
    items = split_list(value)
    if len(items) < 2:
        return False
    avg_words = sum(len(item.split()) for item in items) / len(items)
    return avg_words <= _MAX_LIST_ITEM_WORDS


def numeric_operands(
    requirement: "RequirementParameter", spec: "ExtractedSpecification"
) -> tuple[float | None, str | None, float | None, str | None]:
    """(expected_number, expected_unit, actual_number, actual_unit)."""
    exp_num, exp_unit = parse_value_unit(requirement.expected_value)
    if exp_num is None:
        exp_num = parse_number(requirement.requirement_text)
    expected_unit = requirement.unit or exp_unit

    act_num, act_unit = parse_value_unit(spec.value if spec.value else spec.spec_text)
    actual_unit = spec.unit or act_unit
    return exp_num, expected_unit, act_num, actual_unit


def boolean_operands(
    requirement: "RequirementParameter", spec: "ExtractedSpecification"
) -> tuple[bool | None, bool | None]:
    req_bool = parse_boolean(requirement.expected_value)
    if req_bool is None:
        req_bool = parse_boolean(requirement.requirement_text)
    spec_bool = parse_boolean(spec.value)
    if spec_bool is None:
        spec_bool = parse_boolean(spec.spec_text)
    return req_bool, spec_bool


def list_operands(
    requirement: "RequirementParameter", spec: "ExtractedSpecification"
) -> tuple[list[str], list[str]]:
    required = split_list(requirement.expected_value) or split_list(requirement.requirement_text)
    provided_source = " , ".join(filter(None, [spec.value, spec.spec_text]))
    provided = split_list(provided_source)
    return required, provided


def text_operands(
    requirement: "RequirementParameter", spec: "ExtractedSpecification"
) -> tuple[str, str]:
    req_phrase = normalize_phrase(
        requirement.expected_value or requirement.requirement_text or requirement.requirement_label
    )
    spec_phrase = normalize_phrase(spec.value or spec.spec_text or spec.spec_label)
    return req_phrase, spec_phrase
