import re
from dataclasses import dataclass
from decimal import Decimal

from rapidfuzz import fuzz

from app.models.extraction import ExtractedRequirement, ExtractedSpecification

MATCH_THRESHOLD = 55.0
STRONG_TEXT_MATCH_THRESHOLD = 80.0
NUMERIC_TOLERANCE = 0.15

_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _extract_number(value: str | None) -> float | None:
    if not value:
        return None
    match = _NUMBER_RE.search(value.replace(",", ""))
    return float(match.group()) if match else None


def _compare_numeric(operator: str, expected: float, actual: float) -> bool:
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
    return False


def _within_tolerance(operator: str, expected: float, actual: float) -> bool:
    if expected == 0:
        return False
    relative_gap = abs(actual - expected) / abs(expected)
    if relative_gap > NUMERIC_TOLERANCE:
        return False
    if operator in (">=", ">"):
        return actual >= expected * (1 - NUMERIC_TOLERANCE)
    if operator in ("<=", "<"):
        return actual <= expected * (1 + NUMERIC_TOLERANCE)
    return relative_gap <= NUMERIC_TOLERANCE


def _best_candidate(
    requirement: ExtractedRequirement, specifications: list[ExtractedSpecification]
) -> tuple[ExtractedSpecification | None, float]:
    best_spec: ExtractedSpecification | None = None
    best_score = 0.0
    requirement_text = f"{requirement.requirement_label} {requirement.requirement_text}"
    for spec in specifications:
        spec_text = f"{spec.spec_label} {spec.spec_text}"
        score = fuzz.token_sort_ratio(requirement_text, spec_text)
        if score > best_score:
            best_score = score
            best_spec = spec
    return best_spec, best_score


@dataclass
class MatchOutcome:
    requirement: ExtractedRequirement
    matched_specification: ExtractedSpecification | None
    status: str
    match_score: Decimal
    rationale: str


def evaluate_requirement(
    requirement: ExtractedRequirement, specifications: list[ExtractedSpecification]
) -> MatchOutcome:
    candidate, fuzzy_score = _best_candidate(requirement, specifications)

    if candidate is None or fuzzy_score < MATCH_THRESHOLD:
        return MatchOutcome(
            requirement=requirement,
            matched_specification=None,
            status="no_match",
            match_score=Decimal("0"),
            rationale="No comparable vendor specification was found for this requirement.",
        )

    normalized_score = Decimal(str(round(fuzzy_score / 100, 3)))
    expected_number = _extract_number(requirement.expected_value)
    actual_number = _extract_number(candidate.value)

    if requirement.operator and expected_number is not None and actual_number is not None:
        unit = requirement.unit or ""
        if _compare_numeric(requirement.operator, expected_number, actual_number):
            status = "match"
            rationale = (
                f"Vendor value '{candidate.value or candidate.spec_text}' satisfies the requirement "
                f"({requirement.operator} {requirement.expected_value} {unit}).".strip()
            )
        elif _within_tolerance(requirement.operator, expected_number, actual_number):
            status = "partial"
            rationale = (
                f"Vendor value '{candidate.value or candidate.spec_text}' is close to but does not fully satisfy "
                f"the requirement ({requirement.operator} {requirement.expected_value} {unit}).".strip()
            )
        else:
            status = "no_match"
            rationale = (
                f"Vendor value '{candidate.value or candidate.spec_text}' does not satisfy the requirement "
                f"({requirement.operator} {requirement.expected_value} {unit}).".strip()
            )
    else:
        if fuzzy_score >= STRONG_TEXT_MATCH_THRESHOLD:
            status = "match"
            rationale = f"Vendor specification closely matches the stated requirement (text similarity {normalized_score:.0%})."
        elif fuzzy_score >= MATCH_THRESHOLD:
            status = "partial"
            rationale = (
                f"Vendor specification is a plausible but uncertain match for the requirement "
                f"(text similarity {normalized_score:.0%})."
            )
        else:
            status = "no_match"
            rationale = "No comparable vendor specification was found for this requirement."

    return MatchOutcome(
        requirement=requirement,
        matched_specification=candidate,
        status=status,
        match_score=normalized_score,
        rationale=rationale,
    )


def match_requirements(
    requirements: list[ExtractedRequirement], specifications: list[ExtractedSpecification]
) -> list[MatchOutcome]:
    return [evaluate_requirement(requirement, specifications) for requirement in requirements]
