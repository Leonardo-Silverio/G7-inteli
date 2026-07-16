from uuid import UUID
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.checkpoint import AvaliacaoCheckpoint


class AvaliacaoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_evaluation(self, avaliacao: AvaliacaoCheckpoint) -> AvaliacaoCheckpoint:
        self.db.add(avaliacao)
        self.db.flush()
        return avaliacao

    def get_evaluation(self, avaliacao_id: UUID) -> Optional[AvaliacaoCheckpoint]:
        return (
            self.db.query(AvaliacaoCheckpoint)
            .filter(AvaliacaoCheckpoint.id == avaliacao_id)
            .first()
        )

    def get_latest_evaluation(self, checkpoint_id: UUID) -> Optional[AvaliacaoCheckpoint]:
        return (
            self.db.query(AvaliacaoCheckpoint)
            .filter(AvaliacaoCheckpoint.checkpoint_id == checkpoint_id)
            .order_by(
                AvaliacaoCheckpoint.evaluated_at.desc(),
                AvaliacaoCheckpoint.created_at.desc(),
                AvaliacaoCheckpoint.id.desc(),
            )
            .first()
        )

    def list_evaluations(self, checkpoint_id: UUID) -> list[AvaliacaoCheckpoint]:
        return (
            self.db.query(AvaliacaoCheckpoint)
            .filter(AvaliacaoCheckpoint.checkpoint_id == checkpoint_id)
            .order_by(
                AvaliacaoCheckpoint.evaluated_at.desc(),
                AvaliacaoCheckpoint.created_at.desc(),
                AvaliacaoCheckpoint.id.desc(),
            )
            .all()
        )

    def count_evaluations(self, checkpoint_id: UUID) -> int:
        return (
            self.db.query(func.count(AvaliacaoCheckpoint.id))
            .filter(AvaliacaoCheckpoint.checkpoint_id == checkpoint_id)
            .scalar()
        )