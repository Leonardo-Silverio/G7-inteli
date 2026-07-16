from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.models.mixins import TimestampMixin, UUIDIdMixin

if TYPE_CHECKING:
    from app.models.checkpoint import Checkpoint
    from app.models.usuario import Usuario


class AnexoCheckpoint(UUIDIdMixin, Base):
    __tablename__ = "anexos_checkpoint"
    __table_args__ = (
        CheckConstraint(
            "tamanho_bytes >= 0",
            name="ck_anexo_tamanho_bytes_nao_negativo",
        ),
        UniqueConstraint(
            "storage_key",
            name="uq_anexo_storage_key",
        ),
        UniqueConstraint(
            "checkpoint_id",
            "storage_key",
            name="uq_anexo_checkpoint_storage_key",
        ),
    )

    checkpoint_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("checkpoints.id", name="fk_anexo_checkpoint", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nome_original: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    tamanho_bytes: Mapped[int] = mapped_column(nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    enviado_por_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", name="fk_anexo_enviado_por", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    checkpoint: Mapped[Checkpoint] = relationship(
        back_populates="anexos",
    )
    enviado_por: Mapped[Usuario] = relationship()