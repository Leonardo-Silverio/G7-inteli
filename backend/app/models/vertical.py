from __future__ import annotations

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.mixins import TimestampMixin, UUIDIdMixin


class Vertical(UUIDIdMixin, TimestampMixin, Base):
    __tablename__ = "verticals"

    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    usuarios: Mapped[list[Usuario]] = relationship(back_populates="vertical")
    projetos: Mapped[list[Projeto]] = relationship(back_populates="vertical")
