import uuid

from supabase import Client, create_client

from app.config import settings

_client: Client | None = None


def get_storage_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _client


def build_storage_path(org_id: uuid.UUID, project_id: uuid.UUID, filename: str) -> str:
    return f"{org_id}/{project_id}/{uuid.uuid4()}-{filename}"


async def upload_document(bucket: str, storage_path: str, content: bytes, mime_type: str) -> None:
    client = get_storage_client()
    client.storage.from_(bucket).upload(
        storage_path,
        content,
        file_options={"content-type": mime_type},
    )
