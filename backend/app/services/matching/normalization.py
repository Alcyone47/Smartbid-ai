"""Deterministic text/value normalization used by the matchers.

Pure string logic — canonicalization, synonym folding, boolean/number-word
parsing, value+unit extraction, and list splitting. No LLM, no I/O.
"""

from __future__ import annotations

import re

_SEPARATOR_RE = re.compile(r"[_/\\|\-]+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9%. ]")
_WS_RE = re.compile(r"\s+")
_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")
# a number optionally followed by a unit token (letters, %, /, . )
_VALUE_UNIT_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*([a-zA-Z%][a-zA-Z%/.]*)?")
_LIST_SPLIT_RE = re.compile(r"\s*(?:,|;|/|\band\b|&|\bor\b|\n|•|•)\s*")

_NUMBER_WORDS: dict[str, float] = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80,
    "ninety": 90, "hundred": 100, "thousand": 1000, "million": 1_000_000,
}

# canonicalized phrase -> canonical form (applied token-wise after canonicalization)
_PHRASE_SYNONYMS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(?:three|3|tri)\s*phase\b"), "3 phase"),
    (re.compile(r"\b(?:single|one|1)\s*phase\b"), "1 phase"),
    (re.compile(r"\b3ph\b"), "3 phase"),
    (re.compile(r"\b1ph\b"), "1 phase"),
]

_BOOL_FALSE_PHRASES = (
    "not supported", "not available", "not included", "not provided",
    "not compatible", "not present", "n a",
)
_BOOL_TRUE_TOKENS = {
    "yes", "true", "y", "supported", "support", "available", "included",
    "present", "provided", "compatible", "enabled", "mandatory", "required",
    "compliant", "pass", "ok", "yea",
}
_BOOL_FALSE_TOKENS = {
    "no", "false", "n", "unsupported", "unavailable", "excluded", "absent",
    "incompatible", "disabled", "none", "na", "fail",
}


def canonicalize_text(value: str | None) -> str:
    """Lowercase, replace separators with spaces, drop punctuation, collapse spaces."""
    if not value:
        return ""
    text = value.lower().strip()
    text = _SEPARATOR_RE.sub(" ", text)
    text = _NON_ALNUM_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()


def normalize_phrase(value: str | None) -> str:
    """Canonicalize plus fold number-words and known synonym phrases to a stable form."""
    text = canonicalize_text(value)
    if not text:
        return ""
    for pattern, replacement in _PHRASE_SYNONYMS:
        text = pattern.sub(replacement, text)
    tokens = [str(int(_NUMBER_WORDS[t])) if t in _NUMBER_WORDS else t for t in text.split()]
    return " ".join(tokens)


def parse_number(value: str | None) -> float | None:
    """First numeric value in the string, supporting number-words like 'three'."""
    if not value:
        return None
    cleaned = value.replace(",", "")
    match = _NUMBER_RE.search(cleaned)
    if match:
        return float(match.group())
    for token in canonicalize_text(value).split():
        if token in _NUMBER_WORDS:
            return float(_NUMBER_WORDS[token])
    return None


def parse_value_unit(value: str | None) -> tuple[float | None, str | None]:
    """Extract a leading number and its adjacent unit token, e.g. '30 mins' -> (30.0, 'mins')."""
    if not value:
        return None, None
    cleaned = value.replace(",", "")
    match = _VALUE_UNIT_RE.search(cleaned)
    if match:
        number = float(match.group(1))
        unit = match.group(2)
        return number, (unit or None)
    return parse_number(value), None


def parse_boolean(value: str | None) -> bool | None:
    """Interpret yes/no/supported/etc. Returns None when not boolean-like."""
    text = canonicalize_text(value)
    if not text:
        return None
    for phrase in _BOOL_FALSE_PHRASES:
        if phrase in text:
            return False
    tokens = set(text.split())
    if tokens & _BOOL_FALSE_TOKENS:
        return False
    if tokens & _BOOL_TRUE_TOKENS:
        return True
    return None


def split_list(value: str | None) -> list[str]:
    """Split a delimited enumeration into normalized, de-duplicated items (order kept)."""
    if not value:
        return []
    items: list[str] = []
    seen: set[str] = set()
    for raw in _LIST_SPLIT_RE.split(value):
        item = normalize_phrase(raw)
        if item and item not in seen:
            seen.add(item)
            items.append(item)
    return items
