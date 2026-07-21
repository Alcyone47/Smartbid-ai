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


EQUIPMENT_MATCHED = "matched"
EQUIPMENT_UNMATCHED = "unmatched"


@dataclass
class EquipmentMatchOutcome:
    """Stage-1 result for one RFP equipment (Requirement) against one vendor's specs."""

    requirement: "Requirement"
    matched_equipment_key: str | None
    matched_equipment_label: str | None
    confidence_score: float
    status: str
    vendor_source_page: int | None
    # Transient — the Stage-1-matched vendor specs, for Stage 2 to consume. Not
    # persisted (EquipmentMatch stores only the key/label/score/status).
    matched_specifications: list["ExtractedSpecification"]


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


def _best_equipment_candidate(
    req_equipment_key: str,
    req_equipment_label: str,
    spec_groups: dict[str, list["ExtractedSpecification"]],
) -> tuple[str | None, str | None, float, list["ExtractedSpecification"]]:
    """Best-scoring vendor equipment group for an RFP equipment, regardless of
    threshold (score 0.0 / empty list if there are no vendor equipment groups)."""
    best_key: str | None = None
    best_label: str | None = None
    best_specs: list["ExtractedSpecification"] = []
    best_score = 0.0
    for spec_key, specs in spec_groups.items():
        spec_label = specs[0].equipment_label if specs else spec_key
        score = equipment_candidate_score(req_equipment_key, req_equipment_label, spec_key, spec_label)
        if score > best_score:
            best_score, best_key, best_label, best_specs = score, spec_key, spec_label, specs
    return best_key, best_label, best_score, best_specs


def _match_vendor_equipment(
    req_equipment_key: str,
    req_equipment_label: str,
    spec_groups: dict[str, list["ExtractedSpecification"]],
) -> list["ExtractedSpecification"] | None:
    """Pick the vendor equipment group that best corresponds to an RFP equipment group.

    Returns the scoped spec list, or None when no vendor equipment clears the
    similarity threshold.
    """
    _key, _label, best_score, best_specs = _best_equipment_candidate(
        req_equipment_key, req_equipment_label, spec_groups
    )
    if not best_specs or best_score < config.EQUIPMENT_PAIRING_MIN_SIMILARITY:
        return None
    return best_specs


def match_equipment(
    requirements: list["Requirement"],
    specifications: list["ExtractedSpecification"],
) -> list[EquipmentMatchOutcome]:
    """Stage 1: for each RFP equipment (Requirement), pick the single best-matching
    vendor equipment group for this vendor's specs, or mark it unmatched. No
    fallback to the unscoped spec pool — this is the persisted, auditable pairing
    that Stage 2 (``match_equipment_parameters``) must never bypass.
    """
    spec_groups = _group_specs_by_equipment(specifications)
    outcomes: list[EquipmentMatchOutcome] = []
    for requirement in requirements:
        key, label, score, specs = _best_equipment_candidate(
            requirement.equipment_key, requirement.equipment_label, spec_groups
        )
        if not specs or score < config.EQUIPMENT_PAIRING_MIN_SIMILARITY:
            outcomes.append(
                EquipmentMatchOutcome(
                    requirement=requirement,
                    matched_equipment_key=None,
                    matched_equipment_label=None,
                    confidence_score=round(score, 2),
                    status=EQUIPMENT_UNMATCHED,
                    vendor_source_page=None,
                    matched_specifications=[],
                )
            )
            continue
        pages = [s.source_page for s in specs if s.source_page is not None]
        outcomes.append(
            EquipmentMatchOutcome(
                requirement=requirement,
                matched_equipment_key=key,
                matched_equipment_label=label,
                confidence_score=round(score, 2),
                status=EQUIPMENT_MATCHED,
                vendor_source_page=min(pages) if pages else None,
                matched_specifications=specs,
            )
        )
    return outcomes


def match_equipment_parameters(
    parameters: list["RequirementParameter"],
    vendor_specs: list["ExtractedSpecification"],
) -> list[MatchOutcome]:
    """Stage 2: compare one equipment's parameters against ONLY its Stage-1-matched
    vendor specs. Callers must not invoke this for unmatched equipment — skip it
    entirely rather than passing an unscoped/empty substitute.
    """
    return [evaluate_requirement(parameter, vendor_specs) for parameter in parameters]


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
    group that best corresponds to it. When no vendor equipment clears the
    similarity threshold, that equipment's parameters are compared against an
    empty pool (i.e. NO_MATCH) — never against unrelated vendor equipment.

    Kept as a convenience one-shot function for callers/tests that pass bare
    parameters without a real ``Requirement`` (no ``id`` to key a persisted
    Stage-1 pairing). The production API path uses ``match_equipment`` +
    ``match_equipment_parameters`` directly so Stage-1 outcomes can be persisted.
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
            scoped_specs_by_equipment[equipment_key] = matched if matched is not None else []

    return [
        evaluate_requirement(parameter, scoped_specs_by_equipment[parameter.equipment_key])
        for parameter in parameters
    ]
