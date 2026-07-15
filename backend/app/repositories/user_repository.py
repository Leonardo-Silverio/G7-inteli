from uuid import UUID

from sqlalchemy.orm import Session

from app.models.usuario import Usuario


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Usuario | None:
        return self.db.query(Usuario).filter(Usuario.email == email).first()

    def get_by_id(self, user_id: UUID) -> Usuario | None:
        return self.db.query(Usuario).filter(Usuario.id == user_id).first()

    def create(self, usuario: Usuario) -> Usuario:
        self.db.add(usuario)
        self.db.flush()
        return usuario