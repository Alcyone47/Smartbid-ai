"""Unit tests for GeminiProvider's output-truncation recovery helpers."""

from google.genai import types

from app.core.llm.gemini_provider import (
    _is_truncated,
    _merge_list_payloads,
    _split_document_text,
)


class _FakeCandidate:
    def __init__(self, finish_reason):
        self.finish_reason = finish_reason


class _FakeResponse:
    def __init__(self, finish_reason=None, candidates=True):
        self.candidates = [_FakeCandidate(finish_reason)] if candidates else []


def test_is_truncated_on_max_tokens():
    assert _is_truncated(_FakeResponse(types.FinishReason.MAX_TOKENS)) is True


def test_is_not_truncated_on_stop_or_missing_candidates():
    assert _is_truncated(_FakeResponse(types.FinishReason.STOP)) is False
    assert _is_truncated(_FakeResponse(candidates=False)) is False


def test_split_prefers_page_marker_boundary():
    # The page-2 marker sits before the midpoint, so the split lands on it
    # rather than on an arbitrary newline.
    left_pages = "--- page 1 ---\n" + "a" * 100
    right_pages = "\n--- page 2 ---\n" + "b" * 500
    left, right = _split_document_text(left_pages + right_pages)
    assert left == left_pages
    assert right.startswith("\n--- page 2 ---")


def test_split_falls_back_to_newline_then_midpoint():
    text = "x" * 100 + "\n" + "y" * 100
    left, right = _split_document_text(text)
    assert left + right == text
    assert left.endswith("x" * 10)  # cut at the newline before the midpoint

    no_newline = "z" * 200
    left, right = _split_document_text(no_newline)
    assert left + right == no_newline
    assert len(left) == 100


def test_merge_list_payloads_concatenates_lists():
    left = {"requirements": [{"a": 1}], "note": "l"}
    right = {"requirements": [{"b": 2}], "extra": True}
    merged = _merge_list_payloads(left, right)
    assert merged["requirements"] == [{"a": 1}, {"b": 2}]
    assert merged["note"] == "l"
    assert merged["extra"] is True


def test_parse_json_lenient_handles_extra_data_and_fences():
    from app.core.llm.gemini_provider import _parse_json_lenient

    assert _parse_json_lenient('{"a": 1}') == {"a": 1}
    # Extra data after the object (observed in production) -> first object wins.
    assert _parse_json_lenient('{"a": 1}\n{"b": 2}') == {"a": 1}
    assert _parse_json_lenient('{"a": 1} trailing prose') == {"a": 1}
    # Markdown fences despite JSON mime type.
    assert _parse_json_lenient('```json\n{"a": 1}\n```') == {"a": 1}
