from uuid import UUID
from typing import Optional
from sqlalchemy import func, case
from sqlalchemy.orm import Session, joinedload

from app.models.checkpoint import Checkpoint
from app.models.anexo_checkpoint import AnexoCheckpoint
from app.models.enums import TipoCheckpoint


class CheckpointRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
        self.db.add(checkpoint)
        self.db.flush()
        return checkpoint

    def get_checkpoint_by_id(self, checkpoint_id: UUID) -> Checkpoint | None:
        return (
            self.db.query(Checkpoint)
            .filter(Checkpoint.id == checkpoint_id)
            .first()
        )

    def get_checkpoint_with_attachments(self, checkpoint_id: UUID) -> Checkpoint | None:
        return (
            self.db.query(Checkpoint)
            .options(joinedload(Checkpoint.anexos))
            .filter(Checkpoint.id == checkpoint_id)
            .first()
        )

    def get_checkpoint_by_projeto_and_tipo(
        self, projeto_id: UUID, tipo: TipoCheckpoint
    ) -> Checkpoint | None:
        return (
            self.db.query(Checkpoint)
            .filter(Checkpoint.projeto_id == projeto_id, Checkpoint.tipo == tipo)
            .first()
        )

    def list_checkpoints_by_projeto(self, projeto_id: UUID) -> list[Checkpoint]:
        tipo_order = case(
            (Checkpoint.tipo == TipoCheckpoint.IDEACAO, 1),
            (Checkpoint.tipo == TipoCheckpoint.DESENVOLVIMENTO, 2),
            (Checkpoint.tipo == TipoCheckpoint.PRE_LANCAMENTO, 3),
            else_=4,
        )
        return (
            self.db.query(Checkpoint)
            .filter(Checkpoint.projeto_id == projeto_id)
            .order_by(tipo_order, Checkpoint.created_at.asc())
            .all()
        )

    def update_checkpoint(
        self, checkpoint: Checkpoint, updates: dict[str, object]
    ) -> Checkpoint:
        for key, value in updates.items():
            if hasattr(checkpoint, key):
                setattr(checkpoint, key, value)
        self.db.flush()
        return checkpoint

    def count_checkpoints_by_projeto(self, projeto_id: UUID) -> int:
        return (
            self.db.query(func.count(Checkpoint.id))
            .filter(Checkpoint.projeto_id == projeto_id)
            .scalar()
        )

    def create_attachment(self, attachment: AnexoCheckpoint) -> AnexoCheckpoint:
        self.db.add(attachment)
        self.db.flush()
        return attachment

    def get_attachment_by_id(self, attachment_id: UUID) -> AnexoCheckpoint | None:
        return (
            self.db.query(AnexoCheckpoint)
            .filter(AnexoCheckpoint.id == attachment_id)
            .first()
        )

    def get_attachment_by_id_and_checkpoint(
        self, attachment_id: UUID, checkpoint_id: UUID
    ) -> AnexoCheckpoint | None:
        return (
            self.db.query(AnexoCheckpoint)
            .filter(
                AnexoCheckpoint.id == attachment_id,
                AnexoCheckpoint.checkpoint_id == checkpoint_id,
            )
            .first()
        )

    def list_attachments_by_checkpoint(
        self, checkpoint_id: UUID
    ) -> list[AnexoCheckpoint]:
        return (
            self.db.query(AnexoCheckpoint)
            .filter(AnexoCheckpoint.checkpoint_id == checkpoint_id)
            .order_by(AnexoCheckpoint.created_at.asc(), AnexoCheckpoint.id.asc())
            .all()
        )

    def count_attachments_by_checkpoint(self, checkpoint_id: UUID) -> int:
        return (
            self.db.query(func.count(AnexoCheckpoint.id))
            .filter(AnexoCheckpoint.checkpoint_id == checkpoint_id)
            .scalar()
        )

    def delete_attachment(self, attachment: AnexoCheckpoint) -> None:
        self.db.delete(attachment)
        self.db.flush()