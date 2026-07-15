from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.enums import ClassificacaoFarol, StatusCheckpoint, TipoCheckpoint
from app.models.mixins import TimestampMixin, UUIDIdMixin


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
    avaliacao: Mapped[AvaliacaoCheckpoint | None] = relationship(
        back_populates="checkpoint", uselist=False,
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
        unique=True,
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

    checkpoint: Mapped[Checkpoint] = relationship(back_populates="avaliacao")
