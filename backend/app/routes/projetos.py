from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.dependencies.auth import get_current_user, get_projeto_service
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
from app.services.projeto_service import (
    ProjetoService,
    ProjetoNotFoundError,
    ConversationNotFoundError,
    MissingVerticalError,
    AuthorizationError,
)
from app.schemas.user import CurrentUser

router = APIRouter(prefix="/projetos", tags=["Projetos"])


def _handle_service_error(e: Exception) -> HTTPException:
    if isinstance(e, (ProjetoNotFoundError, ConversationNotFoundError)):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    if isinstance(e, AuthorizationError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    if isinstance(e, MissingVerticalError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("", response_model=ProjetoResponse, status_code=status.HTTP_201_CREATED)
def create_projeto(
    data: ProjetoCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProjetoService = Depends(get_projeto_service),
) -> ProjetoResponse:
    try:
        return service.create_project(data, current_user)
    except (ProjetoNotFoundError, ConversationNotFoundError, MissingVerticalError, AuthorizationError) as e:
        raise _handle_service_error(e)


@router.get("", response_model=ProjetoListResponse, status_code=status.HTTP_200_OK)
def list_projetos(
    params: ProjetoListParams = Depends(),
    current_user: CurrentUser = Depends(get_current_user),
    service: ProjetoService = Depends(get_projeto_service),
) -> ProjetoListResponse:
    try:
        return service.list_projects(params, current_user)
    except (ProjetoNotFoundError, ConversationNotFoundError, MissingVerticalError, AuthorizationError) as e:
        raise _handle_service_error(e)


@router.get("/{projeto_id}", response_model=ProjetoResponse, status_code=status.HTTP_200_OK)
def get_projeto(
    projeto_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProjetoService = Depends(get_projeto_service),
) -> ProjetoResponse:
    try:
        return service.get_project(projeto_id, current_user)
    except (ProjetoNotFoundError, ConversationNotFoundError, MissingVerticalError, AuthorizationError) as e:
        raise _handle_service_error(e)


@router.patch("/{projeto_id}", response_model=ProjetoResponse, status_code=status.HTTP_200_OK)
def update_projeto(
    projeto_id: UUID,
    data: ProjetoUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProjetoService = Depends(get_projeto_service),
) -> ProjetoResponse:
    try:
        return service.update_project(projeto_id, data, current_user)
    except (ProjetoNotFoundError, ConversationNotFoundError, MissingVerticalError, AuthorizationError) as e:
        raise _handle_service_error(e)


@router.get("/{projeto_id}/conversa", response_model=ConversaResponse, status_code=status.HTTP_200_OK)
def get_conversa(
    projeto_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProjetoService = Depends(get_projeto_service),
) -> ConversaResponse:
    try:
        return service.get_conversation(projeto_id, current_user)
    except (ProjetoNotFoundError, ConversationNotFoundError, MissingVerticalError, AuthorizationError) as e:
        raise _handle_service_error(e)


@router.get("/{projeto_id}/mensagens", response_model=MensagemListResponse, status_code=status.HTTP_200_OK)
def list_mensagens(
    projeto_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    service: ProjetoService = Depends(get_projeto_service),
) -> MensagemListResponse:
    try:
        return service.list_messages(projeto_id, page, page_size, current_user)
    except (ProjetoNotFoundError, ConversationNotFoundError, MissingVerticalError, AuthorizationError) as e:
        raise _handle_service_error(e)


@router.post("/{projeto_id}/mensagens", response_model=MensagemResponse, status_code=status.HTTP_201_CREATED)
def send_mensagem(
    projeto_id: UUID,
    data: MensagemCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProjetoService = Depends(get_projeto_service),
) -> MensagemResponse:
    try:
        return service.send_message(projeto_id, data, current_user)
    except (ProjetoNotFoundError, ConversationNotFoundError, MissingVerticalError, AuthorizationError) as e:
        raise _handle_service_error(e)