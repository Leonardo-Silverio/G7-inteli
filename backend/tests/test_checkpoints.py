import pytest
from uuid import uuid4
from datetime import date, timedelta, datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.models.enums import PapelUsuario, TipoCheckpoint, StatusCheckpoint, StatusProjeto
from app.models.usuario import Usuario
from app.models.vertical import Vertical
from app.models.projeto import Projeto
from app.models.checkpoint import Checkpoint, AvaliacaoCheckpoint
from app.models.enums import ClassificacaoFarol
from app.core.jwt import create_access_token

client = TestClient(app)


def _make_user(papel: PapelUsuario, vertical_id=None, user_id=None, email=None) -> Usuario:
    uid = user_id or uuid4()
    user = Usuario(
        id=uid,
        nome=f"User {papel.value}",
        email=email or f"{papel.value.lower()}{uuid4().hex[:8]}@exemplo.com",
        senha_hash="hash",
        papel=papel,
        vertical_id=vertical_id,
        ativo=True,
    )
    return user


def _make_vertical(vertical_id=None) -> Vertical:
    vid = vertical_id or uuid4()
    vertical = Vertical(
        id=vid,
        nome=f"Vertical {vid.hex[:8]}",
        descricao="Descricao",
        ativa=True,
    )
    return vertical


def _make_projeto(projeto_id=None, vertical_id=None, criado_por_id=None, status=StatusProjeto.EM_IDEACAO) -> Projeto:
    pid = projeto_id or uuid4()
    projeto = Projeto(
        id=pid,
        titulo="Projeto Teste",
        descricao="Descricao do projeto",
        vertical_id=vertical_id,
        criado_por_id=criado_por_id,
        status=status,
    )
    return projeto


def _make_checkpoint(checkpoint_id=None, projeto_id=None, tipo=TipoCheckpoint.IDEACAO, status=StatusCheckpoint.EM_PREENCHIMENTO) -> Checkpoint:
    cid = checkpoint_id or uuid4()
    cp = Checkpoint(
        id=cid,
        projeto_id=projeto_id,
        tipo=tipo,
        status=status,
    )
    return cp


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


class TestCheckpointLifecycle:
    def test_creator_starts_ideacao_checkpoint(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        
        headers = _auth_headers(user)
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/iniciar",
            headers=headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["criado"] is True
        assert data["checkpoint"]["status"] == "EM_PREENCHIMENTO"
        assert data["checkpoint"]["tipo"] == "IDEACAO"
        assert data["checkpoint"]["iniciado_em"] is not None
        assert data["checkpoint"]["concluido_em"] is None

    def test_start_checkpoint_idempotent(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator2@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        
        headers = _auth_headers(user)
        
        response1 = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/iniciar",
            headers=headers,
        )
        assert response1.status_code == 201
        data1 = response1.json()
        
        response2 = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/iniciar",
            headers=headers,
        )
        assert response2.status_code == 201
        data2 = response2.json()
        
        assert data2["criado"] is False
        assert data2["checkpoint"]["id"] == data1["checkpoint"]["id"]
        
        response_list = client.get(f"/projetos/{projeto.id}/checkpoints", headers=headers)
        assert response_list.status_code == 200
        assert response_list.json()["total"] == 1

    def test_same_vertical_other_user_cannot_start(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user1 = _create_user(db, "Creator", "creator3@test.com", PapelUsuario.VERTICAL, vertical.id)
        user2 = _create_user(db, "Other", "other@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user1.id)
        
        headers = _auth_headers(user2)
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/iniciar",
            headers=headers,
        )
        
        assert response.status_code == 403

    def test_marketing_cannot_start(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_m = _create_user(db, "M", "m@test.com", PapelUsuario.MARKETING)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        
        headers = _auth_headers(user_m)
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/iniciar",
            headers=headers,
        )
        
        assert response.status_code == 403

    def test_admin_cannot_start(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_a = _create_user(db, "A", "a@test.com", PapelUsuario.ADMIN)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        
        headers = _auth_headers(user_a)
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/iniciar",
            headers=headers,
        )
        
        assert response.status_code == 403

    def test_lideranca_cannot_start(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_l = _create_user(db, "L", "l@test.com", PapelUsuario.LIDERANCA)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        
        headers = _auth_headers(user_l)
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/iniciar",
            headers=headers,
        )
        
        assert response.status_code == 403

    def test_desenvolvimento_before_ideacao_concluded_409(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator4@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        
        headers = _auth_headers(user)
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/iniciar",
            headers=headers,
        )
        
        assert response.status_code == 409

    def test_pre_lancamento_before_desenvolvimento_concluded_409(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator5@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        
        headers = _auth_headers(user)
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/iniciar",
            headers=headers,
        )
        
        assert response.status_code == 409

    def test_checkpoint_order_in_list(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator6@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.DESENVOLVIMENTO, StatusCheckpoint.CONCLUIDO)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.PRE_LANCAMENTO, StatusCheckpoint.CONCLUIDO)
        
        headers = _auth_headers(user)
        response = client.get(f"/projetos/{projeto.id}/checkpoints", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        types = [item["tipo"] for item in data["items"]]
        assert types == ["IDEACAO", "DESENVOLVIMENTO", "PRE_LANCAMENTO"]

    def test_checkpoint_not_found(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator7@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        
        headers = _auth_headers(user)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO",
            headers=headers,
        )
        
        assert response.status_code == 404


class TestCheckpointVisualization:
    def test_creator_can_view_list(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator8@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        response = client.get(f"/projetos/{projeto.id}/checkpoints", headers=headers)
        
        assert response.status_code == 200
        assert response.json()["total"] == 1

    def test_same_vertical_can_view_list(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user1 = _create_user(db, "Creator", "creator9@test.com", PapelUsuario.VERTICAL, vertical.id)
        user2 = _create_user(db, "Other", "other2@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user1.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user2)
        response = client.get(f"/projetos/{projeto.id}/checkpoints", headers=headers)
        
        assert response.status_code == 200
        assert response.json()["total"] == 1

    def test_marketing_can_view_list(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_m = _create_user(db, "M", "m@test.com", PapelUsuario.MARKETING)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user_m)
        response = client.get(f"/projetos/{projeto.id}/checkpoints", headers=headers)
        
        assert response.status_code == 200
        assert response.json()["total"] == 1

    def test_admin_can_view_list(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_a = _create_user(db, "A", "a@test.com", PapelUsuario.ADMIN)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user_a)
        response = client.get(f"/projetos/{projeto.id}/checkpoints", headers=headers)
        
        assert response.status_code == 200
        assert response.json()["total"] == 1

    def test_different_vertical_cannot_view_list(self, db, clean_db):
        vertical1 = _create_vertical(db, "V1")
        vertical2 = _create_vertical(db, "V2")
        user1 = _create_user(db, "U1", "u1@test.com", PapelUsuario.VERTICAL, vertical1.id)
        user2 = _create_user(db, "U2", "u2@test.com", PapelUsuario.VERTICAL, vertical2.id)
        projeto = _create_projeto(db, "Projeto", vertical1.id, user1.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user2)
        response = client.get(f"/projetos/{projeto.id}/checkpoints", headers=headers)
        
        assert response.status_code == 403

    def test_lideranca_cannot_view_list(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_l = _create_user(db, "L", "l@test.com", PapelUsuario.LIDERANCA)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user_l)
        response = client.get(f"/projetos/{projeto.id}/checkpoints", headers=headers)
        
        assert response.status_code == 403

    def test_creator_can_view_single(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator10@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO",
            headers=headers,
        )
        
        assert response.status_code == 200
        assert response.json()["tipo"] == "IDEACAO"

    def test_same_vertical_can_view_single(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user1 = _create_user(db, "Creator", "creator11@test.com", PapelUsuario.VERTICAL, vertical.id)
        user2 = _create_user(db, "Other", "other3@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user1.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user2)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO",
            headers=headers,
        )
        
        assert response.status_code == 200

    def test_marketing_can_view_single(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_m = _create_user(db, "M", "m@test.com", PapelUsuario.MARKETING)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user_m)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO",
            headers=headers,
        )
        
        assert response.status_code == 200

    def test_admin_can_view_single(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_a = _create_user(db, "A", "a@test.com", PapelUsuario.ADMIN)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user_a)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO",
            headers=headers,
        )
        
        assert response.status_code == 200

    def test_different_vertical_cannot_view_single(self, db, clean_db):
        vertical1 = _create_vertical(db, "V1")
        vertical2 = _create_vertical(db, "V2")
        user1 = _create_user(db, "U1", "u1@test.com", PapelUsuario.VERTICAL, vertical1.id)
        user2 = _create_user(db, "U2", "u2@test.com", PapelUsuario.VERTICAL, vertical2.id)
        projeto = _create_projeto(db, "Projeto", vertical1.id, user1.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user2)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO",
            headers=headers,
        )
        
        assert response.status_code == 403

    def test_lideranca_cannot_view_single(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_l = _create_user(db, "L", "l@test.com", PapelUsuario.LIDERANCA)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user_l)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO",
            headers=headers,
        )
        
        assert response.status_code == 403


class TestCheckpointDrafts:
    def test_creator_saves_partial_draft(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator12@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        response = client.patch(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/respostas",
            json={
                "versao_formulario": "ideacao_v1",
                "versao_business": "2026-07",
                "schema_version": 1,
                "tipo_checkpoint": "IDEACAO",
                "respostas": {
                    "descricao_projeto": "Descricao parcial do projeto",
                },
                "anexos": [],
            },
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["checkpoint"]["status"] == "EM_PREENCHIMENTO"
        assert "respostas_formulario" in data["checkpoint"]

    def test_save_draft_multiple_times(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator13@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        
        response1 = client.patch(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/respostas",
            json={
                "versao_formulario": "ideacao_v1",
                "versao_business": "2026-07",
                "schema_version": 1,
                "tipo_checkpoint": "IDEACAO",
                "respostas": {"campo1": "valor1"},
                "anexos": [],
            },
            headers=headers,
        )
        assert response1.status_code == 200
        
        response2 = client.patch(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/respostas",
            json={
                "versao_formulario": "ideacao_v1",
                "versao_business": "2026-07",
                "schema_version": 1,
                "tipo_checkpoint": "IDEACAO",
                "respostas": {"campo1": "valor1", "campo2": "valor2"},
                "anexos": [],
            },
            headers=headers,
        )
        assert response2.status_code == 200
        
        response_list = client.get(f"/projetos/{projeto.id}/checkpoints", headers=headers)
        assert response_list.json()["total"] == 1

    def test_other_user_cannot_save_draft(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user1 = _create_user(db, "Creator", "creator14@test.com", PapelUsuario.VERTICAL, vertical.id)
        user2 = _create_user(db, "Other", "other4@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user1.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user2)
        response = client.patch(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/respostas",
            json={
                "versao_formulario": "ideacao_v1",
                "versao_business": "2026-07",
                "schema_version": 1,
                "tipo_checkpoint": "IDEACAO",
                "respostas": {"campo": "valor"},
                "anexos": [],
            },
            headers=headers,
        )
        
        assert response.status_code == 403

    def test_cannot_save_draft_on_concluded(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator15@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        
        headers = _auth_headers(user)
        response = client.patch(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/respostas",
            json={
                "versao_formulario": "ideacao_v1",
                "versao_business": "2026-07",
                "schema_version": 1,
                "tipo_checkpoint": "IDEACAO",
                "respostas": {"campo": "valor"},
                "anexos": [],
            },
            headers=headers,
        )
        
        assert response.status_code == 409


class TestCheckpointDraftValidation:
    def test_unknown_field_in_request_422(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator16@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        response = client.patch(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/respostas",
            json={
                "versao_formulario": "ideacao_v1",
                "versao_business": "2026-07",
                "schema_version": 1,
                "tipo_checkpoint": "IDEACAO",
                "respostas": {"campo_inexistente": "valor"},
                "anexos": [],
                "campo_extra": "valor",
            },
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_invalid_form_version_422(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator17@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        response = client.patch(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/respostas",
            json={
                "versao_formulario": "versao_invalida",
                "versao_business": "2026-07",
                "schema_version": 1,
                "tipo_checkpoint": "IDEACAO",
                "respostas": {},
                "anexos": [],
            },
            headers=headers,
        )
        
        assert response.status_code == 422


class TestCheckpointSecurity:
    def test_unauthenticated_access_401(self):
        response = client.get("/projetos/00000000-0000-0000-0000-000000000000/checkpoints")
        assert response.status_code == 401

    def test_invalid_token_401(self):
        headers = {"Authorization": "Bearer token_invalido"}
        response = client.get("/projetos/00000000-0000-0000-0000-000000000000/checkpoints", headers=headers)
        assert response.status_code == 401

    def test_no_endpoint_in_public_paths(self):
        from app.main import app
        openapi = app.openapi()
        paths = openapi["paths"]
        for path in paths:
            if "checkpoints" in path:
                for method, details in paths[path].items():
                    if "security" not in details:
                        raise AssertionError(f"Endpoint {method.upper()} {path} nao tem security")


def _criterio_valido(nota: float = 80):
    return {
        "nota": nota,
        "feedback": "Feedback do criterio",
        "evidencias": ["ev1"],
        "sugestoes": ["sg1"],
        "confianca": 90,
    }


def _alinhamento_todos(nota: float):
    c = _criterio_valido(nota)
    return {
        "tom_de_voz_azul": c,
        "identidade_visual_azul": c,
        "posicionamento_malha_regional": c,
        "uso_correto_produtos_marca": c,
        "seguranca_solidez": c,
        "clareza_passageiro": c,
    }


def _potencial_todos(nota: float):
    c = _criterio_valido(nota)
    return {
        "pilares_estrategicos_atuais": c,
        "receita_produtos_proprios": c,
        "alcance_malha_regional": c,
        "diferenciacao_gol_latam": c,
        "recuperacao_fidelizacao_cliente": c,
        "viabilidade_operacional": c,
    }


def _make_avaliacao(checkpoint_id, score_alinhamento=85, score_potencial=90, modelo="gpt-4o", prompt_version="v1"):
    return AvaliacaoCheckpoint(
        checkpoint_id=checkpoint_id,
        score_alinhamento=score_alinhamento,
        score_potencial=score_potencial,
        classificacao_farol=ClassificacaoFarol.PRIORIDADE_MAXIMA,
        criterios_alinhamento=_alinhamento_todos(score_alinhamento),
        criterios_potencial=_potencial_todos(score_potencial),
        feedback_geral="Feedback geral",
        resumo_para_marketing="Resumo marketing",
        evaluation_engine="farol-engine-v1",
        modelo=modelo,
        prompt_version=prompt_version,
        criteria_version="v1",
        prompt_hash="a" * 64,
        criteria_hash="b" * 64,
        evaluated_at=datetime.now(timezone.utc),
    )


class TestAvaliacaoEndpoints:
    def _setup_project_with_checkpoint(self, db, status=StatusCheckpoint.CONCLUIDO):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        cp = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, status)
        return vertical, user, projeto, cp

    def _add_evaluations(self, db, checkpoint_id, count=2):
        for i in range(count):
            av = _make_avaliacao(checkpoint_id, score_alinhamento=70 + i * 5, score_potencial=70 + i * 5, modelo=f"gpt-{4+i}", prompt_version=f"v{i+1}")
            db.add(av)
        db.commit()

    # ===== GET /avaliacao (latest) =====

    def test_latest_evaluation_success(self, db, clean_db):
        vertical, user, projeto, cp = self._setup_project_with_checkpoint(db)
        self._add_evaluations(db, cp.id, 2)

        headers = _auth_headers(user)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/avaliacao",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["avaliacao"] is not None
        assert data["avaliacao"]["modelo"] == "gpt-5"
        assert data["avaliacao"]["score_alinhamento"] == 75.0
        assert data["total_historico"] == 2

    def test_latest_evaluation_no_evaluations(self, db, clean_db):
        vertical, user, projeto, cp = self._setup_project_with_checkpoint(db)

        headers = _auth_headers(user)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/avaliacao",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["avaliacao"] is None
        assert data["total_historico"] == 0

    def test_latest_evaluation_checkpoint_not_found(self, db, clean_db):
        vertical, user, projeto, _ = self._setup_project_with_checkpoint(db)

        headers = _auth_headers(user)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/avaliacao",
            headers=headers,
        )

        assert response.status_code == 404

    def test_latest_evaluation_unauthorized_different_vertical(self, db, clean_db):
        vertical1 = _create_vertical(db, "V1")
        vertical2 = _create_vertical(db, "V2")
        user1 = _create_user(db, "U1", "u1@test.com", PapelUsuario.VERTICAL, vertical1.id)
        user2 = _create_user(db, "U2", "u2@test.com", PapelUsuario.VERTICAL, vertical2.id)
        projeto = _create_projeto(db, "Projeto", vertical1.id, user1.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)

        headers = _auth_headers(user2)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/avaliacao",
            headers=headers,
        )

        assert response.status_code == 403

    def test_latest_evaluation_marketing_can_view(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_m = _create_user(db, "M", "m@test.com", PapelUsuario.MARKETING)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        cp = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        self._add_evaluations(db, cp.id, 1)

        headers = _auth_headers(user_m)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/avaliacao",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["avaliacao"] is not None

    def test_latest_evaluation_creator_can_view(self, db, clean_db):
        vertical, user, projeto, cp = self._setup_project_with_checkpoint(db)
        self._add_evaluations(db, cp.id, 1)

        headers = _auth_headers(user)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/avaliacao",
            headers=headers,
        )

        assert response.status_code == 200

    def test_latest_evaluation_lideranca_forbidden(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_l = _create_user(db, "L", "l@test.com", PapelUsuario.LIDERANCA)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        cp = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        self._add_evaluations(db, cp.id, 1)

        headers = _auth_headers(user_l)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/avaliacao",
            headers=headers,
        )

        assert response.status_code == 403

    # ===== GET /avaliacoes (history) =====

    def test_history_evaluations_order_desc(self, db, clean_db):
        vertical, user, projeto, cp = self._setup_project_with_checkpoint(db)
        self._add_evaluations(db, cp.id, 3)

        headers = _auth_headers(user)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/avaliacoes",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        # Order: most recent first (DESC)
        assert data["items"][0]["modelo"] == "gpt-6"
        assert data["items"][1]["modelo"] == "gpt-5"
        assert data["items"][2]["modelo"] == "gpt-4"

    def test_history_empty_checkpoint(self, db, clean_db):
        vertical, user, projeto, cp = self._setup_project_with_checkpoint(db)

        headers = _auth_headers(user)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/avaliacoes",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_history_checkpoint_not_found(self, db, clean_db):
        vertical, user, projeto, _ = self._setup_project_with_checkpoint(db)

        headers = _auth_headers(user)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/avaliacoes",
            headers=headers,
        )

        assert response.status_code == 404

    def test_history_unauthorized_different_vertical(self, db, clean_db):
        vertical1 = _create_vertical(db, "V1")
        vertical2 = _create_vertical(db, "V2")
        user1 = _create_user(db, "U1", "u1@test.com", PapelUsuario.VERTICAL, vertical1.id)
        user2 = _create_user(db, "U2", "u2@test.com", PapelUsuario.VERTICAL, vertical2.id)
        projeto = _create_projeto(db, "Projeto", vertical1.id, user1.id)
        cp = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        self._add_evaluations(db, cp.id, 1)

        headers = _auth_headers(user2)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/avaliacoes",
            headers=headers,
        )

        assert response.status_code == 403

    def test_history_marketing_can_view(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_m = _create_user(db, "M", "m@test.com", PapelUsuario.MARKETING)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        cp = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        self._add_evaluations(db, cp.id, 2)

        headers = _auth_headers(user_m)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/avaliacoes",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["total"] == 2

    def test_history_creator_can_view(self, db, clean_db):
        vertical, user, projeto, cp = self._setup_project_with_checkpoint(db)
        self._add_evaluations(db, cp.id, 1)

        headers = _auth_headers(user)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/avaliacoes",
            headers=headers,
        )

        assert response.status_code == 200

    def test_history_lideranca_forbidden(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user_v = _create_user(db, "V", "v@test.com", PapelUsuario.VERTICAL, vertical.id)
        user_l = _create_user(db, "L", "l@test.com", PapelUsuario.LIDERANCA)
        projeto = _create_projeto(db, "Projeto", vertical.id, user_v.id)
        cp = _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        self._add_evaluations(db, cp.id, 1)

        headers = _auth_headers(user_l)
        response = client.get(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/avaliacoes",
            headers=headers,
        )

        assert response.status_code == 403