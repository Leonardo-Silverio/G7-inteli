from uuid import UUID
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.jwt import decode_access_token
from app.database.database import get_db
from app.models.enums import PapelUsuario
from app.repositories.user_repository import UserRepository
from app.repositories.projeto_repository import ProjetoRepository
from app.services.auth_service import AuthService
from app.services.projeto_service import ProjetoService
from app.schemas.user import CurrentUser

security = HTTPBearer(auto_error=False)


def get_user_repo(db=Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_projeto_repo(db=Depends(get_db)) -> ProjetoRepository:
    return ProjetoRepository(db)


def get_auth_service(user_repo=Depends(get_user_repo)) -> AuthService:
    return AuthService(user_repo)


def get_projeto_service(repo=Depends(get_projeto_repo)) -> ProjetoService:
    return ProjetoService(repo)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> CurrentUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise credentials_exception

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    user = auth_service.get_current_user(user_id)
    if not user:
        raise credentials_exception

    return user


def require_role(*roles: PapelUsuario):
    def role_checker(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if current_user.papel not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente",
            )
        return current_user

    return role_checker


require_admin = require_role(PapelUsuario.ADMIN)
require_lideranca = require_role(PapelUsuario.LIDERANCA, PapelUsuario.ADMIN)
require_marketing = require_role(PapelUsuario.MARKETING, PapelUsuario.LIDERANCA, PapelUsuario.ADMIN)
require_vertical = require_role(PapelUsuario.VERTICAL, PapelUsuario.MARKETING, PapelUsuario.LIDERANCA, PapelUsuario.ADMIN)