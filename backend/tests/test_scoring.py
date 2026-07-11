from decimal import Decimal

from app.services.matching import config
from app.services.matching.matchers import MATCH, NO_MATCH, PARTIAL
from app.services.matching.scoring import ScoredEntry, compute_compliance_summary


def entry(vendor="Acme", status=MATCH, score="1.0", mandatory=True):
    return ScoredEntry(vendor_name=vendor, status=status, match_score=Decimal(score), is_mandatory=mandatory)


def test_empty_returns_empty():
    assert compute_compliance_summary([]) == []


def test_all_match_is_100():
    s = compute_compliance_summary([entry(), entry()])[0]
    assert s.overall_compliance_pct == 100.0
    assert s.matched == 2 and s.unmatched == 0


def test_mandatory_weighting():
    # one mandatory match (w=3, credit=1), one optional miss (w=1, credit=0)
    rows = [entry(status=MATCH, score="1.0", mandatory=True), entry(status=NO_MATCH, score="0.0", mandatory=False)]
    s = compute_compliance_summary(rows)[0]
    # weighted = 3*1 / (3+1) = 75%
    assert s.overall_compliance_pct == 75.0
    assert s.mandatory_met == 1 and s.optional_unmet == 1


def test_partial_credit_uses_match_score():
    rows = [entry(status=PARTIAL, score="0.5", mandatory=True)]
    s = compute_compliance_summary(rows)[0]
    assert s.overall_compliance_pct == 50.0
    assert s.partial == 1


def test_match_score_none_falls_back_to_status_credit():
    rows = [ScoredEntry("Acme", PARTIAL, None, True)]
    s = compute_compliance_summary(rows)[0]
    assert s.overall_compliance_pct == round(config.PARTIAL_CREDIT * 100, 1)


def test_multiple_vendors_sorted_desc():
    rows = [
        entry(vendor="Low", status=NO_MATCH, score="0.0"),
        entry(vendor="High", status=MATCH, score="1.0"),
    ]
    summaries = compute_compliance_summary(rows)
    assert [s.vendor_name for s in summaries] == ["High", "Low"]
    assert summaries[0].overall_compliance_pct == 100.0
    assert summaries[1].overall_compliance_pct == 0.0


def test_breakdown_counts():
    rows = [
        entry(status=MATCH, score="1.0", mandatory=True),
        entry(status=PARTIAL, score="0.6", mandatory=True),
        entry(status=NO_MATCH, score="0.0", mandatory=False),
    ]
    s = compute_compliance_summary(rows)[0]
    assert s.total_requirements == 3
    assert (s.mandatory_total, s.mandatory_met, s.mandatory_partial, s.mandatory_unmet) == (2, 1, 1, 0)
    assert (s.optional_total, s.optional_met, s.optional_partial, s.optional_unmet) == (1, 0, 0, 1)
