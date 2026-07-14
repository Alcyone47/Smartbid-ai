from app.services.project_status import (
    COMPLETED,
    DRAFT,
    IN_PROGRESS,
    IN_REVIEW,
    derive_project_status,
)


def test_no_documents_is_draft():
    assert (
        derive_project_status(has_documents=False, rfp_extracted=False, vendor_extracted=False, has_matrix=False)
        == DRAFT
    )


def test_uploaded_but_not_extracted_is_in_progress():
    assert (
        derive_project_status(has_documents=True, rfp_extracted=False, vendor_extracted=False, has_matrix=False)
        == IN_PROGRESS
    )


def test_only_rfp_extracted_is_in_progress():
    assert (
        derive_project_status(has_documents=True, rfp_extracted=True, vendor_extracted=False, has_matrix=False)
        == IN_PROGRESS
    )


def test_rfp_and_vendor_extracted_no_matrix_is_in_review():
    assert (
        derive_project_status(has_documents=True, rfp_extracted=True, vendor_extracted=True, has_matrix=False)
        == IN_REVIEW
    )


def test_matrix_present_is_completed():
    assert (
        derive_project_status(has_documents=True, rfp_extracted=True, vendor_extracted=True, has_matrix=True)
        == COMPLETED
    )
