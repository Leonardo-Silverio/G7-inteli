"""update status projeto enum

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OLD_VALUES = [
    "RASCUNHO",
    "IDEACAO",
    "DESENVOLVIMENTO",
    "PRE_LANCAMENTO",
    "APROVADO",
    "ADAPTACAO_SOLICITADA",
    "ENCERRADO",
    "LANCADO",
]

NEW_VALUES = [
    "EM_IDEACAO",
    "EM_DESENVOLVIMENTO",
    "AGUARDANDO_PRE_LANCAMENTO",
    "APROVADO_PARA_LANCAMENTO",
    "LANCADO",
    "EM_ALERTA",
    "ENCERRADO",
]

# Mapping from old to new values
MAPPING = {
    "RASCUNHO": "EM_IDEACAO",
    "IDEACAO": "EM_IDEACAO",
    "DESENVOLVIMENTO": "EM_DESENVOLVIMENTO",
    "PRE_LANCAMENTO": "AGUARDANDO_PRE_LANCAMENTO",
    "APROVADO": "APROVADO_PARA_LANCAMENTO",
    "ADAPTACAO_SOLICITADA": "EM_ALERTA",
    "ENCERRADO": "ENCERRADO",
    "LANCADO": "LANCADO",
}

# Reverse mapping for downgrade (best effort - multiple old values map to same new)
REVERSE_MAPPING = {
    "EM_IDEACAO": "RASCUNHO",  # or IDEACAO, using RASCUNHO as default
    "EM_DESENVOLVIMENTO": "DESENVOLVIMENTO",
    "AGUARDANDO_PRE_LANCAMENTO": "PRE_LANCAMENTO",
    "APROVADO_PARA_LANCAMENTO": "APROVADO",
    "LANCADO": "LANCADO",
    "EM_ALERTA": "ADAPTACAO_SOLICITADA",
    "ENCERRADO": "ENCERRADO",
}


def upgrade() -> None:
    # Create new enum type
    op.execute(
        "CREATE TYPE status_projeto_new AS ENUM ("
        "'EM_IDEACAO', "
        "'EM_DESENVOLVIMENTO', "
        "'AGUARDANDO_PRE_LANCAMENTO', "
        "'APROVADO_PARA_LANCAMENTO', "
        "'LANCADO', "
        "'EM_ALERTA', "
        "'ENCERRADO'"
        ")"
    )

    # Add temporary column with new enum type
    op.add_column(
        "projetos",
        sa.Column("status_new", sa.Enum(*NEW_VALUES, name="status_projeto_new"), nullable=True)
    )

    # Populate temporary column with mapped values
    for old_val, new_val in MAPPING.items():
        op.execute(
            f"UPDATE projetos SET status_new = '{new_val}' WHERE status = '{old_val}'"
        )

    # Drop default from old column
    op.execute("ALTER TABLE projetos ALTER COLUMN status DROP DEFAULT")

    # Drop old column
    op.drop_column("projetos", "status")

    # Rename temporary column to status
    op.alter_column("projetos", "status_new", new_column_name="status")

    # Drop old enum and rename new
    op.execute("DROP TYPE status_projeto")
    op.execute("ALTER TYPE status_projeto_new RENAME TO status_projeto")

    # Set default for new column
    op.execute(
        "ALTER TABLE projetos ALTER COLUMN status SET DEFAULT 'EM_IDEACAO'"
    )


def downgrade() -> None:
    # Create old enum type
    op.execute(
        "CREATE TYPE status_projeto_old AS ENUM ("
        "'RASCUNHO', "
        "'IDEACAO', "
        "'DESENVOLVIMENTO', "
        "'PRE_LANCAMENTO', "
        "'APROVADO', "
        "'ADAPTACAO_SOLICITADA', "
        "'ENCERRADO', "
        "'LANCADO'"
        ")"
    )

    # Add temporary column with old enum type
    op.add_column(
        "projetos",
        sa.Column("status_old", sa.Enum(*OLD_VALUES, name="status_projeto_old"), nullable=True)
    )

    # Populate temporary column with reverse mapped values
    for new_val, old_val in REVERSE_MAPPING.items():
        op.execute(
            f"UPDATE projetos SET status_old = '{old_val}' WHERE status = '{new_val}'"
        )

    # Drop default from current column
    op.execute("ALTER TABLE projetos ALTER COLUMN status DROP DEFAULT")

    # Drop current column
    op.drop_column("projetos", "status")

    # Rename temporary column to status
    op.alter_column("projetos", "status_old", new_column_name="status")

    # Drop new enum and rename old
    op.execute("DROP TYPE status_projeto")
    op.execute("ALTER TYPE status_projeto_old RENAME TO status_projeto")

    # Restore default value
    op.execute(
        "ALTER TABLE projetos ALTER COLUMN status SET DEFAULT 'RASCUNHO'"
    )