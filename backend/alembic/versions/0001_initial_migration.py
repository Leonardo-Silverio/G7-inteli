"""initial migration

Revision ID: 0001
Revises:
Create Date: 2026-07-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- verticals ---
    op.create_table(
        "verticals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("ativa", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_verticals"),
        sa.UniqueConstraint("nome", name="uq_vertical_nome"),
    )

    # --- usuarios ---
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("senha_hash", sa.String(255), nullable=False),
        sa.Column(
            "papel",
            sa.Enum("VERTICAL", "MARKETING", "LIDERANCA", "ADMIN",
                    name="papel_usuario"),
            nullable=False,
        ),
        sa.Column("vertical_id", sa.Uuid(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_usuarios"),
        sa.UniqueConstraint("email", name="uq_usuario_email"),
        sa.ForeignKeyConstraint(["vertical_id"], ["verticals.id"],
                                name="fk_usuarios_vertical_id_verticals"),
    )

    # --- projetos ---
    op.create_table(
        "projetos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("objetivo", sa.Text(), nullable=True),
        sa.Column("vertical_id", sa.Uuid(), nullable=False),
        sa.Column("criado_por_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("RASCUNHO", "IDEACAO", "DESENVOLVIMENTO", "PRE_LANCAMENTO",
                    "APROVADO", "ADAPTACAO_SOLICITADA", "ENCERRADO", "LANCADO",
                    name="status_projeto", ),
            nullable=False, server_default="RASCUNHO",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_projetos"),
        sa.ForeignKeyConstraint(["vertical_id"], ["verticals.id"],
                                name="fk_projetos_vertical_id_verticals"),
        sa.ForeignKeyConstraint(["criado_por_id"], ["usuarios.id"],
                                name="fk_projetos_criado_por_id_usuarios"),
    )

    # --- checkpoints ---
    op.create_table(
        "checkpoints",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("projeto_id", sa.Uuid(), nullable=False),
        sa.Column(
            "tipo",
            sa.Enum("IDEACAO", "DESENVOLVIMENTO", "PRE_LANCAMENTO",
                    name="tipo_checkpoint", ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("PENDENTE", "SUGERIDO", "EM_PREENCHIMENTO", "CONCLUIDO",
                    name="status_checkpoint", ),
            nullable=False, server_default="PENDENTE",
        ),
        sa.Column("sugerido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("iniciado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("concluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("respostas_formulario", sa.JSON(), nullable=True),
        sa.Column("resumo_para_marketing", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_checkpoints"),
        sa.ForeignKeyConstraint(["projeto_id"], ["projetos.id"],
                                name="fk_checkpoints_projeto_id_projetos"),
        sa.UniqueConstraint("projeto_id", "tipo", name="uq_checkpoint_projeto_tipo"),
    )

    # --- avaliacoes_checkpoint ---
    op.create_table(
        "avaliacoes_checkpoint",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("checkpoint_id", sa.Uuid(), nullable=False),
        sa.Column("score_alinhamento", sa.Integer(), nullable=True),
        sa.Column("score_potencial", sa.Integer(), nullable=True),
        sa.Column(
            "classificacao_farol",
            sa.Enum("PRIORIDADE_MAXIMA", "VALE_INVESTIR_TEMPO", "BAIXA_PRIORIDADE",
                    name="classificacao_farol", ),
            nullable=True,
        ),
        sa.Column("criterios_alinhamento", sa.JSON(), nullable=True),
        sa.Column("criterios_potencial", sa.JSON(), nullable=True),
        sa.Column("explicacoes", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_avaliacoes_checkpoint"),
        sa.ForeignKeyConstraint(["checkpoint_id"], ["checkpoints.id"],
                                name="fk_avaliacoes_checkpoint_id_checkpoints"),
        sa.UniqueConstraint("checkpoint_id", name="uq_avaliacao_checkpoint"),
        sa.CheckConstraint(
            "score_alinhamento IS NULL OR (score_alinhamento >= 0 AND score_alinhamento <= 100)",
            name="ck_avaliacao_score_alinhamento",
        ),
        sa.CheckConstraint(
            "score_potencial IS NULL OR (score_potencial >= 0 AND score_potencial <= 100)",
            name="ck_avaliacao_score_potencial",
        ),
    )

    # --- alertas ---
    op.create_table(
        "alertas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("projeto_id", sa.Uuid(), nullable=False),
        sa.Column("checkpoint_id", sa.Uuid(), nullable=True),
        sa.Column(
            "tipo",
            sa.Enum("COMPLIANCE_LEGAL", "REPUTACAO_MARCA", "POSSIVEL_DUPLICACAO",
                    "CUSTO_DESPROPORCIONAL", "OUTRO",
                    name="tipo_alerta", ),
            nullable=False,
        ),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ABERTO", "EM_ANALISE", "RESOLVIDO", "DESCARTADO",
                    name="status_alerta", ),
            nullable=False, server_default="ABERTO",
        ),
        sa.Column(
            "decisao_humana",
            sa.Enum("SOLICITAR_ADAPTACAO", "ENCERRAR_PROJETO", "PERMITIR_CONTINUIDADE",
                    name="decisao_humana", ),
            nullable=True,
        ),
        sa.Column("decidido_por_id", sa.Uuid(), nullable=True),
        sa.Column("decidido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_alertas"),
        sa.ForeignKeyConstraint(["projeto_id"], ["projetos.id"],
                                name="fk_alertas_projeto_id_projetos"),
        sa.ForeignKeyConstraint(["checkpoint_id"], ["checkpoints.id"],
                                name="fk_alertas_checkpoint_id_checkpoints"),
        sa.ForeignKeyConstraint(["decidido_por_id"], ["usuarios.id"],
                                name="fk_alertas_decidido_por_id_usuarios"),
    )

    # --- conversas ---
    op.create_table(
        "conversas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("projeto_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_conversas"),
        sa.ForeignKeyConstraint(["projeto_id"], ["projetos.id"],
                                name="fk_conversas_projeto_id_projetos"),
        sa.UniqueConstraint("projeto_id", name="uq_conversa_projeto"),
    )

    # --- mensagens ---
    op.create_table(
        "mensagens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversa_id", sa.Uuid(), nullable=False),
        sa.Column(
            "autor_tipo",
            sa.Enum("USUARIO", "AGENTE", "SISTEMA",
                    name="autor_mensagem", ),
            nullable=False,
        ),
        sa.Column("usuario_id", sa.Uuid(), nullable=True),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_mensagens"),
        sa.ForeignKeyConstraint(["conversa_id"], ["conversas.id"],
                                name="fk_mensagens_conversa_id_conversas"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"],
                                name="fk_mensagens_usuario_id_usuarios"),
    )

    # indexes
    op.create_index("ix_usuarios_email", "usuarios", ["email"])
    op.create_index("ix_projetos_vertical_id", "projetos", ["vertical_id"])
    op.create_index("ix_projetos_criado_por_id", "projetos", ["criado_por_id"])
    op.create_index("ix_checkpoints_projeto_id", "checkpoints", ["projeto_id"])
    op.create_index("ix_alertas_projeto_id", "alertas", ["projeto_id"])
    op.create_index("ix_mensagens_conversa_id", "mensagens", ["conversa_id"])


def downgrade() -> None:
    # drop indexes
    op.drop_index("ix_mensagens_conversa_id", table_name="mensagens")
    op.drop_index("ix_alertas_projeto_id", table_name="alertas")
    op.drop_index("ix_checkpoints_projeto_id", table_name="checkpoints")
    op.drop_index("ix_projetos_criado_por_id", table_name="projetos")
    op.drop_index("ix_projetos_vertical_id", table_name="projetos")
    op.drop_index("ix_usuarios_email", table_name="usuarios")

    # drop tables (reverse dependency order)
    op.drop_table("mensagens")
    op.drop_table("conversas")
    op.drop_table("alertas")
    op.drop_table("avaliacoes_checkpoint")
    op.drop_table("checkpoints")
    op.drop_table("projetos")
    op.drop_table("usuarios")
    op.drop_table("verticals")

    # drop enum types
    op.execute("DROP TYPE IF EXISTS autor_mensagem")
    op.execute("DROP TYPE IF EXISTS decisao_humana")
    op.execute("DROP TYPE IF EXISTS status_alerta")
    op.execute("DROP TYPE IF EXISTS tipo_alerta")
    op.execute("DROP TYPE IF EXISTS classificacao_farol")
    op.execute("DROP TYPE IF EXISTS status_checkpoint")
    op.execute("DROP TYPE IF EXISTS tipo_checkpoint")
    op.execute("DROP TYPE IF EXISTS status_projeto")
    op.execute("DROP TYPE IF EXISTS papel_usuario")
