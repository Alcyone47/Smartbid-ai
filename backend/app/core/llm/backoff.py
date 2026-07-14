"""Deterministic-testable backoff helpers for LLM rate-limit (429) handling.

Pure functions — no network, no provider imports — so they can be unit-tested and
reused across providers.
"""

from __future__ import annotations

import random
import re
from typing import Callable

# Matches a protobuf duration like "42s" or "1.5s" (Gemini's RetryInfo.retryDelay).
_DURATION_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*s")


def parse_retry_delay_seconds(value: object) -> float | None:
    """Convert a retryDelay / Retry-After value to seconds, or None if unparseable."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = _DURATION_RE.search(str(value))
    return float(match.group(1)) if match else None


def compute_backoff(
    attempt: int,
    base_delay: float,
    max_delay: float,
    server_delay: float | None = None,
    rand: Callable[[], float] = random.random,
) -> float:
    """Seconds to wait before retry ``attempt`` (0-based).

    Exponential ``base * 2**attempt`` capped at ``max_delay``, with equal jitter so the
    result lands in ``[capped/2, capped]``. If the server suggested a longer wait
    (retryDelay/Retry-After), that value wins — never retry sooner than the server asked.
    """
    capped = min(base_delay * (2**attempt), max_delay)
    half = capped / 2
    delay = half + rand() * half
    if server_delay is not None and server_delay > delay:
        delay = server_delay
    return delay
