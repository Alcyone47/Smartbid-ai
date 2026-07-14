"""extraction status lifecycle: queued/extracting/retrying/completed/failed

Revision ID: 0006_extraction_status_lifecycle
Revises: 0005_add_vendor_entity
Create Date: 2026-07-12

Renames the document status vocabulary so the UI can show a real extraction
lifecycle. Adds no columns — remaps existing values and changes the default.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0006_extraction_status_lifecycle"
down_revision: Union[str, None] = "0005_add_vendor_entity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# old -> new (failed is unchanged; retrying is new, only ever set at runtime)
_FORWARD = {"uploaded": "queued", "processing": "extracting", "extracted": "completed"}
_BACKWARD = {new: old for old, new in _FORWARD.items()}


def _remap(mapping: dict[str, str]) -> None:
    for src, dst in mapping.items():
        op.execute(f"UPDATE documents SET status = '{dst}' WHERE status = '{src}'")


def upgrade() -> None:
    op.alter_column("documents", "status", server_default="queued")
    _remap(_FORWARD)
    # An in-flight "retrying" row would be transient; normalize any to queued.
    op.execute("UPDATE documents SET status = 'queued' WHERE status = 'retrying'")


def downgrade() -> None:
    op.alter_column("documents", "status", server_default="uploaded")
    _remap(_BACKWARD)
