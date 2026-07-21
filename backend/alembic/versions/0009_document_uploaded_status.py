"""default documents to 'uploaded' before extraction is triggered

Revision ID: 0009_doc_uploaded_status
Revises: 0008_doc_structure_analysis
Create Date: 2026-07-17

A freshly uploaded document previously defaulted to "queued", making it look
like it was already waiting for the extraction worker. "queued" now means only
that the user has triggered extraction; the pre-trigger state is "uploaded".

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_doc_uploaded_status"
down_revision: Union[str, None] = "0008_doc_structure_analysis"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("documents", "status", server_default="uploaded")
    # Never-extracted documents still sitting at the old default become "uploaded".
    # In-flight/terminal states (extracting, retrying, completed, failed) are left
    # untouched.
    op.execute("UPDATE documents SET status = 'uploaded' WHERE status = 'queued'")


def downgrade() -> None:
    op.alter_column("documents", "status", server_default="queued")
    op.execute("UPDATE documents SET status = 'queued' WHERE status = 'uploaded'")
