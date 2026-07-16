"""add evaluation audit fields

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop unique constraint on checkpoint_id to allow multiple evaluations per checkpoint
    op.drop_constraint("uq_avaliacao_checkpoint", "avaliacoes_checkpoint", type_="unique")

    # Add audit fields
    op.add_column(
        "avaliacoes_checkpoint",
        sa.Column("evaluation_engine", sa.String(100), nullable=False, server_default="farol-engine-v1"),
    )
    op.add_column(
        "avaliacoes_checkpoint",
        sa.Column("modelo", sa.String(100), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "avaliacoes_checkpoint",
        sa.Column("prompt_version", sa.String(100), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "avaliacoes_checkpoint",
        sa.Column("criteria_version", sa.String(100), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "avaliacoes_checkpoint",
        sa.Column("prompt_hash", sa.String(64), nullable=False, server_default=""),
    )
    op.add_column(
        "avaliacoes_checkpoint",
        sa.Column("criteria_hash", sa.String(64), nullable=False, server_default=""),
    )
    op.add_column(
        "avaliacoes_checkpoint",
        sa.Column(
            "evaluated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "avaliacoes_checkpoint",
        sa.Column("feedback_geral", sa.Text(), nullable=True),
    )
    op.add_column(
        "avaliacoes_checkpoint",
        sa.Column("resumo_para_marketing", sa.Text(), nullable=True),
    )

    # Create composite index for efficient latest evaluation queries
    op.create_index(
        "ix_avaliacao_checkpoint_evaluated_at",
        "avaliacoes_checkpoint",
        ["checkpoint_id", "evaluated_at"],
        postgresql_using="btree",
        postgresql_ops={"evaluated_at": "DESC"},
    )


def downgrade() -> None:
    op.drop_index("ix_avaliacao_checkpoint_evaluated_at", table_name="avaliacoes_checkpoint")
    op.drop_column("avaliacoes_checkpoint", "resumo_para_marketing")
    op.drop_column("avaliacoes_checkpoint", "feedback_geral")
    op.drop_column("avaliacoes_checkpoint", "evaluated_at")
    op.drop_column("avaliacoes_checkpoint", "criteria_hash")
    op.drop_column("avaliacoes_checkpoint", "prompt_hash")
    op.drop_column("avaliacoes_checkpoint", "criteria_version")
    op.drop_column("avaliacoes_checkpoint", "prompt_version")
    op.drop_column("avaliacoes_checkpoint", "modelo")
    op.drop_column("avaliacoes_checkpoint", "evaluation_engine")
    op.create_unique_constraint("uq_avaliacao_checkpoint", "avaliacoes_checkpoint", ["checkpoint_id"])