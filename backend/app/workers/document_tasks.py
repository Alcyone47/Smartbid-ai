import asyncio
import uuid

from app.config import settings
from app.core.celery_app import celery_app
from app.core.exceptions import LLMRateLimitError, UnsupportedDocumentTypeError
from app.core.llm.backoff import compute_backoff
from app.core.llm.factory import get_llm_provider
from app.db.session import async_session_maker, engine
from app.models.extraction import ExtractedSpecification, Requirement, RequirementParameter
from app.repositories.document_repository import DocumentRepository
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.specification_repository import SpecificationRepository
from app.services.extraction_service import ExtractionService
from app.services.storage import download_document


async def _process_document_async(document_id: str) -> None:
    async with async_session_maker() as db:
        document_repo = DocumentRepository(db)
        document = await document_repo.get_by_id_unscoped(uuid.UUID(document_id))
        # Transition Queued -> Extracting as soon as the worker picks the job up.
        await document_repo.update_status(document, status="extracting", progress=0)

        async def on_progress(done: int, total: int) -> None:
            # Cap below 100 during batches; 100 is set only once the row is fully persisted.
            pct = min(95, round(done / total * 95)) if total else 0
            await document_repo.update_progress(document, pct)

        # Status on failure is decided by the Celery task (retrying vs failed), so
        # exceptions propagate rather than being swallowed here.
        content = await download_document(settings.supabase_storage_bucket, document.storage_path)
        extraction_service = ExtractionService(llm_provider=get_llm_provider())

        if document.doc_type == "rfp":
            outcome = await extraction_service.extract_requirements(
                content, document.mime_type, progress_callback=on_progress
            )
            requirement_repo = RequirementRepository(db)
            requirements = [
                Requirement(
                    org_id=document.org_id,
                    document_id=document.id,
                    project_id=document.project_id,
                    # The LLM's requirement_key/label identify the equipment/item.
                    equipment_key=item.requirement_key,
                    equipment_label=item.requirement_label,
                    category=item.category,
                    source_page=item.source_page,
                    raw_llm_response=outcome.raw_response,
                    parameters=[
                        RequirementParameter(
                            org_id=document.org_id,
                            document_id=document.id,
                            project_id=document.project_id,
                            equipment_key=item.requirement_key,
                            equipment_label=item.requirement_label,
                            category=item.category,
                            parameter_key=param.parameter_key,
                            parameter_label=param.parameter_label,
                            parameter_text=param.parameter_text,
                            expected_value=param.expected_value,
                            unit=param.unit,
                            operator=param.operator,
                            is_mandatory=param.is_mandatory,
                            source_page=param.source_page,
                        )
                        for param in item.parameters
                    ],
                )
                for item in outcome.result.requirements
            ]
            await requirement_repo.delete_by_document(document.id)
            await requirement_repo.bulk_create(requirements)
            await document_repo.update_structure_analysis(document, outcome.structure_analysis)
        elif document.doc_type == "vendor_proposal":
            outcome = await extraction_service.extract_specifications(
                content, document.mime_type, progress_callback=on_progress
            )
            specification_repo = SpecificationRepository(db)
            specifications = [
                ExtractedSpecification(
                    org_id=document.org_id,
                    document_id=document.id,
                    project_id=document.project_id,
                    vendor_name=document.vendor_name,
                    vendor_id=document.vendor_id,
                    equipment_key=item.equipment_key,
                    equipment_label=item.equipment_label,
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
            await specification_repo.delete_by_document(document.id)
            await specification_repo.bulk_create(specifications)
        else:
            raise UnsupportedDocumentTypeError(f"Unsupported doc_type for extraction: {document.doc_type}")

        await document_repo.update_page_count(document, outcome.page_count)
        await document_repo.update_status(document, status="completed", progress=100)


async def _run_task(document_id: str) -> None:
    # Each Celery task runs in its own event loop via asyncio.run(). The shared
    # async engine caches asyncpg connections bound to the loop that created them,
    # so dispose the pool at the end of every task — otherwise the next task gets a
    # connection tied to an already-closed loop ("Event loop is closed").
    try:
        await _process_document_async(document_id)
    finally:
        await engine.dispose()


async def _set_status(document_id: str, status: str, error_message: str | None = None) -> None:
    """Standalone status write used from the task's exception handlers (runs in its own
    event loop / session after the main task's engine was disposed)."""
    try:
        async with async_session_maker() as db:
            repo = DocumentRepository(db)
            document = await repo.get_by_id_unscoped(uuid.UUID(document_id))
            await repo.update_status(document, status=status, error_message=error_message)
    finally:
        await engine.dispose()


@celery_app.task(bind=True, name="process_document", max_retries=settings.extraction_max_retries)
def process_document(self, document_id: str) -> None:
    try:
        asyncio.run(_run_task(document_id))
    except LLMRateLimitError as exc:
        # Transient rate limit: re-queue the whole job (status "Retrying") unless we've
        # run out of attempts, honoring the server's suggested delay when provided.
        if self.request.retries >= settings.extraction_max_retries:
            asyncio.run(_set_status(document_id, "failed", error_message=f"Rate limited: {exc.message}"))
            raise
        attempt = self.request.retries + 1
        asyncio.run(
            _set_status(
                document_id,
                "retrying",
                error_message=f"Rate limited — retrying ({attempt}/{settings.extraction_max_retries})",
            )
        )
        countdown = exc.retry_after or compute_backoff(
            self.request.retries,
            settings.extraction_retry_base_delay,
            settings.extraction_retry_max_delay,
        )
        raise self.retry(exc=exc, countdown=countdown)
    except Exception as exc:
        asyncio.run(_set_status(document_id, "failed", error_message=str(exc)))
        raise
