from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.enums import PapelUsuario
from app.models.mixins import TimestampMixin, UUIDIdMixin


class Usuario(UUIDIdMixin, TimestampMixin, Base):
    __tablename__ = "usuarios"

    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    papel: Mapped[PapelUsuario] = mapped_column(
        SQLEnum(PapelUsuario, name="papel_usuario"),
        nullable=False,
    )
    vertical_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("verticals.id", name="fk_usuario_vertical"),
        nullable=True,
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    vertical: Mapped[Vertical | None] = relationship(back_populates="usuarios")
    projetos_criados: Mapped[list[Projeto]] = relationship(back_populates="criador")
