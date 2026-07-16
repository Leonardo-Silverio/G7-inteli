from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.schemas.checkpoint import (
    CheckpointListResponse,
    CheckpointResponse,
    CheckpointStartResponse,
    CheckpointDraftResponse,
    CheckpointSubmitResponse,
    CheckpointSalvarRespostasRequest,
    CheckpointEnviarRequest,
    AnexoListResponse,
    AnexoUploadResponse,
)
from app.services.checkpoint_service import (
    CheckpointService,
    ProjetoNotFoundForCheckpointError,
    CheckpointNotFoundError,
    CheckpointAuthorizationError,
    CheckpointOrderError,
    CheckpointAlreadyExistsError,
    InvalidCheckpointTransitionError,
    AttachmentNotFoundError,
    AttachmentLimitExceededError,
    CheckpointValidationError,
    AttachmentRequiredError,
)
from app.schemas.user import CurrentUser
from app.models.enums import TipoCheckpoint
from app.dependencies.auth import get_checkpoint_service

router = APIRouter(
    prefix="/projetos/{projeto_id}/checkpoints",
    tags=["Checkpoints"],
)


def _handle_service_error(e: Exception) -> HTTPException:
    if isinstance(e, (ProjetoNotFoundForCheckpointError, CheckpointNotFoundError, AttachmentNotFoundError)):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    if isinstance(e, CheckpointAuthorizationError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    if isinstance(e, CheckpointValidationError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors)
    if isinstance(e, AttachmentRequiredError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    if isinstance(e, (CheckpointOrderError, CheckpointAlreadyExistsError, InvalidCheckpointTransitionError, AttachmentLimitExceededError)):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=CheckpointListResponse, status_code=status.HTTP_200_OK)
def list_checkpoints(
    projeto_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: CheckpointService = Depends(get_checkpoint_service),
) -> CheckpointListResponse:
    try:
        return service.list_checkpoints(projeto_id, current_user)
    except (ProjetoNotFoundForCheckpointError, CheckpointNotFoundError, CheckpointAuthorizationError) as e:
        raise _handle_service_error(e)


@router.get("/{tipo}", response_model=CheckpointResponse, status_code=status.HTTP_200_OK)
def get_checkpoint(
    projeto_id: UUID,
    tipo: TipoCheckpoint,
    current_user: CurrentUser = Depends(get_current_user),
    service: CheckpointService = Depends(get_checkpoint_service),
) -> CheckpointResponse:
    try:
        return service.get_checkpoint(projeto_id, tipo, current_user)
    except (ProjetoNotFoundForCheckpointError, CheckpointNotFoundError, CheckpointAuthorizationError) as e:
        raise _handle_service_error(e)


@router.post("/{tipo}/iniciar", response_model=CheckpointStartResponse, status_code=status.HTTP_201_CREATED)
def start_checkpoint(
    projeto_id: UUID,
    tipo: TipoCheckpoint,
    current_user: CurrentUser = Depends(get_current_user),
    service: CheckpointService = Depends(get_checkpoint_service),
) -> CheckpointStartResponse:
    try:
        return service.start_checkpoint(projeto_id, tipo, current_user)
    except (ProjetoNotFoundForCheckpointError, CheckpointNotFoundError, CheckpointAuthorizationError, CheckpointOrderError) as e:
        raise _handle_service_error(e)


@router.patch("/{tipo}/respostas", response_model=CheckpointDraftResponse, status_code=status.HTTP_200_OK)
def save_checkpoint_draft(
    projeto_id: UUID,
    tipo: TipoCheckpoint,
    data: CheckpointSalvarRespostasRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CheckpointService = Depends(get_checkpoint_service),
) -> CheckpointDraftResponse:
    try:
        return service.save_checkpoint_draft(projeto_id, tipo, data.respostas, current_user)
    except (ProjetoNotFoundForCheckpointError, CheckpointNotFoundError, CheckpointAuthorizationError, InvalidCheckpointTransitionError) as e:
        raise _handle_service_error(e)


@router.post("/{tipo}/enviar", response_model=CheckpointSubmitResponse, status_code=status.HTTP_200_OK)
def submit_checkpoint(
    projeto_id: UUID,
    tipo: TipoCheckpoint,
    data: CheckpointEnviarRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CheckpointService = Depends(get_checkpoint_service),
) -> CheckpointSubmitResponse:
    try:
        return service.submit_checkpoint(projeto_id, tipo, data.respostas, current_user)
    except (ProjetoNotFoundForCheckpointError, CheckpointNotFoundError, CheckpointAuthorizationError, InvalidCheckpointTransitionError, CheckpointValidationError, AttachmentRequiredError) as e:
        raise _handle_service_error(e)


@router.get("/{tipo}/anexos", response_model=AnexoListResponse, status_code=status.HTTP_200_OK)
def list_attachments(
    projeto_id: UUID,
    tipo: TipoCheckpoint,
    current_user: CurrentUser = Depends(get_current_user),
    service: CheckpointService = Depends(get_checkpoint_service),
) -> AnexoListResponse:
    try:
        return service.list_attachments(projeto_id, tipo, current_user)
    except (ProjetoNotFoundForCheckpointError, CheckpointNotFoundError, CheckpointAuthorizationError) as e:
        raise _handle_service_error(e)


@router.post("/{tipo}/anexos", response_model=AnexoUploadResponse, status_code=status.HTTP_201_CREATED)
def register_attachment(
    projeto_id: UUID,
    tipo: TipoCheckpoint,
    storage_key: str,
    nome_original: str,
    mime_type: str,
    tamanho_bytes: int,
    current_user: CurrentUser = Depends(get_current_user),
    service: CheckpointService = Depends(get_checkpoint_service),
) -> AnexoUploadResponse:
    try:
        return service.register_attachment(
            projeto_id,
            tipo,
            storage_key,
            nome_original,
            mime_type,
            tamanho_bytes,
            current_user,
        )
    except (ProjetoNotFoundForCheckpointError, CheckpointNotFoundError, CheckpointAuthorizationError, InvalidCheckpointTransitionError, AttachmentLimitExceededError) as e:
        raise _handle_service_error(e)


@router.delete("/{tipo}/anexos/{anexo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    projeto_id: UUID,
    tipo: TipoCheckpoint,
    anexo_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: CheckpointService = Depends(get_checkpoint_service),
) -> None:
    try:
        service.delete_attachment(projeto_id, tipo, anexo_id, current_user)
    except (ProjetoNotFoundForCheckpointError, CheckpointNotFoundError, CheckpointAuthorizationError, AttachmentNotFoundError) as e:
        raise _handle_service_error(e)