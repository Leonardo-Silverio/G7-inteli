from uuid import UUID
from typing import Optional

from app.models.enums import PapelUsuario, StatusProjeto, AutorMensagem
from app.models.projeto import Projeto
from app.models.conversa import Conversa, Mensagem
from app.repositories.projeto_repository import ProjetoRepository
from app.schemas.projeto import (
    ProjetoCreate,
    ProjetoUpdate,
    ProjetoResponse,
    ProjetoListParams,
    ProjetoListResponse,
    MensagemCreate,
    MensagemResponse,
    MensagemListResponse,
    ConversaResponse,
)
from app.schemas.user import CurrentUser


class ProjetoNotFoundError(ValueError):
    pass


class ConversationNotFoundError(ValueError):
    pass


class MissingVerticalError(ValueError):
    pass


class AuthorizationError(ValueError):
    pass


class ProjetoService:
    def __init__(self, repo: ProjetoRepository):
        self.repo = repo

    def create_project(
        self,
        data: ProjetoCreate,
        current_user: CurrentUser,
    ) -> ProjetoResponse:
        self._require_vertical_user(current_user)

        projeto = Projeto(
            titulo=data.titulo,
            descricao=data.descricao,
            vertical_id=current_user.vertical_id,
            criado_por_id=current_user.id,
            status=StatusProjeto.EM_IDEACAO,
        )
        self.repo.create_project(projeto)

        conversa = Conversa(projeto_id=projeto.id)
        self.repo.create_conversation(conversa)

        return ProjetoResponse.model_validate(projeto)

    def list_projects(
        self,
        params: ProjetoListParams,
        current_user: CurrentUser,
    ) -> ProjetoListResponse:
        if current_user.papel == PapelUsuario.VERTICAL:
            if not current_user.vertical_id:
                raise MissingVerticalError("Usuário não possui vertical associada")
            effective_vertical_id = current_user.vertical_id
        elif current_user.papel == PapelUsuario.MARKETING:
            effective_vertical_id = params.vertical_id
        elif current_user.papel == PapelUsuario.ADMIN:
            effective_vertical_id = params.vertical_id
        elif current_user.papel == PapelUsuario.LIDERANCA:
            raise AuthorizationError("Acesso negado")
        else:
            raise AuthorizationError("Papel inválido")

        total = self.repo.count_projects(
            vertical_id=effective_vertical_id,
            status=params.status,
            criado_por_id=params.criado_por_id,
            search=params.search,
        )
        items = self.repo.list_projects(
            page=params.page,
            page_size=params.page_size,
            vertical_id=effective_vertical_id,
            status=params.status,
            criado_por_id=params.criado_por_id,
            search=params.search,
        )
        pages = (total + params.page_size - 1) // params.page_size

        return ProjetoListResponse(
            items=[ProjetoResponse.model_validate(p) for p in items],
            page=params.page,
            page_size=params.page_size,
            total=total,
            pages=pages,
        )

    def get_project(
        self,
        projeto_id: UUID,
        current_user: CurrentUser,
    ) -> ProjetoResponse:
        projeto = self.repo.get_project_by_id(projeto_id)
        if not projeto:
            raise ProjetoNotFoundError("Projeto não encontrado")

        self._authorize_view_project(projeto, current_user)

        return ProjetoResponse.model_validate(projeto)

    def update_project(
        self,
        projeto_id: UUID,
        data: ProjetoUpdate,
        current_user: CurrentUser,
    ) -> ProjetoResponse:
        projeto = self.repo.get_project_by_id(projeto_id)
        if not projeto:
            raise ProjetoNotFoundError("Projeto não encontrado")

        self._authorize_edit_project(projeto, current_user)

        updates = data.model_dump(exclude_unset=True)
        if not updates:
            raise ValueError("Nenhum campo para atualizar")

        for key in list(updates.keys()):
            if key not in ("titulo", "descricao"):
                updates.pop(key)

        if not updates:
            raise ValueError("Nenhum campo permitido para atualização")

        self.repo.update_project(projeto, updates)
        return ProjetoResponse.model_validate(projeto)

    def get_conversation(
        self,
        projeto_id: UUID,
        current_user: CurrentUser,
    ) -> ConversaResponse:
        projeto = self.repo.get_project_by_id(projeto_id)
        if not projeto:
            raise ProjetoNotFoundError("Projeto não encontrado")

        self._authorize_access_conversation(projeto, current_user)

        conversa = self.repo.get_conversation_by_project(projeto_id)
        if not conversa:
            raise ConversationNotFoundError("Conversa não encontrada")

        return ConversaResponse.model_validate(conversa)

    def list_messages(
        self,
        projeto_id: UUID,
        page: int,
        page_size: int,
        current_user: CurrentUser,
    ) -> MensagemListResponse:
        projeto = self.repo.get_project_by_id(projeto_id)
        if not projeto:
            raise ProjetoNotFoundError("Projeto não encontrado")

        self._authorize_access_conversation(projeto, current_user)

        conversa = self.repo.get_conversation_by_project(projeto_id)
        if not conversa:
            return MensagemListResponse(
                items=[],
                page=page,
                page_size=page_size,
                total=0,
                pages=0,
            )

        total = self.repo.count_messages(conversa.id)
        items = self.repo.list_messages(conversa.id, page, page_size)
        pages = (total + page_size - 1) // page_size

        return MensagemListResponse(
            items=[MensagemResponse.model_validate(m) for m in items],
            page=page,
            page_size=page_size,
            total=total,
            pages=pages,
        )

    def send_message(
        self,
        projeto_id: UUID,
        data: MensagemCreate,
        current_user: CurrentUser,
    ) -> MensagemResponse:
        projeto = self.repo.get_project_by_id(projeto_id)
        if not projeto:
            raise ProjetoNotFoundError("Projeto não encontrado")

        self._authorize_access_conversation(projeto, current_user)

        conversa = self.repo.get_conversation_by_project(projeto_id)
        if not conversa:
            raise ConversationNotFoundError("Conversa não encontrada")

        mensagem = Mensagem(
            conversa_id=conversa.id,
            autor_tipo=AutorMensagem.USUARIO,
            usuario_id=current_user.id,
            conteudo=data.conteudo,
        )
        self.repo.add_message(mensagem)
        return MensagemResponse.model_validate(mensagem)

    def _require_vertical_user(self, user: CurrentUser) -> None:
        if user.papel != PapelUsuario.VERTICAL:
            raise AuthorizationError("Apenas usuários VERTICAL podem criar projetos")
        if not user.vertical_id:
            raise MissingVerticalError("Usuário não possui vertical associada")

    def _authorize_view_project(self, projeto: Projeto, user: CurrentUser) -> None:
        if user.papel == PapelUsuario.VERTICAL:
            if projeto.vertical_id != user.vertical_id:
                raise AuthorizationError("Acesso negado")
        elif user.papel == PapelUsuario.MARKETING:
            return
        elif user.papel == PapelUsuario.ADMIN:
            return
        elif user.papel == PapelUsuario.LIDERANCA:
            raise AuthorizationError("Acesso negado")
        else:
            raise AuthorizationError("Papel inválido")

    def _authorize_edit_project(self, projeto: Projeto, user: CurrentUser) -> None:
        if user.papel == PapelUsuario.VERTICAL:
            if projeto.criado_por_id != user.id:
                raise AuthorizationError("Apenas o criador pode editar")
        elif user.papel == PapelUsuario.ADMIN:
            return
        elif user.papel in (PapelUsuario.MARKETING, PapelUsuario.LIDERANCA):
            raise AuthorizationError("Acesso negado")
        else:
            raise AuthorizationError("Papel inválido")

    def _authorize_access_conversation(self, projeto: Projeto, user: CurrentUser) -> None:
        if projeto.criado_por_id != user.id:
            raise AuthorizationError("Acesso negado: apenas o criador pode acessar a conversa")