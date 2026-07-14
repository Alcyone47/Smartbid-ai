"""Deterministic project-status derivation.

Project status is not stored/managed manually — it is derived from the project's
documents and compliance state each time projects are read, so it can never drift
out of sync with actual progress. Pure logic, no DB or LLM.

Lifecycle:
    draft        no documents uploaded yet
    in_progress  documents uploaded, but the RFP and at least one vendor proposal
                 have not both finished extraction
    in_review    RFP + at least one vendor extracted, no compliance matrix yet
    completed    a compliance matrix has been generated
"""

from __future__ import annotations

DRAFT = "draft"
IN_PROGRESS = "in_progress"
IN_REVIEW = "in_review"
COMPLETED = "completed"


def derive_project_status(
    *,
    has_documents: bool,
    rfp_extracted: bool,
    vendor_extracted: bool,
    has_matrix: bool,
) -> str:
    """Map concrete progress signals to a project lifecycle status."""
    if not has_documents:
        return DRAFT
    # A matrix can only exist once extraction ran, so it implies "results are ready".
    if has_matrix:
        return COMPLETED
    if rfp_extracted and vendor_extracted:
        return IN_REVIEW
    return IN_PROGRESS
