from app.services.matching import EQUIPMENT_MATCHED, EQUIPMENT_UNMATCHED, match_equipment, match_equipment_parameters
from app.services.matching.matchers import NO_MATCH
from tests._factories import make_requirement, make_requirement_group, make_specification


def test_match_equipment_exact_key_match():
    req = make_requirement_group(
        equipment_key="core_switch",
        equipment_label="Core Switch",
        parameters=[make_requirement(key="ports", label="Ports")],
    )
    specs = [make_specification(key="ports", label="Ports", equipment_key="core_switch", equipment_label="Core Switch")]
    [outcome] = match_equipment([req], specs)
    assert outcome.status == EQUIPMENT_MATCHED
    assert outcome.matched_equipment_key == "core_switch"
    assert outcome.confidence_score == 100.0
    assert outcome.matched_specifications == specs


def test_match_equipment_below_threshold_is_unmatched():
    req = make_requirement_group(
        equipment_key="ip_camera",
        equipment_label="IP Camera",
        parameters=[make_requirement(key="resolution", label="Resolution")],
    )
    specs = [
        make_specification(
            key="capacity", label="Capacity", equipment_key="ups_unit", equipment_label="UPS Unit"
        )
    ]
    [outcome] = match_equipment([req], specs)
    assert outcome.status == EQUIPMENT_UNMATCHED
    assert outcome.matched_equipment_key is None
    assert outcome.matched_specifications == []
    # Audit trail: the best (sub-threshold) score is still recorded, not discarded.
    assert 0.0 <= outcome.confidence_score < 60.0


def test_match_equipment_no_vendor_specs_at_all():
    req = make_requirement_group(
        equipment_key="ip_camera",
        equipment_label="IP Camera",
        parameters=[make_requirement(key="resolution", label="Resolution")],
    )
    [outcome] = match_equipment([req], [])
    assert outcome.status == EQUIPMENT_UNMATCHED
    assert outcome.confidence_score == 0.0
    assert outcome.vendor_source_page is None


def test_match_equipment_vendor_source_page_is_min_of_group():
    req = make_requirement_group(
        equipment_key="core_switch",
        equipment_label="Core Switch",
        parameters=[make_requirement(key="ports", label="Ports")],
    )
    specs = [
        make_specification(key="ports", label="Ports", equipment_key="core_switch", equipment_label="Core Switch"),
        make_specification(key="throughput", label="Throughput", equipment_key="core_switch", equipment_label="Core Switch"),
    ]
    specs[0].source_page = 5
    specs[1].source_page = 2
    [outcome] = match_equipment([req], specs)
    assert outcome.status == EQUIPMENT_MATCHED
    assert outcome.vendor_source_page == 2


def test_match_equipment_many_to_one_allowed():
    """Two different RFP equipment may each independently pick the same vendor
    equipment as their single best match — no exclusivity/greedy assignment."""
    req_a = make_requirement_group(
        equipment_key="access_switch", equipment_label="Access Switch",
        parameters=[make_requirement(key="ports", label="Ports")],
    )
    req_b = make_requirement_group(
        equipment_key="core_switch", equipment_label="Core Switch",
        parameters=[make_requirement(key="ports", label="Ports")],
    )
    specs = [make_specification(key="ports", label="Ports", equipment_key="switch", equipment_label="Switch")]
    outcome_a, outcome_b = match_equipment([req_a, req_b], specs)
    assert outcome_a.status == EQUIPMENT_MATCHED
    assert outcome_b.status == EQUIPMENT_MATCHED
    assert outcome_a.matched_equipment_key == outcome_b.matched_equipment_key == "switch"


def test_match_equipment_parameters_scoped_only_to_matched_specs():
    param = make_requirement(key="throughput", label="Throughput", expected_value="20", unit="Mbps", operator=">=")
    # Deliberately exclude the spec that would otherwise satisfy this parameter —
    # Stage 2 must be a pure function of exactly what it's given, nothing more.
    unrelated_spec = make_specification(key="color", label="Chassis Colour", value="black")
    [outcome] = match_equipment_parameters([param], [unrelated_spec])
    assert outcome.status == NO_MATCH
