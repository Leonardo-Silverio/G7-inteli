"""create anexos_checkpoint table

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "anexos_checkpoint",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("checkpoint_id", sa.Uuid(), nullable=False),
        sa.Column("nome_original", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("tamanho_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("enviado_por_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_anexos_checkpoint"),
        sa.ForeignKeyConstraint(
            ["checkpoint_id"],
            ["checkpoints.id"],
            name="fk_anexos_checkpoint_checkpoint_id_checkpoints",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["enviado_por_id"],
            ["usuarios.id"],
            name="fk_anexos_checkpoint_enviado_por_id_usuarios",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "tamanho_bytes >= 0",
            name="ck_anexo_tamanho_bytes_nao_negativo",
        ),
        sa.UniqueConstraint("storage_key", name="uq_anexo_storage_key"),
        sa.UniqueConstraint("checkpoint_id", "storage_key", name="uq_anexo_checkpoint_storage_key"),
    )

    op.create_index(
        "ix_anexos_checkpoint_checkpoint_id",
        "anexos_checkpoint",
        ["checkpoint_id"],
    )
    op.create_index(
        "ix_anexos_checkpoint_enviado_por_id",
        "anexos_checkpoint",
        ["enviado_por_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_anexos_checkpoint_enviado_por_id", table_name="anexos_checkpoint")
    op.drop_index("ix_anexos_checkpoint_checkpoint_id", table_name="anexos_checkpoint")
    op.drop_table("anexos_checkpoint")