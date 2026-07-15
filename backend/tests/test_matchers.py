from app.services.matching import matchers as M


# --- numeric ---


def test_numeric_ge_pass_unit_normalized():
    r = M.match_numeric(">=", 20, "Mbps", 2, "Gbps")
    assert r.status == M.MATCH and r.credit == 1.0


def test_numeric_le_pass():
    assert M.match_numeric("<=", 40, "C", 35, "C").status == M.MATCH


def test_numeric_equality_operator_variants():
    # both '=' and '==' must be treated as equality (the extraction emits '=')
    assert M.match_numeric("=", 230, "V", 230, "V").status == M.MATCH
    assert M.match_numeric("==", 230, "V", 230, "V").status == M.MATCH


def test_numeric_equality_near_is_partial():
    # equality targets still allow the tolerance band (240 is ~4% off 230)
    assert M.match_numeric("=", 230, "V", 240, "V").status == M.PARTIAL


def test_numeric_equality_far_fail():
    assert M.match_numeric("=", 230, "V", 300, "V").status == M.NO_MATCH


def test_numeric_within_tolerance_partial():
    r = M.match_numeric(">=", 100, None, 90, None)  # 10% short, within 15%
    assert r.status == M.PARTIAL and 0.5 <= r.credit < 1.0


def test_numeric_outside_tolerance_no_match():
    assert M.match_numeric(">=", 100, None, 50, None).status == M.NO_MATCH


def test_numeric_dimension_mismatch_no_match():
    r = M.match_numeric(">=", 20, "Mbps", 5, "km")
    assert r.status == M.NO_MATCH


def test_numeric_hz_vs_nits_no_match():
    # regression: 64 Hz must not match 64 nits (different physical quantities)
    r = M.match_numeric("==", 64, "Hz", 64, "nits")
    assert r.status == M.NO_MATCH


def test_numeric_known_vs_unrecognized_unit_no_match():
    # a vendor unit we don't recognise must not be assumed to share the
    # requirement's unit
    r = M.match_numeric("==", 64, "Hz", 64, "blorps")
    assert r.status == M.NO_MATCH


def test_numeric_bare_actual_assumes_requirement_unit():
    # vendor stated a bare number: still compared in the requirement's unit
    r = M.match_numeric(">=", 100, "ms", 90, None)
    assert r.status == M.PARTIAL


def test_numeric_nit_alias_cdm2():
    r = M.match_numeric(">=", 300, "nits", 350, "cd/m2")
    assert r.status == M.MATCH


def test_numeric_missing_actual_no_match():
    assert M.match_numeric(">=", 20, "Mbps", None, None).status == M.NO_MATCH


# --- boolean ---


def test_boolean_match():
    assert M.match_boolean(True, True).status == M.MATCH


def test_boolean_mismatch():
    assert M.match_boolean(True, False).status == M.NO_MATCH


def test_boolean_provided_unknown():
    assert M.match_boolean(True, None).status == M.NO_MATCH


def test_boolean_required_none_defaults_true():
    assert M.match_boolean(None, True).status == M.MATCH


# --- list ---


def test_list_full_match():
    assert M.match_list(["ospf", "bgp"], ["ospf", "bgp", "rip"]).status == M.MATCH


def test_list_partial_credit_is_fraction():
    r = M.match_list(["ospf", "bgp", "rip"], ["ospf", "bgp"])
    assert r.status == M.PARTIAL and r.credit == round(2 / 3, 3)
    assert "rip" in r.rationale


def test_list_disjoint_no_match():
    assert M.match_list(["ospf"], ["mpls"]).status == M.NO_MATCH


def test_list_fuzzy_item_present():
    # near-identical wording still counts as present
    assert M.match_list(["gigabit ethernet"], ["gigabit ethernet port"]).status == M.MATCH


# --- text ---


def test_text_exact_match():
    assert M.match_text("rack mountable", "rack mountable").status == M.MATCH


def test_text_strong_similarity_match():
    assert M.match_text("rack mountable chassis", "rack mountable chassis unit").status == M.MATCH


def test_text_partial():
    r = M.match_text("supports ipsec vpn tunnels", "ipsec vpn")
    assert r.status in (M.PARTIAL, M.MATCH)


def test_text_no_match():
    assert M.match_text("liquid cooling", "wall mounted bracket").status == M.NO_MATCH
