import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.notification_repository import NotificationRepository


class NotificationService:
    """Creates the org-visible notifications for pipeline events (extraction,
    matching). Called from the Celery worker and the matching API — never decides
    business outcomes itself, just records that one happened.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._repo = NotificationRepository(db)

    async def notify_extraction_completed(
        self, *, org_id: uuid.UUID, project_id: uuid.UUID, document_name: str, doc_type: str
    ) -> None:
        kind = "RFP" if doc_type == "rfp" else "vendor proposal"
        await self._repo.create(
            org_id=org_id,
            project_id=project_id,
            type="extraction_completed",
            title="Extraction completed",
            message=f'Finished extracting the {kind} "{document_name}".',
        )

    async def notify_extraction_failed(
        self, *, org_id: uuid.UUID, project_id: uuid.UUID, document_name: str, error_message: str
    ) -> None:
        await self._repo.create(
            org_id=org_id,
            project_id=project_id,
            type="extraction_failed",
            title="Extraction failed",
            message=f'Extraction failed for "{document_name}": {error_message}',
        )

    async def notify_matching_completed(
        self, *, org_id: uuid.UUID, project_id: uuid.UUID, vendor_name: str, compliance_pct: float
    ) -> None:
        await self._repo.create(
            org_id=org_id,
            project_id=project_id,
            type="matching_completed",
            title="Matching completed",
            message=f"{vendor_name} matched at {compliance_pct:.1f}% compliance.",
        )
