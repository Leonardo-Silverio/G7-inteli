from __future__ import annotations

import uuid

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.enums import StatusProjeto
from app.models.mixins import TimestampMixin, UUIDIdMixin


class Projeto(UUIDIdMixin, TimestampMixin, Base):
    __tablename__ = "projetos"

    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    objetivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    vertical_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("verticals.id", name="fk_projeto_vertical"),
        nullable=False,
    )
    criado_por_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", name="fk_projeto_criador"),
        nullable=False,
    )
    status: Mapped[StatusProjeto] = mapped_column(
        SQLEnum(StatusProjeto, name="status_projeto"),
        default=StatusProjeto.EM_IDEACAO,
        nullable=False,
    )

    vertical: Mapped[Vertical] = relationship(back_populates="projetos")
    criador: Mapped[Usuario] = relationship(back_populates="projetos_criados")
    checkpoints: Mapped[list[Checkpoint]] = relationship(back_populates="projeto")
    alertas: Mapped[list[Alerta]] = relationship(back_populates="projeto")
    conversa: Mapped[Conversa | None] = relationship(
        back_populates="projeto", uselist=False,
    )
