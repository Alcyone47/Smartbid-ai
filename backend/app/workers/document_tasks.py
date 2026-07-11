import asyncio
import uuid

from app.config import settings
from app.core.celery_app import celery_app
from app.core.exceptions import UnsupportedDocumentTypeError
from app.core.llm.factory import get_llm_provider
from app.db.session import async_session_maker
from app.models.extraction import ExtractedRequirement, ExtractedSpecification
from app.repositories.document_repository import DocumentRepository
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.specification_repository import SpecificationRepository
from app.services.extraction_service import ExtractionService
from app.services.storage import download_document


async def _process_document_async(document_id: str) -> None:
    async with async_session_maker() as db:
        document_repo = DocumentRepository(db)
        document = await document_repo.get_by_id_unscoped(uuid.UUID(document_id))

        try:
            content = await download_document(settings.supabase_storage_bucket, document.storage_path)
            extraction_service = ExtractionService(llm_provider=get_llm_provider())

            if document.doc_type == "rfp":
                outcome = await extraction_service.extract_requirements(content, document.mime_type)
                requirement_repo = RequirementRepository(db)
                requirements = [
                    ExtractedRequirement(
                        org_id=document.org_id,
                        document_id=document.id,
                        project_id=document.project_id,
                        requirement_key=item.requirement_key,
                        requirement_label=item.requirement_label,
                        category=item.category,
                        requirement_text=item.requirement_text,
                        expected_value=item.expected_value,
                        unit=item.unit,
                        operator=item.operator,
                        is_mandatory=item.is_mandatory,
                        source_page=item.source_page,
                        raw_llm_response=outcome.raw_response,
                    )
                    for item in outcome.result.requirements
                ]
                await requirement_repo.bulk_create(requirements)
            elif document.doc_type == "vendor_proposal":
                outcome = await extraction_service.extract_specifications(content, document.mime_type)
                specification_repo = SpecificationRepository(db)
                specifications = [
                    ExtractedSpecification(
                        org_id=document.org_id,
                        document_id=document.id,
                        project_id=document.project_id,
                        vendor_name=document.vendor_name,
                        spec_key=item.spec_key,
                        spec_label=item.spec_label,
                        spec_text=item.spec_text,
                        value=item.value,
                        unit=item.unit,
                        source_page=item.source_page,
                        raw_llm_response=outcome.raw_response,
                    )
                    for item in outcome.result.specifications
                ]
                await specification_repo.bulk_create(specifications)
            else:
                raise UnsupportedDocumentTypeError(f"Unsupported doc_type for extraction: {document.doc_type}")

            await document_repo.update_page_count(document, outcome.page_count)
            await document_repo.update_status(document, status="extracted")
        except Exception as exc:
            await document_repo.update_status(document, status="failed", error_message=str(exc))
            raise


@celery_app.task(name="process_document")
def process_document(document_id: str) -> None:
    asyncio.run(_process_document_async(document_id))
