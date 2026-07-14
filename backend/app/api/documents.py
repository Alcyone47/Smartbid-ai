import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.projects import _get_org_project
from app.config import settings
from app.db.session import get_db
from app.dependencies import CurrentUser, get_current_org_user
from app.models.document import Document
from app.repositories.vendor_repository import VendorRepository
from app.schemas.document import DocType, DocumentRead
from app.services.storage import build_storage_path, upload_document

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])


@router.get("", response_model=list[DocumentRead])
async def list_documents(
    project_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> list[Document]:
    await _get_org_project(project_id, current_user.org_id, db)
    result = await db.execute(
        select(Document).where(Document.project_id == project_id).order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_project_document(
    project_id: uuid.UUID,
    doc_type: DocType = Form(...),
    vendor_name: str | None = Form(None),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> Document:
    await _get_org_project(project_id, current_user.org_id, db)

    if doc_type == "vendor_proposal" and not vendor_name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="vendor_name is required for vendor proposals")

    # A vendor may own multiple PDFs: reuse the vendor with this name or create it.
    vendor_id = None
    if doc_type == "vendor_proposal" and vendor_name:
        vendor = await VendorRepository(db).get_or_create(current_user.org_id, project_id, vendor_name.strip())
        vendor_id = vendor.id

    content = await file.read()
    storage_path = build_storage_path(current_user.org_id, project_id, file.filename or "document")
    await upload_document(settings.supabase_storage_bucket, storage_path, content, file.content_type or "application/octet-stream")

    document = Document(
        org_id=current_user.org_id,
        project_id=project_id,
        doc_type=doc_type,
        vendor_name=vendor_name,
        vendor_id=vendor_id,
        storage_path=storage_path,
        original_filename=file.filename or "document",
        mime_type=file.content_type or "application/octet-stream",
        uploaded_by=current_user.user_id,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> Document:
    await _get_org_project(project_id, current_user.org_id, db)
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.project_id == project_id)
    )
    document = result.scalars().first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await _get_org_project(project_id, current_user.org_id, db)
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.project_id == project_id)
    )
    document = result.scalars().first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await db.delete(document)
    await db.commit()
