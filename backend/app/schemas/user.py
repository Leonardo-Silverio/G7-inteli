from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.enums import PapelUsuario


class UserCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    papel: PapelUsuario
    vertical_id: UUID | None = None


class UserResponse(BaseModel):
    id: UUID
    nome: str
    email: EmailStr
    papel: PapelUsuario
    vertical_id: UUID | None
    ativo: bool

    class Config:
        from_attributes = True


class CurrentUser(BaseModel):
    id: UUID
    email: str
    papel: PapelUsuario
    vertical_id: UUID | None