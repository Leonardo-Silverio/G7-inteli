"""add feedback_json column to avaliacoes_checkpoint

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "avaliacoes_checkpoint",
        sa.Column("feedback_json", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("avaliacoes_checkpoint", "feedback_json")
