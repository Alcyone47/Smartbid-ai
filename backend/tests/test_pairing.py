from app.services.matching.pairing import best_candidate, candidate_score
from tests._factories import make_requirement, make_specification


def test_exact_key_match_scores_max():
    req = make_requirement(key="throughput", label="Throughput")
    spec = make_specification(key="throughput", label="Link Speed")
    assert candidate_score(req, spec) == 100.0


def test_unit_dimension_gate_penalizes_wrong_dimension():
    req = make_requirement(key="latency", label="Latency", unit="ms")
    right = make_specification(key="latency", label="Latency", unit="ms")
    wrong = make_specification(key="latency", label="Latency", unit="km")
    assert candidate_score(req, right) > candidate_score(req, wrong)


def test_best_candidate_picks_correct_spec():
    req = make_requirement(key="power", label="Power Consumption")
    specs = [
        make_specification(key="weight", label="Weight"),
        make_specification(key="power", label="Power Consumption"),
        make_specification(key="ports", label="Port Count"),
    ]
    best, score = best_candidate(req, specs)
    assert best is specs[1] and score == 100.0


def test_best_candidate_label_fuzzy_fallback():
    req = make_requirement(key="op_temp", label="Operating Temperature Range")
    spec = make_specification(key="temp_operating", label="Operating Temperature")
    best, score = best_candidate(req, [spec])
    assert best is spec and score >= 55.0


def test_best_candidate_none_when_no_specs():
    best, score = best_candidate(make_requirement(), [])
    assert best is None and score == 0.0
