from uuid import UUID
from datetime import datetime, UTC

from app.core.hashing import hash_password, verify_password
from app.core.jwt import create_access_token
from app.models.enums import PapelUsuario
from app.models.usuario import Usuario
from app.repositories.user_repository import UserRepository
from app.schemas.user import CurrentUser, UserResponse


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def register(
        self,
        nome: str,
        email: str,
        senha: str,
        papel: PapelUsuario,
        vertical_id: UUID | None = None,
    ) -> UserResponse:
        existing = self.user_repo.get_by_email(email)
        if existing:
            raise ValueError("Email já cadastrado")

        senha_hash = hash_password(senha)
        usuario = Usuario(
            nome=nome,
            email=email,
            senha_hash=senha_hash,
            papel=papel,
            vertical_id=vertical_id,
        )
        self.user_repo.create(usuario)
        return UserResponse.model_validate(usuario)

    def login(self, email: str, senha: str) -> str:
        usuario = self.user_repo.get_by_email(email)
        if not usuario or not usuario.ativo:
            raise ValueError("Credenciais inválidas")

        if not verify_password(senha, usuario.senha_hash):
            raise ValueError("Credenciais inválidas")

        token_data = {
            "sub": str(usuario.id),
            "email": usuario.email,
            "role": usuario.papel.value,
            "iat": int(datetime.now(UTC).timestamp()),
        }
        return create_access_token(token_data)

    def get_current_user(self, user_id: UUID) -> CurrentUser | None:
        usuario = self.user_repo.get_by_id(user_id)
        if not usuario or not usuario.ativo:
            return None
        return CurrentUser(
            id=usuario.id,
            email=usuario.email,
            papel=usuario.papel,
            vertical_id=usuario.vertical_id,
        )