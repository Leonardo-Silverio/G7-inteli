import pytest
from uuid import uuid4
from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.models.enums import PapelUsuario, TipoCheckpoint, StatusCheckpoint, StatusProjeto
from app.models.usuario import Usuario
from app.models.vertical import Vertical
from app.models.projeto import Projeto
from app.models.checkpoint import Checkpoint
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


def _valid_ideacao_payload():
    return {
        "versao_formulario": "ideacao_v1",
        "versao_business": "2026-07",
        "schema_version": 1,
        "tipo_checkpoint": "IDEACAO",
        "respostas": {
            "descricao_projeto": "Projeto de teste com descricao longa suficiente",
            "proposta_solucao": "Solucao proposta detalhada para o projeto",
            "focos_azul": ["RECONQUISTA_CLIENTE"],
            "impacto_rotas": "NAO_E_SOBRE_ROTAS",
            "existe_semelhante": False,
            "semelhante_descricao": None,
            "prazo_mercado": "1_3_MESES",
            "dependencia_critica": False,
            "dependencia_descricao": None,
            "diferencial": "Diferencial competitivo claro e detalhado",
            "info_nao_compartilhada": False,
            "info_nao_compartilhada_descricao": None,
        },
    }


def _valid_desenvolvimento_payload():
    return {
        "versao_formulario": "desenvolvimento_v1",
        "versao_business": "2026-07",
        "schema_version": 1,
        "tipo_checkpoint": "DESENVOLVIMENTO",
        "respostas": {
            "material_desenvolvido": "Material desenvolvido detalhado para o checkpoint",
            "produtos_azul": ["AZUL_FIDELIDADE"],
            "tom_escala": 3,
            "mudancas_desde_ideacao": "Mudancas desde o checkpoint de ideacao",
            "feedback_ideacao_enderecado": "SIM",
            "feedback_explicacao": None,
            "limitacoes_internas": "NAO",
            "limitacoes_explicacao": None,
        },
    }


def _valid_pre_lancamento_payload():
    return {
        "versao_formulario": "pre_lancamento_v1",
        "versao_business": "2026-07",
        "schema_version": 1,
        "tipo_checkpoint": "PRE_LANCAMENTO",
        "respostas": {
            "versao_final_descricao": "Descricao da versao final do projeto",
            "areas_acordo": "SIM",
            "areas_lista": None,
            "dados_clientes": False,
            "dados_clientes_descricao": None,
            "revisao_juridica": "NAO",
            "revisao_juridica_referencia": None,
            "tarifas_confirmadas": True,
            "risco_interpretacao": False,
            "risco_interpretacao_descricao": None,
            "comparado_campanhas": "NAO",
            "data_prevista_lancamento": (date.today() + timedelta(days=30)).isoformat(),
            "riscos_incertos": "Riscos incertos identificados",
        },
    }


class TestIdeacaoForm:
    def test_submit_ideacao_success(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_ideacao@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/enviar",
            json=_valid_ideacao_payload(),
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["checkpoint"]["status"] == "CONCLUIDO"
        assert data["checkpoint"]["concluido_em"] is not None
        assert data["checkpoint"]["tipo"] == "IDEACAO"
        assert "proxima_etapa" in data

    def test_ideacao_short_descricao_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_ideacao2@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        payload = _valid_ideacao_payload()
        payload["respostas"]["descricao_projeto"] = "Curto"
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_ideacao_short_proposta_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_ideacao3@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        payload = _valid_ideacao_payload()
        payload["respostas"]["proposta_solucao"] = "Curto"
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_ideacao_empty_focos_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_ideacao4@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        payload = _valid_ideacao_payload()
        payload["respostas"]["focos_azul"] = []
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_ideacao_nenhum_with_other_foco_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_ideacao5@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        payload = _valid_ideacao_payload()
        payload["respostas"]["focos_azul"] = ["NENHUM", "RECONQUISTA_CLIENTE"]
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_ideacao_missing_impacto_rotas_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_ideacao6@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        payload = _valid_ideacao_payload()
        del payload["respostas"]["impacto_rotas"]
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_ideacao_existe_semelhante_without_descricao_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_ideacao7@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        payload = _valid_ideacao_payload()
        payload["respostas"]["existe_semelhante"] = True
        payload["respostas"]["semelhante_descricao"] = None
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_ideacao_dependencia_critica_without_descricao_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_ideacao8@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        payload = _valid_ideacao_payload()
        payload["respostas"]["dependencia_critica"] = True
        payload["respostas"]["dependencia_descricao"] = None
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_ideacao_diferencial_ausente_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_ideacao9@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        payload = _valid_ideacao_payload()
        payload["respostas"]["diferencial"] = "Curto"
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_ideacao_info_nao_compartilhada_without_descricao_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_ideacao10@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO)
        
        headers = _auth_headers(user)
        payload = _valid_ideacao_payload()
        payload["respostas"]["info_nao_compartilhada"] = True
        payload["respostas"]["info_nao_compartilhada_descricao"] = None
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/IDEACAO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422


class TestDesenvolvimentoForm:
    def test_submit_desenvolvimento_success(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_dev@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        
        # Iniciar checkpoint de desenvolvimento
        headers = _auth_headers(user)
        client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/iniciar",
            headers=headers,
        )
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/enviar",
            json=_valid_desenvolvimento_payload(),
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["checkpoint"]["status"] == "CONCLUIDO"
        assert data["checkpoint"]["tipo"] == "DESENVOLVIMENTO"

    def test_desenvolvimento_invalid_tom_escala_low(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_dev2@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        
        headers = _auth_headers(user)
        client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/iniciar",
            headers=headers,
        )
        
        payload = _valid_desenvolvimento_payload()
        payload["respostas"]["tom_escala"] = 0
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_desenvolvimento_invalid_tom_escala_high(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_dev3@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        
        headers = _auth_headers(user)
        client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/iniciar",
            headers=headers,
        )
        
        payload = _valid_desenvolvimento_payload()
        payload["respostas"]["tom_escala"] = 6
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_desenvolvimento_nenhum_with_other_produto_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_dev5@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        
        headers = _auth_headers(user)
        client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/iniciar",
            headers=headers,
        )
        
        payload = _valid_desenvolvimento_payload()
        payload["respostas"]["produtos_azul"] = ["NENHUM", "AZUL_FIDELIDADE"]
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_desenvolvimento_feedback_parcial_without_explicacao_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_dev6@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        
        headers = _auth_headers(user)
        client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/iniciar",
            headers=headers,
        )
        
        payload = _valid_desenvolvimento_payload()
        payload["respostas"]["feedback_ideacao_enderecado"] = "PARCIALMENTE"
        payload["respostas"]["feedback_explicacao"] = None
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_desenvolvimento_feedback_nao_without_explicacao_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_dev7@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        
        headers = _auth_headers(user)
        client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/iniciar",
            headers=headers,
        )
        
        payload = _valid_desenvolvimento_payload()
        payload["respostas"]["feedback_ideacao_enderecado"] = "NAO"
        payload["respostas"]["feedback_explicacao"] = None
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_desenvolvimento_limitacoes_true_without_descricao_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_dev8@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        
        headers = _auth_headers(user)
        client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/iniciar",
            headers=headers,
        )
        
        payload = _valid_desenvolvimento_payload()
        payload["respostas"]["limitacoes_internas"] = "SIM"
        payload["respostas"]["limitacoes_explicacao"] = None
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_desenvolvimento_mudancas_desde_ideacao_ausente_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_dev9@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        
        headers = _auth_headers(user)
        client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/iniciar",
            headers=headers,
        )
        
        payload = _valid_desenvolvimento_payload()
        payload["respostas"]["mudancas_desde_ideacao"] = "Curto"
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_desenvolvimento_cannot_start_before_ideacao_concluded(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_dev10@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.EM_PREENCHIMENTO)
        
        headers = _auth_headers(user)
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/DESENVOLVIMENTO/iniciar",
            headers=headers,
        )
        
        assert response.status_code == 409


class TestPreLancamentoForm:
    def test_submit_pre_lancamento_success_with_attachment(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_pre@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.DESENVOLVIMENTO, StatusCheckpoint.CONCLUIDO)
        
        headers = _auth_headers(user)
        client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/iniciar",
            headers=headers,
        )
        
        # Add attachment first
        client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/anexos",
            params={
                "storage_key": f"storage/{uuid4().hex}",
                "nome_original": "anexo.pdf",
                "mime_type": "application/pdf",
                "tamanho_bytes": 1024,
            },
            headers=headers,
        )
        
        payload = _valid_pre_lancamento_payload()
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["checkpoint"]["status"] == "CONCLUIDO"
        assert data["checkpoint"]["tipo"] == "PRE_LANCAMENTO"

    def test_pre_lancamento_sem_anexo_obrigatorio(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_pre2@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.DESENVOLVIMENTO, StatusCheckpoint.CONCLUIDO)
        
        headers = _auth_headers(user)
        client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/iniciar",
            headers=headers,
        )
        
        payload = _valid_pre_lancamento_payload()
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_pre_lancamento_areas_parcialmente_sem_lista_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_pre3@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.DESENVOLVIMENTO, StatusCheckpoint.CONCLUIDO)
        
        headers = _auth_headers(user)
        client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/iniciar",
            headers=headers,
        )
        
        payload = _valid_pre_lancamento_payload()
        payload["respostas"]["areas_acordo"] = "PARCIALMENTE"
        payload["respostas"]["areas_lista"] = None
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_pre_lancamento_areas_nao_sem_lista_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_pre4@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.DESENVOLVIMENTO, StatusCheckpoint.CONCLUIDO)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.PRE_LANCAMENTO)
        
        headers = _auth_headers(user)
        payload = _valid_pre_lancamento_payload()
        payload["respostas"]["areas_acordo"] = "NAO"
        payload["respostas"]["areas_lista"] = None
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_pre_lancamento_envolve_dados_true_sem_descricao_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_pre5@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.DESENVOLVIMENTO, StatusCheckpoint.CONCLUIDO)
        
        headers = _auth_headers(user)
        client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/iniciar",
            headers=headers,
        )
        
        payload = _valid_pre_lancamento_payload()
        payload["respostas"]["dados_clientes"] = True
        payload["respostas"]["dados_clientes_descricao"] = None
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_pre_lancamento_risco_true_sem_descricao_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_pre6@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.DESENVOLVIMENTO, StatusCheckpoint.CONCLUIDO)
        
        headers = _auth_headers(user)
        client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/iniciar",
            headers=headers,
        )
        
        payload = _valid_pre_lancamento_payload()
        payload["respostas"]["risco_interpretacao"] = True
        payload["respostas"]["risco_interpretacao_descricao"] = None
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_pre_lancamento_data_prevista_ausente_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_pre7@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.DESENVOLVIMENTO, StatusCheckpoint.CONCLUIDO)
        
        headers = _auth_headers(user)
        client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/iniciar",
            headers=headers,
        )
        
        payload = _valid_pre_lancamento_payload()
        del payload["respostas"]["data_prevista_lancamento"]
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_pre_lancamento_data_invalida_rejected(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_pre8@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.DESENVOLVIMENTO, StatusCheckpoint.CONCLUIDO)
        
        headers = _auth_headers(user)
        client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/iniciar",
            headers=headers,
        )
        
        payload = _valid_pre_lancamento_payload()
        payload["respostas"]["data_prevista_lancamento"] = "data-invalida"
        
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/enviar",
            json=payload,
            headers=headers,
        )
        
        assert response.status_code == 422

    def test_pre_lancamento_cannot_start_before_desenvolvimento_concluded(self, db, clean_db):
        vertical = _create_vertical(db, "Test")
        user = _create_user(db, "Creator", "creator_pre9@test.com", PapelUsuario.VERTICAL, vertical.id)
        projeto = _create_projeto(db, "Projeto", vertical.id, user.id)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.IDEACAO, StatusCheckpoint.CONCLUIDO)
        _create_checkpoint(db, projeto.id, TipoCheckpoint.DESENVOLVIMENTO, StatusCheckpoint.EM_PREENCHIMENTO)
        
        headers = _auth_headers(user)
        response = client.post(
            f"/projetos/{projeto.id}/checkpoints/PRE_LANCAMENTO/iniciar",
            headers=headers,
        )
        
        assert response.status_code == 409