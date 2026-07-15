from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.enums import DecisaoHumana, StatusAlerta, TipoAlerta
from app.models.mixins import TimestampMixin, UUIDIdMixin


class Alerta(UUIDIdMixin, TimestampMixin, Base):
    __tablename__ = "alertas"

    projeto_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projetos.id", name="fk_alerta_projeto"),
        nullable=False,
    )
    checkpoint_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("checkpoints.id", name="fk_alerta_checkpoint"),
        nullable=True,
    )
    tipo: Mapped[TipoAlerta] = mapped_column(
        SQLEnum(TipoAlerta, name="tipo_alerta"),
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[StatusAlerta] = mapped_column(
        SQLEnum(StatusAlerta, name="status_alerta"),
        default=StatusAlerta.ABERTO,
        nullable=False,
    )
    decisao_humana: Mapped[DecisaoHumana | None] = mapped_column(
        SQLEnum(DecisaoHumana, name="decisao_humana"),
        nullable=True,
    )
    decidido_por_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", name="fk_alerta_decidido_por"),
        nullable=True,
    )
    decidido_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    projeto: Mapped[Projeto] = relationship(back_populates="alertas")
    checkpoint: Mapped[Checkpoint | None] = relationship()
    decidido_por: Mapped[Usuario | None] = relationship()
