"""Tunable constants for the deterministic matching engine.

Single source of truth for thresholds, tolerances, status credit, and the
mandatory-vs-optional weights used by compliance scoring. Nothing here calls the
LLM; adjusting these values changes matching/scoring behaviour without touching
any logic.
"""

# --- Pairing (parameter-aware candidate selection) ---
# Minimum normalized-label similarity (0-100) for a spec to be considered a
# plausible candidate for a requirement before typed comparison runs.
PAIRING_MIN_SIMILARITY = 55.0
# A label similarity at/above this is treated as a confident parameter match.
PAIRING_STRONG_SIMILARITY = 80.0

# --- Numeric comparison ---
# Relative gap (fraction of the expected value) still counted as a partial match
# when the strict operator check fails, e.g. 0.15 == within 15%.
NUMERIC_TOLERANCE = 0.15

# --- Text comparison ---
# Normalized fuzzy similarity (0-100) required for a text match / partial.
TEXT_STRONG_SIMILARITY = 85.0
TEXT_PARTIAL_SIMILARITY = 60.0

# --- Status -> compliance credit (0..1) ---
# Credit awarded per requirement for aggregate scoring. Typed matchers may return
# a finer-grained partial credit; PARTIAL_CREDIT is the default when they don't.
MATCH_CREDIT = 1.0
PARTIAL_CREDIT = 0.5
NO_MATCH_CREDIT = 0.0

# --- Scoring weights ---
# Relative importance of a requirement in the weighted compliance percentage.
MANDATORY_WEIGHT = 3.0
OPTIONAL_WEIGHT = 1.0


def weight_for(is_mandatory: bool) -> float:
    """Weight a requirement contributes to the compliance percentage."""
    return MANDATORY_WEIGHT if is_mandatory else OPTIONAL_WEIGHT
