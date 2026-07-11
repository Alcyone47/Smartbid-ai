"""Deterministic compliance scoring.

Pure aggregation over already-computed match rows — no LLM, no DB. Produces a
per-vendor compliance summary: a mandatory-weighted overall percentage plus
mandatory/optional breakdowns and status counts. The API adapts persisted rows
into ``ScoredEntry`` instances before calling ``compute_compliance_summary``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from app.services.matching import config
from app.services.matching.matchers import MATCH, NO_MATCH, PARTIAL

_STATUS_CREDIT = {MATCH: config.MATCH_CREDIT, PARTIAL: config.PARTIAL_CREDIT, NO_MATCH: config.NO_MATCH_CREDIT}


@dataclass(frozen=True)
class ScoredEntry:
    vendor_name: str
    status: str
    match_score: Decimal | None
    is_mandatory: bool


@dataclass
class VendorComplianceSummary:
    vendor_name: str
    overall_compliance_pct: float
    total_requirements: int
    matched: int
    partial: int
    unmatched: int
    mandatory_total: int
    mandatory_met: int
    mandatory_partial: int
    mandatory_unmet: int
    optional_total: int
    optional_met: int
    optional_partial: int
    optional_unmet: int


def _credit(entry: ScoredEntry) -> float:
    if entry.match_score is not None:
        return max(0.0, min(1.0, float(entry.match_score)))
    return _STATUS_CREDIT.get(entry.status, 0.0)


def compute_compliance_summary(entries: Iterable[ScoredEntry]) -> list[VendorComplianceSummary]:
    """Aggregate match rows into one summary per vendor, ranked by compliance desc."""
    by_vendor: dict[str, list[ScoredEntry]] = {}
    for entry in entries:
        by_vendor.setdefault(entry.vendor_name, []).append(entry)

    summaries = [_summarize(vendor, rows) for vendor, rows in by_vendor.items()]
    summaries.sort(key=lambda s: s.overall_compliance_pct, reverse=True)
    return summaries


def _summarize(vendor_name: str, rows: list[ScoredEntry]) -> VendorComplianceSummary:
    weighted_credit = 0.0
    total_weight = 0.0
    counts = {MATCH: 0, PARTIAL: 0, NO_MATCH: 0}
    mand = {MATCH: 0, PARTIAL: 0, NO_MATCH: 0}
    opt = {MATCH: 0, PARTIAL: 0, NO_MATCH: 0}

    for row in rows:
        weight = config.weight_for(row.is_mandatory)
        weighted_credit += weight * _credit(row)
        total_weight += weight
        bucket = row.status if row.status in counts else NO_MATCH
        counts[bucket] += 1
        (mand if row.is_mandatory else opt)[bucket] += 1

    overall = round(weighted_credit / total_weight * 100, 1) if total_weight else 0.0

    return VendorComplianceSummary(
        vendor_name=vendor_name,
        overall_compliance_pct=overall,
        total_requirements=len(rows),
        matched=counts[MATCH],
        partial=counts[PARTIAL],
        unmatched=counts[NO_MATCH],
        mandatory_total=sum(mand.values()),
        mandatory_met=mand[MATCH],
        mandatory_partial=mand[PARTIAL],
        mandatory_unmet=mand[NO_MATCH],
        optional_total=sum(opt.values()),
        optional_met=opt[MATCH],
        optional_partial=opt[PARTIAL],
        optional_unmet=opt[NO_MATCH],
    )
