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

from collections import defaultdict

from app.services.matching import config, matchers, param_types
from app.services.matching.pairing import best_candidate, equipment_candidate_score

if TYPE_CHECKING:
    from app.models.extraction import (
        ExtractedSpecification,
        Requirement,
        RequirementParameter,
    )


@dataclass
class MatchOutcome:
    # ``requirement`` is a single parameter (with its Minimum Required
    # Specification); its equipment_key/label/text alias attributes let the typed
    # matchers read it unchanged.
    requirement: "RequirementParameter"
    matched_specification: "ExtractedSpecification | None"
    status: str
    match_score: Decimal
    rationale: str


def evaluate_requirement(
    requirement: "RequirementParameter", specifications: list["ExtractedSpecification"]
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
    requirement: "RequirementParameter", candidate: "ExtractedSpecification"
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


def _group_specs_by_equipment(
    specifications: list["ExtractedSpecification"],
) -> dict[str, list["ExtractedSpecification"]]:
    groups: dict[str, list["ExtractedSpecification"]] = defaultdict(list)
    for spec in specifications:
        groups[spec.equipment_key].append(spec)
    return dict(groups)


def _match_vendor_equipment(
    req_equipment_key: str,
    req_equipment_label: str,
    spec_groups: dict[str, list["ExtractedSpecification"]],
) -> list["ExtractedSpecification"] | None:
    """Pick the vendor equipment group that best corresponds to an RFP equipment group.

    Returns the scoped spec list, or None when no vendor equipment clears the
    similarity threshold (caller then falls back to the full spec pool).
    """
    best_specs: list["ExtractedSpecification"] | None = None
    best_score = 0.0
    for spec_key, specs in spec_groups.items():
        spec_label = specs[0].equipment_label if specs else spec_key
        score = equipment_candidate_score(req_equipment_key, req_equipment_label, spec_key, spec_label)
        if score > best_score:
            best_score = score
            best_specs = specs
    if best_specs is None or best_score < config.EQUIPMENT_PAIRING_MIN_SIMILARITY:
        return None
    return best_specs


def _flatten_parameters(
    requirements: list["Requirement | RequirementParameter"],
) -> list["RequirementParameter"]:
    """Expand hierarchical Requirements (equipment) into their flat parameter list.

    Tolerates being handed parameters directly (an item without a ``parameters``
    attribute is treated as a parameter itself), so callers and tests can pass
    either shape.
    """
    parameters: list["RequirementParameter"] = []
    for requirement in requirements:
        children = getattr(requirement, "parameters", None)
        if children is None:
            parameters.append(requirement)  # already a parameter
        else:
            parameters.extend(children)
    return parameters


def match_requirements(
    requirements: list["Requirement | RequirementParameter"],
    specifications: list["ExtractedSpecification"],
) -> list[MatchOutcome]:
    """Equipment-first matching over the hierarchy: each Requirement is one
    equipment/item; its parameters are compared only against the vendor equipment
    group that best corresponds to it. Falls back to the full spec pool when no
    vendor equipment matches, so single-equipment ("general") documents behave
    exactly as before.
    """
    parameters = _flatten_parameters(requirements)
    spec_groups = _group_specs_by_equipment(specifications)

    # Resolve the scoped spec pool once per equipment group, not per parameter.
    scoped_specs_by_equipment: dict[str, list["ExtractedSpecification"]] = {}
    for parameter in parameters:
        equipment_key = parameter.equipment_key
        if equipment_key not in scoped_specs_by_equipment:
            matched = _match_vendor_equipment(
                equipment_key, parameter.equipment_label, spec_groups
            )
            scoped_specs_by_equipment[equipment_key] = (
                matched if matched is not None else specifications
            )

    return [
        evaluate_requirement(parameter, scoped_specs_by_equipment[parameter.equipment_key])
        for parameter in parameters
    ]
