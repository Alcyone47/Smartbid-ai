"""Parameter-aware pairing: choose the vendor spec that describes the same
parameter as a requirement.

Prefers an exact normalized key match, then normalized label similarity, then a
discounted full-text fallback — all gated by unit-dimension compatibility so a
spec measured in a different quantity can't win on incidental word overlap.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rapidfuzz import fuzz

from app.services.matching.normalization import normalize_phrase
from app.services.matching.units import same_dimension

if TYPE_CHECKING:
    from app.models.extraction import ExtractedRequirement, ExtractedSpecification

_INCOMPATIBLE_DIMENSION_PENALTY = 0.4
_TEXT_FALLBACK_DISCOUNT = 0.9


def candidate_score(
    requirement: "ExtractedRequirement", spec: "ExtractedSpecification"
) -> float:
    """0-100 confidence that ``spec`` describes the same parameter as ``requirement``."""
    req_key = normalize_phrase(requirement.requirement_key)
    spec_key = normalize_phrase(spec.spec_key)
    if req_key and req_key == spec_key:
        base = 100.0
    else:
        req_label = normalize_phrase(requirement.requirement_label)
        spec_label = normalize_phrase(spec.spec_label)
        label_score = max(
            fuzz.token_set_ratio(req_label, spec_label),
            fuzz.token_sort_ratio(req_label, spec_label),
        )
        text_score = fuzz.token_set_ratio(
            normalize_phrase(f"{requirement.requirement_label} {requirement.requirement_text}"),
            normalize_phrase(f"{spec.spec_label} {spec.spec_text}"),
        )
        base = max(float(label_score), _TEXT_FALLBACK_DISCOUNT * float(text_score))

    if not same_dimension(requirement.unit, spec.unit):
        base *= _INCOMPATIBLE_DIMENSION_PENALTY
    return base


def best_candidate(
    requirement: "ExtractedRequirement", specifications: list["ExtractedSpecification"]
) -> tuple["ExtractedSpecification | None", float]:
    best_spec: "ExtractedSpecification | None" = None
    best_score = 0.0
    for spec in specifications:
        score = candidate_score(requirement, spec)
        if score > best_score:
            best_score = score
            best_spec = spec
    return best_spec, best_score
