import pytest
from uuid import uuid4
from unittest.mock import Mock
from datetime import datetime, UTC

from fastapi.testclient import TestClient

from app.main import app
from app.models.enums import PapelUsuario, StatusProjeto, AutorMensagem
from app.models.usuario import Usuario
from app.models.vertical import Vertical
from app.models.projeto import Projeto
from app.models.conversa import Conversa, Mensagem

client = TestClient(app)


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


def _create_user(db, nome, papel: PapelUsuario, vertical_id=None):
    email = f"{nome.lower()}-{uuid4().hex[:8]}@test.com"
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


class TestConversaAutoCreated:
    def test_conversa_created_automatically_with_project(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical Test")
        user = _create_user(db, "Creator", PapelUsuario.VERTICAL, vertical.id)
        
        headers = _auth_headers(user)
        
        response = client.post(
            "/projetos",
            json={"titulo": "Projeto com Conversa", "descricao": "Desc"},
            headers=headers,
        )
        assert response.status_code == 201
        projeto_id = response.json()["id"]
        
        conv_response = client.get(f"/projetos/{projeto_id}/conversa", headers=headers)
        assert conv_response.status_code == 200
        conv_data = conv_response.json()
        assert conv_data["projeto_id"] == projeto_id
        assert "created_at" in conv_data
        assert "updated_at" in conv_data


class TestConversaAccess:
    def test_creator_can_access_conversa(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        creator = _create_user(db, "Creator", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, creator.id)
        _create_conversa(db, projeto.id)
        
        headers = _auth_headers(creator)
        response = client.get(f"/projetos/{projeto.id}/conversa", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["projeto_id"] == str(projeto.id)

    def test_other_same_vertical_cannot_access_conversa(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        creator = _create_user(db, "Creator", PapelUsuario.VERTICAL, vertical.id)
        other = _create_user(db, "Other", PapelUsuario.VERTICAL, vertical.id)
        
        projeto = _create_projeto(db, "Projeto", vertical.id, creator.id)
        _create_conversa(db, projeto.id)
        
        headers = _auth_headers(other)
        response = client.get(f"/projetos/{projeto.id}/conversa", headers=headers)
        assert response.status_code == 403

    def test_marketing_cannot_access_conversa(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        creator = _create_user(db, "Creator", PapelUsuario.VERTICAL, vertical.id)
        marketing = _create_user(db, "Marketing", PapelUsuario.MARKETING)
        
        projeto = _create_projeto(db, "Projeto", vertical.id, creator.id)
        _create_conversa(db, projeto.id)
        
        headers = _auth_headers(marketing)
        response = client.get(f"/projetos/{projeto.id}/conversa", headers=headers)
        assert response.status_code == 403

    def test_admin_cannot_access_conversa(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        creator = _create_user(db, "Creator", PapelUsuario.VERTICAL, vertical.id)
        admin = _create_user(db, "Admin", PapelUsuario.ADMIN)
        
        projeto = _create_projeto(db, "Projeto", vertical.id, creator.id)
        _create_conversa(db, projeto.id)
        
        headers = _auth_headers(admin)
        response = client.get(f"/projetos/{projeto.id}/conversa", headers=headers)
        assert response.status_code == 403

    def test_lideranca_cannot_access_conversa(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        creator = _create_user(db, "Creator", PapelUsuario.VERTICAL, vertical.id)
        lideranca = _create_user(db, "Lideranca", PapelUsuario.LIDERANCA)
        
        projeto = _create_projeto(db, "Projeto", vertical.id, creator.id)
        _create_conversa(db, projeto.id)
        
        headers = _auth_headers(lideranca)
        response = client.get(f"/projetos/{projeto.id}/conversa", headers=headers)
        assert response.status_code == 403


class TestMensagensSend:
    def test_creator_can_send_message(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        creator = _create_user(db, "Creator", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, creator.id)
        conv = _create_conversa(db, projeto.id)
        
        headers = _auth_headers(creator)
        response = client.post(
            f"/projetos/{projeto.id}/mensagens",
            json={"conteudo": "Minha primeira mensagem"},
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["conteudo"] == "Minha primeira mensagem"
        assert data["autor_tipo"] == "USUARIO"
        assert data["usuario_id"] == str(creator.id)
        assert data["conversa_id"] == str(conv.id)

    def test_other_same_vertical_cannot_send_message(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        creator = _create_user(db, "Creator", PapelUsuario.VERTICAL, vertical.id)
        other = _create_user(db, "Other", PapelUsuario.VERTICAL, vertical.id)
        
        projeto = _create_projeto(db, "Projeto", vertical.id, creator.id)
        _create_conversa(db, projeto.id)
        
        headers = _auth_headers(other)
        response = client.post(
            f"/projetos/{projeto.id}/mensagens",
            json={"conteudo": "Tentativa"},
            headers=headers,
        )
        assert response.status_code == 403

    def test_marketing_cannot_send_message(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        creator = _create_user(db, "Creator", PapelUsuario.VERTICAL, vertical.id)
        marketing = _create_user(db, "Marketing", PapelUsuario.MARKETING)
        
        projeto = _create_projeto(db, "Projeto", vertical.id, creator.id)
        _create_conversa(db, projeto.id)
        
        headers = _auth_headers(marketing)
        response = client.post(
            f"/projetos/{projeto.id}/mensagens",
            json={"conteudo": "Tentativa"},
            headers=headers,
        )
        assert response.status_code == 403

    def test_admin_cannot_send_message(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        
        creator = _create_user(db, "Creator", PapelUsuario.VERTICAL, vertical.id)
        admin = _create_user(db, "Admin", PapelUsuario.ADMIN)
        
        projeto = _create_projeto(db, "Projeto", vertical.id, creator.id)
        _create_conversa(db, projeto.id)
        
        headers = _auth_headers(admin)
        response = client.post(
            f"/projetos/{projeto.id}/mensagens",
            json={"conteudo": "Tentativa"},
            headers=headers,
        )
        assert response.status_code == 403


class TestMensagensInvalidContent:
    def test_empty_content_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        creator = _create_user(db, "Creator", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, creator.id)
        _create_conversa(db, projeto.id)
        
        headers = _auth_headers(creator)
        response = client.post(
            f"/projetos/{projeto.id}/mensagens",
            json={"conteudo": ""},
            headers=headers,
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert any("vazio" in str(d).lower() or "character" in str(d).lower() for d in detail)

    def test_whitespace_only_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        creator = _create_user(db, "Creator", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, creator.id)
        _create_conversa(db, projeto.id)
        
        headers = _auth_headers(creator)
        response = client.post(
            f"/projetos/{projeto.id}/mensagens",
            json={"conteudo": "   "},
            headers=headers,
        )
        assert response.status_code == 422

    def test_over_10000_chars_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        creator = _create_user(db, "Creator", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, creator.id)
        _create_conversa(db, projeto.id)
        
        headers = _auth_headers(creator)
        long_content = "x" * 10001
        response = client.post(
            f"/projetos/{projeto.id}/mensagens",
            json={"conteudo": long_content},
            headers=headers,
        )
        assert response.status_code == 422


class TestMensagensPagination:
    def test_pagination_asc_order(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        creator = _create_user(db, "Creator", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, creator.id)
        conv = _create_conversa(db, projeto.id)
        
        for i in range(5):
            _create_mensagem(db, conv.id, creator.id, f"Mensagem {i}")
        
        headers = _auth_headers(creator)
        
        response = client.get(
            f"/projetos/{projeto.id}/mensagens",
            params={"page": 1, "page_size": 2},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] == 5
        assert data["pages"] == 3
        assert len(data["items"]) == 2
        
        first_page_items = data["items"]
        assert first_page_items[0]["conteudo"] == "Mensagem 0"
        assert first_page_items[1]["conteudo"] == "Mensagem 1"
        
        response2 = client.get(
            f"/projetos/{projeto.id}/mensagens",
            params={"page": 2, "page_size": 2},
            headers=headers,
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["page"] == 2
        assert data2["items"][0]["conteudo"] == "Mensagem 2"

    def test_creator_sees_messages(self, db, clean_db):
        vertical = _create_vertical(db, "Vertical")
        creator = _create_user(db, "Creator", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, creator.id)
        conv = _create_conversa(db, projeto.id)
        
        _create_mensagem(db, conv.id, creator.id, "Test message")
        
        headers = _auth_headers(creator)
        response = client.get(f"/projetos/{projeto.id}/mensagens", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["conteudo"] == "Test message"