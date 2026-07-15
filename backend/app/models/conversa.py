from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.enums import AutorMensagem
from app.models.mixins import TimestampMixin, UUIDIdMixin


class Conversa(UUIDIdMixin, TimestampMixin, Base):
    __tablename__ = "conversas"

    projeto_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projetos.id", name="fk_conversa_projeto"),
        unique=True,
        nullable=False,
    )

    projeto: Mapped[Projeto] = relationship(back_populates="conversa")
    mensagens: Mapped[list[Mensagem]] = relationship(back_populates="conversa")


class Mensagem(UUIDIdMixin, Base):
    __tablename__ = "mensagens"

    conversa_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversas.id", name="fk_mensagem_conversa"),
        nullable=False,
    )
    autor_tipo: Mapped[AutorMensagem] = mapped_column(
        SQLEnum(AutorMensagem, name="autor_mensagem"),
        nullable=False,
    )
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", name="fk_mensagem_usuario"),
        nullable=True,
    )
    conteudo: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    conversa: Mapped[Conversa] = relationship(back_populates="mensagens")
