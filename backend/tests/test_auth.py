import pytest
from uuid import uuid4
from unittest.mock import Mock, MagicMock
from datetime import datetime, UTC, timedelta
from jose import jwt

from app.config.settings import settings
from app.models.enums import PapelUsuario
from app.models.usuario import Usuario
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService
from app.core.jwt import create_access_token, decode_access_token
from app.core.hashing import hash_password, verify_password


class TestAuthService:
    def setup_method(self):
        self.mock_repo = Mock()
        self.auth_service = AuthService(self.mock_repo)

    def test_register_success(self):
        user_id = uuid4()
        mock_user = Mock(spec=Usuario)
        mock_user.id = user_id
        mock_user.nome = "João"
        mock_user.email = "joao@exemplo.com"
        mock_user.papel = PapelUsuario.VERTICAL
        mock_user.vertical_id = None
        mock_user.ativo = True
        mock_user.created_at = datetime.now(UTC)
        mock_user.updated_at = datetime.now(UTC)
        mock_user.senha_hash = "hashed_password"

        self.mock_repo.get_by_email.return_value = None

        def create_user(u):
            u.id = user_id
            u.ativo = True
            u.created_at = datetime.now(UTC)
            u.updated_at = datetime.now(UTC)
            return u

        self.mock_repo.create = Mock(side_effect=create_user)

        result = self.auth_service.register(
            nome="João",
            email="joao@exemplo.com",
            senha="senha123",
            papel=PapelUsuario.VERTICAL,
        )

        assert result.email == "joao@exemplo.com"
        assert result.nome == "João"
        assert result.papel == PapelUsuario.VERTICAL

    def test_register_duplicate_email_raises(self):
        self.mock_repo.get_by_email.return_value = Mock(spec=Usuario)

        with pytest.raises(ValueError, match="Email já cadastrado"):
            self.auth_service.register(
                nome="João",
                email="joao@exemplo.com",
                senha="senha123",
                papel=PapelUsuario.VERTICAL,
            )

    def test_login_success(self):
        user_id = uuid4()
        senha_hash = hash_password("senha123")
        mock_user = Mock(spec=Usuario)
        mock_user.id = user_id
        mock_user.email = "joao@exemplo.com"
        mock_user.senha_hash = senha_hash
        mock_user.papel = PapelUsuario.VERTICAL
        mock_user.ativo = True

        self.mock_repo.get_by_email.return_value = mock_user

        token = self.auth_service.login("joao@exemplo.com", "senha123")

        assert token is not None
        payload = decode_access_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["email"] == "joao@exemplo.com"
        assert payload["role"] == "VERTICAL"

    def test_login_invalid_password(self):
        user_id = uuid4()
        senha_hash = hash_password("senha123")
        mock_user = Mock(spec=Usuario)
        mock_user.id = user_id
        mock_user.email = "joao@exemplo.com"
        mock_user.senha_hash = senha_hash
        mock_user.ativo = True

        self.mock_repo.get_by_email.return_value = mock_user

        with pytest.raises(ValueError, match="Credenciais inválidas"):
            self.auth_service.login("joao@exemplo.com", "senha_errada")

    def test_login_user_not_found(self):
        self.mock_repo.get_by_email.return_value = None

        with pytest.raises(ValueError, match="Credenciais inválidas"):
            self.auth_service.login("naoexiste@exemplo.com", "senha123")

    def test_login_user_inactive(self):
        mock_user = Mock(spec=Usuario)
        mock_user.ativo = False

        self.mock_repo.get_by_email.return_value = mock_user

        with pytest.raises(ValueError, match="Credenciais inválidas"):
            self.auth_service.login("joao@exemplo.com", "senha123")

    def test_get_current_user_success(self):
        user_id = uuid4()
        mock_user = Mock(spec=Usuario)
        mock_user.id = user_id
        mock_user.email = "joao@exemplo.com"
        mock_user.papel = PapelUsuario.VERTICAL
        mock_user.vertical_id = None
        mock_user.ativo = True

        self.mock_repo.get_by_id.return_value = mock_user

        result = self.auth_service.get_current_user(user_id)

        assert result is not None
        assert result.id == user_id
        assert result.email == "joao@exemplo.com"
        assert result.papel == PapelUsuario.VERTICAL

    def test_get_current_user_not_found(self):
        self.mock_repo.get_by_id.return_value = None

        result = self.auth_service.get_current_user(uuid4())

        assert result is None

    def test_get_current_user_inactive(self):
        mock_user = Mock(spec=Usuario)
        mock_user.ativo = False

        self.mock_repo.get_by_id.return_value = mock_user

        result = self.auth_service.get_current_user(uuid4())

        assert result is None


class TestSecurity:
    def test_create_access_token(self):
        data = {"sub": str(uuid4()), "email": "test@test.com", "role": "ADMIN"}
        token = create_access_token(data)

        assert token is not None
        payload = decode_access_token(token)
        assert payload["sub"] == data["sub"]
        assert payload["email"] == data["email"]
        assert payload["role"] == data["role"]
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_invalid_token(self):
        result = decode_access_token("invalid.token.string")
        assert result is None

    def test_decode_expired_token(self):
        data = {"sub": str(uuid4()), "email": "test@test.com", "role": "ADMIN"}
        expire = datetime.now(UTC) - timedelta(minutes=1)
        token = jwt.encode(
            {**data, "exp": expire},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        result = decode_access_token(token)
        assert result is None

    def test_hash_and_verify_password(self):
        password = "minha_senha_segura123"
        hashed = hash_password(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("senha_errada", hashed)