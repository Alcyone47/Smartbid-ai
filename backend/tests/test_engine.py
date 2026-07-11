from pathlib import Path

import app.services.matching as matching_pkg
from app.services.matching import evaluate_requirement, match_requirements
from app.services.matching.matchers import MATCH, NO_MATCH, PARTIAL
from tests._factories import make_requirement, make_specification


def test_numeric_end_to_end_unit_normalized():
    req = make_requirement(key="throughput", label="Throughput", expected_value="20", unit="Mbps", operator=">=")
    spec = make_specification(key="throughput", label="Throughput", value="2", unit="Gbps")
    outcome = evaluate_requirement(req, [spec])
    assert outcome.status == MATCH
    assert float(outcome.match_score) == 1.0
    assert outcome.matched_specification is spec


def test_boolean_end_to_end():
    req = make_requirement(key="redundancy", label="Power Redundancy", expected_value="required")
    spec = make_specification(key="redundancy", label="Power Redundancy", value="Supported")
    assert evaluate_requirement(req, [spec]).status == MATCH


def test_list_partial_end_to_end():
    req = make_requirement(
        key="routing", label="Routing Protocols", text="Must support OSPF, BGP and RIP", is_mandatory=False
    )
    spec = make_specification(key="routing", label="Routing Protocols", text="OSPF and BGP supported")
    outcome = evaluate_requirement(req, [spec])
    assert outcome.status == PARTIAL
    assert float(outcome.match_score) == round(2 / 3, 3)


def test_no_candidate_is_no_match():
    req = make_requirement(key="latency", label="Latency", expected_value="10", unit="ms", operator="<=")
    spec = make_specification(key="color", label="Chassis Colour", value="black")
    outcome = evaluate_requirement(req, [spec])
    assert outcome.status == NO_MATCH
    assert outcome.matched_specification is None


def test_determinism():
    req = make_requirement(key="throughput", label="Throughput", expected_value="20", unit="Mbps", operator=">=")
    specs = [
        make_specification(key="weight", label="Weight", value="2", unit="kg"),
        make_specification(key="throughput", label="Throughput", value="18", unit="Mbps"),
    ]
    first = evaluate_requirement(req, specs)
    second = evaluate_requirement(req, specs)
    assert (first.status, first.match_score, first.rationale) == (second.status, second.match_score, second.rationale)


def test_match_requirements_maps_all():
    reqs = [make_requirement(key="a", label="A"), make_requirement(key="b", label="B")]
    outcomes = match_requirements(reqs, [])
    assert len(outcomes) == 2 and all(o.status == NO_MATCH for o in outcomes)


def test_engine_never_imports_llm():
    """Static guard: no module in the matching package may import the LLM layer."""
    package_dir = Path(matching_pkg.__file__).parent
    forbidden = ("core.llm", "get_llm_provider", "anthropic", "groq", "genai", "voyageai")
    for path in package_dir.glob("*.py"):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                for needle in forbidden:
                    assert needle not in stripped, f"{path.name} imports '{needle}': {stripped}"
