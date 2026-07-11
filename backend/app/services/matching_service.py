"""Backward-compatible facade for the matching engine.

The implementation now lives in the ``app.services.matching`` package. This module
is kept so existing imports (``from app.services.matching_service import
match_requirements``) continue to work.
"""

from app.services.matching import MatchOutcome, evaluate_requirement, match_requirements

__all__ = ["MatchOutcome", "evaluate_requirement", "match_requirements"]
