from app.schemas.extraction import RequirementExtractionItem
from app.services.extraction_service import (
    _batch_document,
    _batch_segments,
    _parse_batch_items,
    _segment_pages,
)


def test_parse_batch_items_skips_malformed_keeps_valid():
    data = {
        "requirements": [
            {"requirement_key": "k1", "requirement_label": "Good One", "requirement_text": "t", "is_mandatory": True},
            {"equipment_key": "wifi", "requirement_text": "missing label", "is_mandatory": True},  # no requirement_label
        ]
    }
    items, skipped = _parse_batch_items(data, "requirements", RequirementExtractionItem)
    assert skipped == 1
    assert [i.requirement_label for i in items] == ["Good One"]


def test_parse_batch_items_handles_missing_key():
    assert _parse_batch_items({}, "requirements", RequirementExtractionItem) == ([], 0)
    assert _parse_batch_items("garbage", "requirements", RequirementExtractionItem) == ([], 0)


def _page_count(block: str) -> int:
    return block.count("--- page ")


def test_page_group_batches_not_one_per_page():
    pages = [f"page {i} content" for i in range(1, 21)]  # 20 short pages
    batches = _batch_document(pages, max_chars=100_000, max_pages=8)
    # 20 pages @ 8 per group -> 3 batches (8, 8, 4), NOT 20.
    assert len(batches) == 3
    assert [_page_count(b) for b in batches] == [8, 8, 4]


def test_char_cap_closes_batch_before_page_cap():
    # Each page ~50 chars; char cap of 120 fits ~2 pages even though page cap is 8.
    pages = ["x" * 50 for _ in range(6)]
    batches = _batch_document(pages, max_chars=120, max_pages=8)
    assert len(batches) > 1
    for block in batches:
        # source text portion stays under the cap (markers add a little overhead)
        assert _page_count(block) <= 3


def test_oversized_single_page_is_split_by_chars():
    pages = ["y" * 250]  # one page far larger than the char cap
    segments = _segment_pages(pages, max_chars=100)
    assert len(segments) == 3  # 100 + 100 + 50
    assert all(page_no == 1 for page_no, _ in segments)
    # batching still produces at least one block and preserves the page number
    batches = _batch_document(pages, max_chars=100, max_pages=8)
    assert all("--- page 1 ---" in b for b in batches)


def test_batch_segments_groups_by_page_limit():
    segs = [(i, "t") for i in range(1, 11)]  # 10 distinct pages, tiny text
    batches = _batch_segments(segs, max_chars=100_000, max_pages=5)
    assert len(batches) == 2 and len(batches[0]) == 5 and len(batches[1]) == 5
