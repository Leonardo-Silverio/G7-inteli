from uuid import UUID
from typing import Optional
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.projeto import Projeto
from app.models.conversa import Conversa, Mensagem
from app.models.enums import StatusProjeto


class ProjetoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, projeto: Projeto) -> Projeto:
        self.db.add(projeto)
        self.db.flush()
        return projeto

    def get_project_by_id(self, projeto_id: UUID) -> Projeto | None:
        return (
            self.db.query(Projeto)
            .options(joinedload(Projeto.vertical), joinedload(Projeto.criador))
            .filter(Projeto.id == projeto_id)
            .first()
        )

    def _build_project_filters(
        self,
        vertical_id: UUID | None = None,
        status: StatusProjeto | None = None,
        criado_por_id: UUID | None = None,
        search: str | None = None,
    ):
        conditions = []
        if vertical_id:
            conditions.append(Projeto.vertical_id == vertical_id)
        if status:
            conditions.append(Projeto.status == status)
        if criado_por_id:
            conditions.append(Projeto.criado_por_id == criado_por_id)
        if search:
            search_pattern = f"%{search}%"
            conditions.append(
                or_(
                    Projeto.titulo.ilike(search_pattern),
                    Projeto.descricao.ilike(search_pattern),
                )
            )
        return conditions

    def count_projects(
        self,
        vertical_id: UUID | None = None,
        status: StatusProjeto | None = None,
        criado_por_id: UUID | None = None,
        search: str | None = None,
    ) -> int:
        query = select(func.count(Projeto.id))
        conditions = self._build_project_filters(
            vertical_id, status, criado_por_id, search
        )
        if conditions:
            query = query.where(*conditions)
        return self.db.execute(query).scalar_one()

    def list_projects(
        self,
        page: int = 1,
        page_size: int = 20,
        vertical_id: UUID | None = None,
        status: StatusProjeto | None = None,
        criado_por_id: UUID | None = None,
        search: str | None = None,
    ) -> list[Projeto]:
        query = select(Projeto).options(
            joinedload(Projeto.vertical), joinedload(Projeto.criador)
        )
        conditions = self._build_project_filters(
            vertical_id, status, criado_por_id, search
        )
        if conditions:
            query = query.where(*conditions)
        query = query.order_by(Projeto.created_at.desc(), Projeto.id.desc())
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        return list(self.db.execute(query).scalars().unique().all())

    def update_project(self, projeto: Projeto, updates: dict[str, object]) -> Projeto:
        for key, value in updates.items():
            if hasattr(projeto, key):
                setattr(projeto, key, value)
        self.db.flush()
        return projeto

    def create_conversation(self, conversa: Conversa) -> Conversa:
        self.db.add(conversa)
        self.db.flush()
        return conversa

    def get_conversation_by_project(self, projeto_id: UUID) -> Conversa | None:
        return (
            self.db.query(Conversa)
            .filter(Conversa.projeto_id == projeto_id)
            .first()
        )

    def add_message(self, mensagem: Mensagem) -> Mensagem:
        self.db.add(mensagem)
        self.db.flush()
        return mensagem

    def list_messages(
        self,
        conversa_id: UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> list[Mensagem]:
        query = select(Mensagem).filter(Mensagem.conversa_id == conversa_id)
        query = query.order_by(Mensagem.created_at.asc(), Mensagem.id.asc())
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        return list(self.db.execute(query).scalars().all())

    def count_messages(self, conversa_id: UUID) -> int:
        return (
            self.db.query(func.count(Mensagem.id))
            .filter(Mensagem.conversa_id == conversa_id)
            .scalar()
        )