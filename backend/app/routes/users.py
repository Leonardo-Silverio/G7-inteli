from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_auth_service
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/users", tags=["Usuários"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    try:
        return auth_service.register(
            nome=user_data.nome,
            email=user_data.email,
            senha=user_data.senha,
            papel=user_data.papel,
            vertical_id=user_data.vertical_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))