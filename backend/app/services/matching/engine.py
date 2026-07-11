"""Matching engine orchestration.

Per requirement: pick the parameter-matched vendor spec (pairing), infer the
comparison type, dispatch to the typed matcher, and produce a MatchOutcome whose
``match_score`` is the satisfaction credit (0..1). Fully deterministic — imports
nothing from ``app.core.llm``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.matching import config, matchers, param_types
from app.services.matching.pairing import best_candidate

if TYPE_CHECKING:
    from app.models.extraction import ExtractedRequirement, ExtractedSpecification


@dataclass
class MatchOutcome:
    requirement: "ExtractedRequirement"
    matched_specification: "ExtractedSpecification | None"
    status: str
    match_score: Decimal
    rationale: str


def evaluate_requirement(
    requirement: "ExtractedRequirement", specifications: list["ExtractedSpecification"]
) -> MatchOutcome:
    candidate, pairing_score = best_candidate(requirement, specifications)

    if candidate is None or pairing_score < config.PAIRING_MIN_SIMILARITY:
        return MatchOutcome(
            requirement=requirement,
            matched_specification=None,
            status=matchers.NO_MATCH,
            match_score=Decimal("0"),
            rationale="No comparable vendor specification was found for this requirement.",
        )

    result = _compare(requirement, candidate)
    return MatchOutcome(
        requirement=requirement,
        matched_specification=candidate,
        status=result.status,
        match_score=Decimal(str(round(result.credit, 3))),
        rationale=result.rationale,
    )


def _compare(
    requirement: "ExtractedRequirement", candidate: "ExtractedSpecification"
) -> matchers.MatchResult:
    param_type = param_types.infer_type(requirement)

    if param_type == param_types.NUMERIC:
        expected, expected_unit, actual, actual_unit = param_types.numeric_operands(requirement, candidate)
        if expected is None or actual is None:
            # numeric intent but a value is missing — fall back to text comparison
            return matchers.match_text(*param_types.text_operands(requirement, candidate))
        return matchers.match_numeric(requirement.operator, expected, expected_unit, actual, actual_unit)

    if param_type == param_types.BOOLEAN:
        return matchers.match_boolean(*param_types.boolean_operands(requirement, candidate))

    if param_type == param_types.LIST:
        return matchers.match_list(*param_types.list_operands(requirement, candidate))

    return matchers.match_text(*param_types.text_operands(requirement, candidate))


def match_requirements(
    requirements: list["ExtractedRequirement"], specifications: list["ExtractedSpecification"]
) -> list[MatchOutcome]:
    return [evaluate_requirement(requirement, specifications) for requirement in requirements]
