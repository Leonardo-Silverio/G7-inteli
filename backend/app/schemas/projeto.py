from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.enums import StatusProjeto, AutorMensagem


class ProjetoCreate(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    descricao: str | None = Field(default=None, max_length=5000)


class ProjetoUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=200)
    descricao: str | None = Field(default=None, max_length=5000)


class ProjetoResponse(BaseModel):
    id: UUID
    titulo: str
    descricao: str | None
    objetivo: str | None
    vertical_id: UUID
    criado_por_id: UUID
    status: StatusProjeto
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjetoListParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    status: StatusProjeto | None = None
    vertical_id: UUID | None = None
    criado_por_id: UUID | None = None
    search: str | None = None


class ProjetoListResponse(BaseModel):
    items: list[ProjetoResponse]
    page: int
    page_size: int
    total: int
    pages: int


class MensagemCreate(BaseModel):
    conteudo: str = Field(min_length=1, max_length=10000)

    @field_validator("conteudo", mode="before")
    @classmethod
    def strip_conteudo(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("conteudo")
    @classmethod
    def validar_conteudo_nao_vazio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Conteúdo da mensagem não pode ser vazio")
        return v


class MensagemResponse(BaseModel):
    id: UUID
    conversa_id: UUID
    autor_tipo: AutorMensagem
    usuario_id: UUID | None
    conteudo: str
    created_at: datetime

    class Config:
        from_attributes = True


class MensagemListResponse(BaseModel):
    items: list[MensagemResponse]
    page: int
    page_size: int
    total: int
    pages: int


class ConversaResponse(BaseModel):
    id: UUID
    projeto_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True