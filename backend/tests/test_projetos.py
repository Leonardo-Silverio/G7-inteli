import pytest
from uuid import uuid4
from unittest.mock import Mock
from datetime import datetime, UTC

from fastapi.testclient import TestClient

from app.main import app
from app.models.enums import PapelUsuario, StatusProjeto
from app.models.usuario import Usuario
from app.models.vertical import Vertical
from app.models.projeto import Projeto
from app.models.conversa import Conversa, Mensagem
from app.schemas.projeto import ProjetoCreate, ProjetoUpdate, MensagemCreate


client = TestClient(app)


def _make_user(papel: PapelUsuario, vertical_id=None, user_id=None, email=None) -> Mock:
    uid = user_id or uuid4()
    mock_user = Mock(spec=Usuario)
    mock_user.id = uid
    mock_user.nome = f"User {papel.value}"
    mock_user.email = email or f"{papel.value.lower()}@exemplo.com"
    mock_user.papel = papel
    mock_user.vertical_id = vertical_id
    mock_user.ativo = True
    mock_user.senha_hash = "hash"
    mock_user.created_at = datetime.now(UTC)
    mock_user.updated_at = datetime.now(UTC)
    return mock_user


def _make_vertical(vertical_id=None) -> Mock:
    vid = vertical_id or uuid4()
    mock_vertical = Mock(spec=Vertical)
    mock_vertical.id = vid
    mock_vertical.nome = "Vertical Teste"
    mock_vertical.descricao = "Descricao"
    mock_vertical.ativa = True
    return mock_vertical


def _make_projeto(projeto_id=None, vertical_id=None, criado_por_id=None) -> Mock:
    pid = projeto_id or uuid4()
    mock_projeto = Mock(spec=Projeto)
    mock_projeto.id = pid
    mock_projeto.titulo = "Projeto Teste"
    mock_projeto.descricao = "Descricao do projeto"
    mock_projeto.objetivo = None
    mock_projeto.vertical_id = vertical_id
    mock_projeto.criado_por_id = criado_por_id
    mock_projeto.status = StatusProjeto.EM_IDEACAO
    mock_projeto.created_at = datetime.now(UTC)
    mock_projeto.updated_at = datetime.now(UTC)
    return mock_projeto


def _make_conversa(conversa_id=None, projeto_id=None) -> Mock:
    cid = conversa_id or uuid4()
    mock_conversa = Mock(spec=Conversa)
    mock_conversa.id = cid
    mock_conversa.projeto_id = projeto_id
    mock_conversa.created_at = datetime.now(UTC)
    mock_conversa.updated_at = datetime.now(UTC)
    return mock_conversa


def _make_mensagem(mensagem_id=None, conversa_id=None, usuario_id=None, conteudo="Teste") -> Mock:
    mid = mensagem_id or uuid4()
    mock_msg = Mock(spec=Mensagem)
    mock_msg.id = mid
    mock_msg.conversa_id = conversa_id
    mock_msg.autor_tipo = "USUARIO"
    mock_msg.usuario_id = usuario_id
    mock_msg.conteudo = conteudo
    mock_msg.created_at = datetime.now(UTC)
    return mock_msg


def _auth_headers(user) -> dict:
    from app.core.jwt import create_access_token
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.papel.value,
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


def _create_vertical(db, nome="Vertical"):
    vertical = Vertical(nome=f"{nome} {uuid4().hex[:8]}")
    db.add(vertical)
    db.commit()
    db.refresh(vertical)
    return vertical


def _create_user(db, nome, email, papel: PapelUsuario, vertical_id=None):
    user = Usuario(
        nome=nome,
        email=email,
        senha_hash="hash",
        papel=papel,
        vertical_id=vertical_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_projeto(db, titulo, vertical_id, criado_por_id, status=StatusProjeto.EM_IDEACAO):
    projeto = Projeto(
        titulo=titulo,
        descricao="Desc",
        vertical_id=vertical_id,
        criado_por_id=criado_por_id,
        status=status,
    )
    db.add(projeto)
    db.commit()
    db.refresh(projeto)
    return projeto


def _create_conversa(db, projeto_id):
    conv = Conversa(projeto_id=projeto_id)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def _create_mensagem(db, conversa_id, usuario_id, conteudo):
    msg = Mensagem(
        conversa_id=conversa_id,
        autor_tipo="USUARIO",
        usuario_id=usuario_id,
        conteudo=conteudo,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


class TestProjetosCreate:
    def test_vertical_creates_project_success(self, db, clean_db):
        vertical = _create_vertical(db, "Test Vertical")
        user = _create_user(db, "User VERTICAL", "vertical@exemplo.com", PapelUsuario.VERTICAL, vertical.id)
        
        headers = _auth_headers(user)
        
        response = client.post(
            "/projetos",
            json={"titulo": "Novo Projeto", "descricao": "Descricao do projeto"},
            headers=headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["titulo"] == "Novo Projeto"
        assert data["descricao"] == "Descricao do projeto"
        assert data["status"] == "EM_IDEACAO"
        assert data["criado_por_id"] == str(user.id)
        assert data["vertical_id"] == str(vertical.id)
        
        projeto_id = data["id"]
        
        conversa_response = client.get(f"/projetos/{projeto_id}/conversa", headers=headers)
        assert conversa_response.status_code == 200
        conv_data = conversa_response.json()
        assert conv_data["projeto_id"] == projeto_id

    def test_marketing_cannot_create_project(self, db, clean_db):
        user = _create_user(db, "User MARKETING", "marketing@exemplo.com", PapelUsuario.MARKETING)
        
        headers = _auth_headers(user)
        
        response = client.post(
            "/projetos",
            json={"titulo": "Projeto", "descricao": "Desc"},
            headers=headers,
        )
        
        assert response.status_code == 403

    def test_admin_cannot_create_project(self, db, clean_db):
        user = _create_user(db, "User ADMIN", "admin@exemplo.com", PapelUsuario.ADMIN)
        
        headers = _auth_headers(user)
        
        response = client.post(
            "/projetos",
            json={"titulo": "Projeto", "descricao": "Desc"},
            headers=headers,
        )
        
        assert response.status_code == 403

    def test_lideranca_cannot_create_project(self, db, clean_db):
        user = _create_user(db, "User LIDERANCA", "lideranca@exemplo.com", PapelUsuario.LIDERANCA)
        
        headers = _auth_headers(user)
        
        response = client.post(
            "/projetos",
            json={"titulo": "Projeto", "descricao": "Desc"},
            headers=headers,
        )
        
        assert response.status_code == 403

    def test_vertical_without_vertical_id_cannot_create(self, db, clean_db):
        user = _create_user(db, "User VERTICAL", "vertical@exemplo.com", PapelUsuario.VERTICAL, vertical_id=None)
        
        headers = _auth_headers(user)
        
        response = client.post(
            "/projetos",
            json={"titulo": "Projeto", "descricao": "Desc"},
            headers=headers,
        )
        
        assert response.status_code == 400
        assert "vertical" in response.json()["detail"].lower()

    def test_unauthenticated_cannot_create(self):
        response = client.post(
            "/projetos",
            json={"titulo": "Projeto", "descricao": "Desc"},
        )
        assert response.status_code == 401


class TestProjetosList:
    def test_vertical_lists_only_own_projects(self, db, clean_db):
        vertical1 = _create_vertical(db, "Vertical 1")
        vertical2 = _create_vertical(db, "Vertical 2")
        
        user1 = _create_user(db, "User 1", "u1@test.com", PapelUsuario.VERTICAL, vertical1.id)
        user2 = _create_user(db, "User 2", "u2@test.com", PapelUsuario.VERTICAL, vertical2.id)
        
        p1 = _create_projeto(db, "Projeto V1", vertical1.id, user1.id)
        p2 = _create_projeto(db, "Projeto V2", vertical2.id, user2.id)
        
        headers1 = _auth_headers(user1)
        headers2 = _auth_headers(user2)
        
        response1 = client.get("/projetos", headers=headers1)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["total"] == 1
        assert data1["items"][0]["titulo"] == "Projeto V1"
        
        response2 = client.get("/projetos", headers=headers2)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["total"] == 1
        assert data2["items"][0]["titulo"] == "Projeto V2"

    def test_marketing_lists_all_projects(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical M")
        
        user_v = _create_user(db, "V User", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_m = _create_user(db, "M User", "m@test.com", PapelUsuario.MARKETING)
        
        _create_projeto(db, "Proj 1", vertical.id, user_v.id)
        _create_projeto(db, "Proj 2", vertical.id, user_v.id)
        
        headers_m = _auth_headers(user_m)
        response = client.get("/projetos", headers=headers_m)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_admin_lists_all_projects(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical A")
        
        user_v = _create_user(db, "V User", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_a = _create_user(db, "A User", "a@test.com", PapelUsuario.ADMIN)
        
        _create_projeto(db, "Proj 1", vertical.id, user_v.id)
        
        headers_a = _auth_headers(user_a)
        response = client.get("/projetos", headers=headers_a)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_lideranca_cannot_list_projects(self, db, clean_db):
        user = _create_user(db, "User LIDERANCA", "l@test.com", PapelUsuario.LIDERANCA)
        
        headers = _auth_headers(user)
        response = client.get("/projetos", headers=headers)
        assert response.status_code == 403


class TestProjetosGet:
    def test_creator_can_view_project(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        user = _create_user(db, "Creator", "c@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Meu Projeto", vertical.id, user.id)
        
        headers = _auth_headers(user)
        response = client.get(f"/projetos/{projeto.id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["titulo"] == "Meu Projeto"
        assert data["id"] == str(projeto.id)

    def test_same_vertical_can_view_project(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        user1 = _create_user(db, "Creator", "c@test.com", PapelUsuario.VERTICAL, vertical.id)
        user2 = _create_user(db, "Other", "o@test.com", PapelUsuario.VERTICAL, vertical.id)
        
        projeto = _create_projeto(db, "Projeto", vertical.id, user1.id)
        
        headers = _auth_headers(user2)
        response = client.get(f"/projetos/{projeto.id}", headers=headers)
        assert response.status_code == 200

    def test_marketing_can_view_project(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_m = _create_user(db, "M", "m@test.com", PapelUsuario.MARKETING)
        
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        
        headers = _auth_headers(user_m)
        response = client.get(f"/projetos/{projeto.id}", headers=headers)
        assert response.status_code == 200

    def test_admin_can_view_project(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_a = _create_user(db, "A", "a@test.com", PapelUsuario.ADMIN)
        
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        
        headers = _auth_headers(user_a)
        response = client.get(f"/projetos/{projeto.id}", headers=headers)
        assert response.status_code == 200

    def test_different_vertical_cannot_view(self, db, clean_db):
        vertical1 = _create_vertical(db, "V1")
        vertical2 = _create_vertical(db, "V2")
        
        user1 = _create_user(db, "U1", "u1@test.com", PapelUsuario.VERTICAL, vertical1.id)
        user2 = _create_user(db, "U2", "u2@test.com", PapelUsuario.VERTICAL, vertical2.id)
        
        projeto = _create_projeto(db, "Projeto", vertical1.id, user1.id)
        
        headers = _auth_headers(user2)
        response = client.get(f"/projetos/{projeto.id}", headers=headers)
        assert response.status_code == 403


class TestProjetosUpdate:
    def test_creator_can_update(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        user = _create_user(db, "Creator", "c@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Original", vertical.id, user.id)
        
        headers = _auth_headers(user)
        response = client.patch(
            f"/projetos/{projeto.id}",
            json={"titulo": "Atualizado", "descricao": "Nova desc"},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["titulo"] == "Atualizado"
        assert data["descricao"] == "Nova desc"

    def test_admin_can_update(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_a = _create_user(db, "A", "a@test.com", PapelUsuario.ADMIN)
        
        projeto = _create_projeto(db, "Original", vertical.id, user_v.id)
        
        headers = _auth_headers(user_a)
        response = client.patch(
            f"/projetos/{projeto.id}",
            json={"titulo": "Admin Edit"},
            headers=headers,
        )
        assert response.status_code == 200

    def test_marketing_cannot_update(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_m = _create_user(db, "M", "m@test.com", PapelUsuario.MARKETING)
        
        projeto = _create_projeto(db, "Original", vertical.id, user_v.id)
        
        headers = _auth_headers(user_m)
        response = client.patch(
            f"/projetos/{projeto.id}",
            json={"titulo": "Tentativa"},
            headers=headers,
        )
        assert response.status_code == 403

    def test_lideranca_cannot_update(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_l = _create_user(db, "L", "l@test.com", PapelUsuario.LIDERANCA)
        
        projeto = _create_projeto(db, "Original", vertical.id, user_v.id)
        
        headers = _auth_headers(user_l)
        response = client.patch(
            f"/projetos/{projeto.id}",
            json={"titulo": "Tentativa"},
            headers=headers,
        )
        assert response.status_code == 403

    def test_other_vertical_cannot_update(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        user1 = _create_user(db, "U1", "u1@test.com", PapelUsuario.VERTICAL, vertical.id)
        user2 = _create_user(db, "U2", "u2@test.com", PapelUsuario.VERTICAL, vertical.id)
        
        projeto = _create_projeto(db, "Original", vertical.id, user1.id)
        
        headers = _auth_headers(user2)
        response = client.patch(
            f"/projetos/{projeto.id}",
            json={"titulo": "Tentativa"},
            headers=headers,
        )
        assert response.status_code == 403


class TestProjetosFilters:
    def test_filter_by_status(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        user = _create_user(db, "U", "u@test.com", PapelUsuario.ADMIN)
        
        p1 = _create_projeto(db, "P1", vertical.id, user.id, StatusProjeto.EM_IDEACAO)
        p2 = _create_projeto(db, "P2", vertical.id, user.id, StatusProjeto.EM_DESENVOLVIMENTO)
        
        headers = _auth_headers(user)
        response = client.get("/projetos", params={"status": "EM_IDEACAO"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["titulo"] == "P1"

    def test_search_by_title(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        user = _create_user(db, "U", "u@test.com", PapelUsuario.ADMIN)
        
        p1 = _create_projeto(db, "Projeto Especial", vertical.id, user.id)
        p2 = _create_projeto(db, "Outro Projeto", vertical.id, user.id)
        
        headers = _auth_headers(user)
        response = client.get("/projetos", params={"search": "Especial"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "Especial" in data["items"][0]["titulo"]

    def test_filter_by_vertical_id(self, db, clean_db):
        vertical1 = _create_vertical(db, "Vertical 1")
        vertical2 = _create_vertical(db, "Vertical 2")
        
        user = _create_user(db, "U", "u@test.com", PapelUsuario.ADMIN)
        
        p1 = _create_projeto(db, "P1", vertical1.id, user.id)
        p2 = _create_projeto(db, "P2", vertical2.id, user.id)
        
        headers = _auth_headers(user)
        response = client.get("/projetos", params={"vertical_id": str(vertical1.id)}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["titulo"] == "P1"

    def test_filter_by_criado_por_id(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        user1 = _create_user(db, "U1", "u1@test.com", PapelUsuario.ADMIN)
        user2 = _create_user(db, "U2", "u2@test.com", PapelUsuario.ADMIN)
        
        p1 = _create_projeto(db, "P1", vertical.id, user1.id)
        p2 = _create_projeto(db, "P2", vertical.id, user2.id)
        
        headers = _auth_headers(user1)
        response = client.get("/projetos", params={"criado_por_id": str(user1.id)}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["titulo"] == "P1"

    def test_combined_filters(self, db, clean_db):
        vertical1 = _create_vertical(db, "Vertical 1")
        vertical2 = _create_vertical(db, "Vertical 2")
        
        user = _create_user(db, "U", "u@test.com", PapelUsuario.ADMIN)
        
        p1 = _create_projeto(db, "P1 Ideacao", vertical1.id, user.id, StatusProjeto.EM_IDEACAO)
        p2 = _create_projeto(db, "P2 Desenvolvimento", vertical1.id, user.id, StatusProjeto.EM_DESENVOLVIMENTO)
        p3 = _create_projeto(db, "P3 Ideacao", vertical2.id, user.id, StatusProjeto.EM_IDEACAO)
        
        headers = _auth_headers(user)
        response = client.get(
            "/projetos", 
            params={"status": "EM_IDEACAO", "vertical_id": str(vertical1.id)}, 
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["titulo"] == "P1 Ideacao"


class TestProjetosPagination:
    def test_pagination(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        user = _create_user(db, "U", "u@test.com", PapelUsuario.ADMIN)
        
        for i in range(5):
            _create_projeto(db, f"Proj {i}", vertical.id, user.id)
        
        headers = _auth_headers(user)
        
        response = client.get("/projetos", params={"page": 1, "page_size": 2}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] == 5
        assert data["pages"] == 3
        assert len(data["items"]) == 2
        
        response2 = client.get("/projetos", params={"page": 2, "page_size": 2}, headers=headers)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["page"] == 2
        assert len(data2["items"]) == 2