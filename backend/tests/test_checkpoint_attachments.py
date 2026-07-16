import pytest
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.models.enums import PapelUsuario, TipoCheckpoint, StatusCheckpoint, StatusProjeto
from app.models.usuario import Usuario
from app.models.vertical import Vertical
from app.models.projeto import Projeto
from app.models.checkpoint import Checkpoint
from app.models.anexo_checkpoint import AnexoCheckpoint
from app.core.jwt import create_access_token

client = TestClient(app)


def _auth_headers(user: Usuario) -> dict:
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.papel.value,
    }
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


def _create_vertical(db, nome="Vertical"):
    vertical = Vertical(nome=f"{nome} {uuid4().hex[:8]}", descricao="Desc", ativa=True)
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
        ativo=True,
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


def _create_checkpoint(db, projeto_id, tipo, status=StatusCheckpoint.EM_PREENCHIMENTO):
    cp = Checkpoint(
        projeto_id=projeto_id,
        tipo=tipo,
        status=status,
    )
    db.add(cp)
    db.commit()
    db.refresh(cp)
    return cp


def _create_anexo(db, checkpoint_id, nome_original="teste.pdf", mime_type="application/pdf", tamanho_bytes=1024, storage_key=None, enviado_por_id=None):
    anexo = AnexoCheckpoint(
        checkpoint_id=checkpoint_id,
        nome_original=nome_original,
        mime_type=mime_type,
        tamanho_bytes=tamanho_bytes,
        storage_key=storage_key or f"storage/{uuid4().hex}",
        enviado_por_id=enviado_por_id,
    )
    db.add(anexo)
    db.commit()
    db.refresh(anexo)
    return anexo


class TestAttachmentsRegister:
    def test_creator_registers_attachment_metadata(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_attach@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        checkpoint = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        storage_key = f"storage/{uuid4().hex}"
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos",
            params={
                "storage_key": storage_key,
                "nome_original": "documento.pdf",
                "mime_type": "application/pdf",
                "tamanho_bytes": 2048,
            },
            headers=headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["nome_original"] == "documento.pdf"
        assert data["mime_type"] == "application/pdf"
        assert data["tamanho_bytes"] == 2048
        assert data["storage_key"] == storage_key
        assert data["id"] is not None

    def test_attachment_only_metadata_no_uploadfile(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_attach2@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        storage_key = f"storage/{uuid4().hex}"
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos",
            params={
                "storage_key": storage_key,
                "nome_original": "teste.txt",
                "mime_type": "text/plain",
                "tamanho_bytes": 100,
            },
            headers=headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "storage_key" in data
        assert "nome_original" in data
        assert "mime_type" in data
        assert "tamanho_bytes" in data
        assert "id" in data


class TestAttachmentsList:
    def test_list_attachments_ordered_by_created_at_asc(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_list@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        checkpoint = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        _create_anexo(db, checkpoint.id, "a.txt", "text/plain", 100, f"storage/{uuid4().hex}", user.id)
        _create_anexo(db, checkpoint.id, "b.pdf", "application/pdf", 200, f"storage/{uuid4().hex}", user.id)
        _create_anexo(db, checkpoint.id, "c.doc", "application/msword", 300, f"storage/{uuid4().hex}", user.id)
        
        headers = _auth_headers(user)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos",
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        names = [item["nome_original"] for item in data["items"]]
        assert names == ["a.txt", "b.pdf", "c.doc"]

    def test_list_attachments_limit_10(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_limit@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        checkpoint = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        for i in range(10):
            _create_anexo(db, checkpoint.id, f"file{i}.txt", "text/plain", 100, f"storage/{uuid4().hex}", user.id)
        
        headers = _auth_headers(user)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos",
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10

    def test_creator_can_list(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_list2@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        checkpoint = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        _create_anexo(db, checkpoint.id, "test.pdf", "application/pdf", 100, f"storage/{uuid4().hex}", user.id)
        
        headers = _auth_headers(user)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos",
            headers=headers,
        )
        
        assert response.status_code == 200

    def test_same_vertical_can_list(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user1 = _create_user(db, "Creator", "creator_list3@test.com", PapelUsuario.VERTICAL, vertical.id)
        user2 = _create_user(db, "Other", "other_list@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user1.id)
        checkpoint = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        _create_anexo(db, checkpoint.id, "test.pdf", "application/pdf", 100, f"storage/{uuid4().hex}", user1.id)
        
        headers = _auth_headers(user2)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos",
            headers=headers,
        )
        
        assert response.status_code == 200

    def test_marketing_can_list(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_m = _create_user(db, "M", "m@test.com", PapelUsuario.MARKETING)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        checkpoint = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        _create_anexo(db, checkpoint.id, "test.pdf", "application/pdf", 100, f"storage/{uuid4().hex}", user_v.id)
        
        headers = _auth_headers(user_m)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos",
            headers=headers,
        )
        
        assert response.status_code == 200

    def test_admin_can_list(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_a = _create_user(db, "A", "a@test.com", PapelUsuario.ADMIN)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        checkpoint = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        _create_anexo(db, checkpoint.id, "test.pdf", "application/pdf", 100, f"storage/{uuid4().hex}", user_v.id)
        
        headers = _auth_headers(user_a)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos",
            headers=headers,
        )
        
        assert response.status_code == 200

    def test_different_vertical_cannot_list(self, db, clean_db):
        vertical1 = _create_vertical(db, "V1")
        vertical2 = _create_vertical(db, "V2")
        user1 = _create_user(db, "U1", "u1@test.com", PapelUsuario.VERTICAL, vertical1.id)
        user2 = _create_user(db, "U2", "u2@test.com", PapelUsuario.VERTICAL, vertical2.id)
        projeto = _create_projeto(db, "Projeto", vertical1.id, user1.id)
        checkpoint = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        _create_anexo(db, checkpoint.id, "test.pdf", "application/pdf", 100, f"storage/{uuid4().hex}", user1.id)
        
        headers = _auth_headers(user2)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos",
            headers=headers,
        )
        
        assert response.status_code == 403

    def test_lideranca_cannot_list(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_l = _create_user(db, "L", "l@test.com", PapelUsuario.LIDERANCA)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        checkpoint = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        _create_anexo(db, checkpoint.id, "test.pdf", "application/pdf", 100, f"storage/{uuid4().hex}", user_v.id)
        
        headers = _auth_headers(user_l)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos",
            headers=headers,
        )
        
        assert response.status_code == 403


class TestAttachmentsCreatePermissions:
    def test_only_creator_can_create(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user1 = _create_user(db, "Creator", "creator_perm@test.com", PapelUsuario.VERTICAL, vertical.id)
        user2 = _create_user(db, "Other", "other_perm@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user1.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user2)
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos",
            params={
                "storage_key": f"storage/{uuid4().hex}",
                "nome_original": "test.pdf",
                "mime_type": "application/pdf",
                "tamanho_bytes": 100,
            },
            headers=headers,
        )
        
        assert response.status_code == 403

    def test_marketing_cannot_create(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_m = _create_user(db, "M", "m@test.com", PapelUsuario.MARKETING)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user_m)
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos",
            params={
                "storage_key": f"storage/{uuid4().hex}",
                "nome_original": "test.pdf",
                "mime_type": "application/pdf",
                "tamanho_bytes": 100,
            },
            headers=headers,
        )
        
        assert response.status_code == 403

    def test_admin_cannot_create(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_a = _create_user(db, "A", "a@test.com", PapelUsuario.ADMIN)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user_a)
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos",
            params={
                "storage_key": f"storage/{uuid4().hex}",
                "nome_original": "test.pdf",
                "mime_type": "application/pdf",
                "tamanho_bytes": 100,
            },
            headers=headers,
        )
        
        assert response.status_code == 403

    def test_lideranca_cannot_create(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_l = _create_user(db, "L", "l@test.com", PapelUsuario.LIDERANCA)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user_l)
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos",
            params={
                "storage_key": f"storage/{uuid4().hex}",
                "nome_original": "test.pdf",
                "mime_type": "application/pdf",
                "tamanho_bytes": 100,
            },
            headers=headers,
        )
        
        assert response.status_code == 403


class TestAttachmentsDelete:
    def test_creator_can_delete(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_del@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        checkpoint = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        anexo = _create_anexo(db, checkpoint.id, "test.pdf", "application/pdf", 100, f"storage/{uuid4().hex}", user.id)
        
        headers = _auth_headers(user)
        response = client.delete(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos/{anexo.id}",
            headers=headers,
        )
        
        assert response.status_code == 204
        
        response_list = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos",
            headers=headers,
        )
        assert response_list.json()["total"] == 0

    def test_delete_removes_only_db_record(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_del2@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        checkpoint = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        anexo = _create_anexo(db, checkpoint.id, "test.pdf", "application/pdf", 100, f"storage/{uuid4().hex}", user.id)
        
        headers = _auth_headers(user)
        response = client.delete(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos/{anexo.id}",
            headers=headers,
        )
        
        assert response.status_code == 204

    def test_other_user_cannot_delete(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user1 = _create_user(db, "Creator", "creator_del3@test.com", PapelUsuario.VERTICAL, vertical.id)
        user2 = _create_user(db, "Other", "other_del@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user1.id)
        checkpoint = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        anexo = _create_anexo(db, checkpoint.id, "test.pdf", "application/pdf", 100, f"storage/{uuid4().hex}", user1.id)
        
        headers = _auth_headers(user2)
        response = client.delete(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos/{anexo.id}",
            headers=headers,
        )
        
        assert response.status_code == 403

    def test_attachments_not_found_404(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_404@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        fake_id = uuid4()
        response = client.delete(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos/{fake_id}",
            headers=headers,
        )
        
        assert response.status_code == 404

    def test_attachment_from_other_checkpoint_404(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_other@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        checkpoint1 = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        checkpoint2 = _create_checkpoint(db, projeto.id, TipoCheckpoint.DESENVOLVIMENTO)
        anexo = _create_anexo(db, checkpoint2.id, "test.pdf", "application/pdf", 100, f"storage/{uuid4().hex}", user.id)
        
        headers = _auth_headers(user)
        response = client.delete(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos/{anexo.id}",
            headers=headers,
        )
        
        assert response.status_code == 404


class TestAttachmentsLimit:
    def test_limit_10_attachments(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_lim@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        checkpoint = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        
        for i in range(10):
            response = client.post(
                f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos",
                params={
                    "storage_key": f"storage/{uuid4().hex}",
                    "nome_original": f"file{i}.pdf",
                    "mime_type": "application/pdf",
                    "tamanho_bytes": 100,
                },
                headers=headers,
            )
            assert response.status_code == 201
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/anexos",
            params={
                "storage_key": f"storage/{uuid4().hex}",
                "nome_original": "file11.pdf",
                "mime_type": "application/pdf",
                "tamanho_bytes": 100,
            },
            headers=headers,
        )
        
        assert response.status_code == 409


class TestAttachmentsSecurity:
    def test_unauthenticated_access_401(self):
        response = client.get("/projetos/00000000-0000-0000-0000-000000000000/checkpoints/IDEACAO/anexos")
        assert response.status_code == 401

    def test_invalid_token_401(self):
        headers = {"Authorization": "Bearer token_invalido"}
        response = client.get("/projetos/00000000-0000-0000-0000-000000000000/checkpoints/IDEACAO/anexos", headers=headers)
        assert response.status_code == 401