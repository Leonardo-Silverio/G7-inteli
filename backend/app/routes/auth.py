from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import CurrentUser
from app.services.auth_service import AuthService
from app.dependencies.auth import get_auth_service

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    try:
        access_token = auth_service.login(request.email, request.senha)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return Token(access_token=access_token)


@router.get("/me", response_model=CurrentUser, status_code=status.HTTP_200_OK)
def me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current_user