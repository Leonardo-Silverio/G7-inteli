from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.enums import ClassificacaoFarol, StatusCheckpoint, TipoCheckpoint
from app.models.mixins import TimestampMixin, UUIDIdMixin

if TYPE_CHECKING:
    from app.models.anexo_checkpoint import AnexoCheckpoint
    from app.models.projeto import Projeto


class Checkpoint(UUIDIdMixin, TimestampMixin, Base):
    __tablename__ = "checkpoints"
    __table_args__ = (
        UniqueConstraint("projeto_id", "tipo", name="uq_checkpoint_projeto_tipo"),
    )

    projeto_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projetos.id", name="fk_checkpoint_projeto"),
        nullable=False,
    )
    tipo: Mapped[TipoCheckpoint] = mapped_column(
        SQLEnum(TipoCheckpoint, name="tipo_checkpoint"),
        nullable=False,
    )
    status: Mapped[StatusCheckpoint] = mapped_column(
        SQLEnum(StatusCheckpoint, name="status_checkpoint"),
        default=StatusCheckpoint.PENDENTE,
        nullable=False,
    )
    sugerido_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    iniciado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    concluido_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    respostas_formulario: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    resumo_para_marketing: Mapped[str | None] = mapped_column(Text, nullable=True)

    projeto: Mapped[Projeto] = relationship(back_populates="checkpoints")
    avaliacoes: Mapped[list[AvaliacaoCheckpoint]] = relationship(
        back_populates="checkpoint",
        lazy="select",
        order_by="AvaliacaoCheckpoint.evaluated_at.desc()",
    )
    anexos: Mapped[list[AnexoCheckpoint]] = relationship(
        back_populates="checkpoint",
        cascade="all, delete-orphan",
    )


class AvaliacaoCheckpoint(UUIDIdMixin, TimestampMixin, Base):
    __tablename__ = "avaliacoes_checkpoint"
    __table_args__ = (
        CheckConstraint(
            "score_alinhamento IS NULL OR (score_alinhamento >= 0 AND score_alinhamento <= 100)",
            name="ck_avaliacao_score_alinhamento",
        ),
        CheckConstraint(
            "score_potencial IS NULL OR (score_potencial >= 0 AND score_potencial <= 100)",
            name="ck_avaliacao_score_potencial",
        ),
    )

    checkpoint_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("checkpoints.id", name="fk_avaliacao_checkpoint"),
        nullable=False,
    )
    score_alinhamento: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_potencial: Mapped[int | None] = mapped_column(Integer, nullable=True)
    classificacao_farol: Mapped[ClassificacaoFarol | None] = mapped_column(
        SQLEnum(ClassificacaoFarol, name="classificacao_farol"),
        nullable=True,
    )
    criterios_alinhamento: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    criterios_potencial: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    explicacoes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    feedback_geral: Mapped[str | None] = mapped_column(Text, nullable=True)
    resumo_para_marketing: Mapped[str | None] = mapped_column(Text, nullable=True)

    evaluation_engine: Mapped[str] = mapped_column(
        sa.String(100), nullable=False, default="farol-engine-v1"
    )
    modelo: Mapped[str] = mapped_column(sa.String(100), nullable=False, default="unknown")
    prompt_version: Mapped[str] = mapped_column(sa.String(100), nullable=False, default="unknown")
    criteria_version: Mapped[str] = mapped_column(sa.String(100), nullable=False, default="unknown")
    prompt_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False, default="")
    criteria_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False, default="")
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    checkpoint: Mapped[Checkpoint] = relationship(back_populates="avaliacoes")
