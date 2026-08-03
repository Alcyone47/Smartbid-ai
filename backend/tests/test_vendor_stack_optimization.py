import uuid
from decimal import Decimal

from app.schemas.compliance import EquipmentComplianceGroup, EquipmentSpecComparison
from app.services.matching.optimization import optimize_vendor_stack

VENDOR_A = uuid.uuid4()
VENDOR_B = uuid.uuid4()


def _spec(
    *, status: str = "match", match_score: str | None = "1.0", is_mandatory: bool = True
) -> EquipmentSpecComparison:
    return EquipmentSpecComparison(
        id=uuid.uuid4(),
        requirement_id=uuid.uuid4(),
        matched_specification_id=None,
        requirement_label="Ports",
        requirement_text="",
        expected_value=None,
        unit=None,
        operator=None,
        is_mandatory=is_mandatory,
        vendor_value=None,
        source_page=None,
        status=status,
        match_score=Decimal(match_score) if match_score is not None else None,
        rationale="",
    )


def _group(
    *,
    equipment_key: str,
    vendor_id: uuid.UUID,
    vendor_name: str,
    compliance_pct: float,
    match_status: str = "matched",
    equipment_match_confidence: float | None = 100.0,
    specs: list[EquipmentSpecComparison] | None = None,
) -> EquipmentComplianceGroup:
    specs = specs if specs is not None else []
    return EquipmentComplianceGroup(
        equipment_key=equipment_key,
        equipment_label=equipment_key.replace("_", " ").title(),
        vendor_name=vendor_name,
        vendor_id=vendor_id,
        match_status=match_status,
        equipment_match_confidence=equipment_match_confidence,
        compliance_pct=compliance_pct,
        total_specs=len(specs),
        matched=sum(1 for s in specs if s.status == "match"),
        partial=sum(1 for s in specs if s.status == "partial"),
        unmatched=sum(1 for s in specs if s.status not in ("match", "partial")),
        specs=specs,
    )


def test_picks_highest_compliance_vendor_per_equipment():
    groups = [
        _group(
            equipment_key="core_switch",
            vendor_id=VENDOR_A,
            vendor_name="Acme",
            compliance_pct=80.0,
            specs=[_spec(match_score="0.8")],
        ),
        _group(
            equipment_key="core_switch",
            vendor_id=VENDOR_B,
            vendor_name="Zenith",
            compliance_pct=95.0,
            specs=[_spec(match_score="0.95")],
        ),
    ]
    result = optimize_vendor_stack(groups)
    [selection] = result.equipment
    assert selection.best_vendor_id == VENDOR_B
    assert selection.best_vendor_name == "Zenith"
    assert selection.compliance_pct == 95.0
    # Candidates are exposed ranked desc for explainability.
    assert [c.vendor_name for c in selection.candidates] == ["Zenith", "Acme"]


def test_tie_break_by_confidence_then_vendor_name():
    groups = [
        _group(
            equipment_key="ups",
            vendor_id=VENDOR_A,
            vendor_name="Beta",
            compliance_pct=90.0,
            equipment_match_confidence=70.0,
        ),
        _group(
            equipment_key="ups",
            vendor_id=VENDOR_B,
            vendor_name="Alpha",
            compliance_pct=90.0,
            equipment_match_confidence=90.0,
        ),
    ]
    result = optimize_vendor_stack(groups)
    [selection] = result.equipment
    # Same compliance_pct -> higher equipment_match_confidence wins, not vendor name.
    assert selection.best_vendor_name == "Alpha"


def test_tie_break_falls_back_to_vendor_name_when_confidence_equal():
    groups = [
        _group(
            equipment_key="ups",
            vendor_id=VENDOR_A,
            vendor_name="Zenith",
            compliance_pct=90.0,
            equipment_match_confidence=80.0,
        ),
        _group(
            equipment_key="ups",
            vendor_id=VENDOR_B,
            vendor_name="Acme",
            compliance_pct=90.0,
            equipment_match_confidence=80.0,
        ),
    ]
    result = optimize_vendor_stack(groups)
    [selection] = result.equipment
    assert selection.best_vendor_name == "Acme"


def test_equipment_with_no_vendor_match_is_excluded_from_overall_score():
    groups = [
        _group(
            equipment_key="ip_camera",
            vendor_id=VENDOR_A,
            vendor_name="Acme",
            compliance_pct=0.0,
            match_status="unmatched",
            equipment_match_confidence=20.0,
        ),
        _group(
            equipment_key="core_switch",
            vendor_id=VENDOR_A,
            vendor_name="Acme",
            compliance_pct=100.0,
            specs=[_spec(match_score="1.0")],
        ),
    ]
    result = optimize_vendor_stack(groups)
    unmatched = next(s for s in result.equipment if s.equipment_key == "ip_camera")
    assert unmatched.best_vendor_id is None
    assert unmatched.best_vendor_name is None
    assert unmatched.match_status == "unmatched"
    # Only the matched equipment's specs feed the overall score.
    assert result.overall_optimized_compliance_pct == 100.0


def test_overall_score_applies_mandatory_weighting():
    groups = [
        _group(
            equipment_key="core_switch",
            vendor_id=VENDOR_A,
            vendor_name="Acme",
            compliance_pct=50.0,
            specs=[
                _spec(status="match", match_score="1.0", is_mandatory=True),
                _spec(status="no_match", match_score="0.0", is_mandatory=False),
            ],
        ),
    ]
    result = optimize_vendor_stack(groups)
    # Mandatory weight 3.0 vs optional weight 1.0: (3*1.0 + 1*0.0) / 4 * 100 = 75.0
    assert result.overall_optimized_compliance_pct == 75.0


def test_vendor_usage_tally_across_multiple_equipment():
    groups = [
        _group(equipment_key="core_switch", vendor_id=VENDOR_A, vendor_name="Acme", compliance_pct=90.0),
        _group(equipment_key="access_switch", vendor_id=VENDOR_A, vendor_name="Acme", compliance_pct=85.0),
        _group(equipment_key="ups", vendor_id=VENDOR_B, vendor_name="Zenith", compliance_pct=99.0),
    ]
    result = optimize_vendor_stack(groups)
    usage_by_vendor = {u.vendor_name: u.equipment_count for u in result.vendor_usage}
    assert usage_by_vendor == {"Acme": 2, "Zenith": 1}
    # Sorted desc by equipment_count.
    assert result.vendor_usage[0].vendor_name == "Acme"
