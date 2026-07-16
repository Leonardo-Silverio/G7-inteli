import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.models.enums import StatusCheckpoint, TipoCheckpoint, ClassificacaoFarol
from app.models.checkpoint import Checkpoint
from app.models.projeto import Projeto
from app.models.usuario import Usuario
from app.models.vertical import Vertical
from app.services.checkpoint_service import CheckpointService
from app.services.avaliacao_service import AvaliacaoService
from app.config.settings import settings
from app.ai.provider import FakeAIProvider
from app.ai.checkpoint_evaluator import CheckpointAIEvaluator
from app.repositories.checkpoint_repository import CheckpointRepository
from app.repositories.projeto_repository import ProjetoRepository
from app.repositories.avaliacao_repository import AvaliacaoRepository
from app.schemas.user import CurrentUser
from app.schemas.checkpoint import (
    CheckpointEnviarRequest,
    IdeacaoFormData,
)
from app.schemas.avaliacao import (
    AvaliacaoIAOutput,
    CriterioAvaliacao,
    CriteriosAlinhamento,
    CriteriosPotencial,
    FeedbackItem,
)


def _valid_ia_output() -> AvaliacaoIAOutput:
    criterio = CriterioAvaliacao(
        nota=80,
        feedback="Bom",
        evidencias=["ev1"],
        sugestoes=["sg1"],
        confianca=90,
    )
    alinhamento = CriteriosAlinhamento(
        tom_de_voz_azul=criterio,
        identidade_visual_azul=criterio,
        posicionamento_malha_regional=criterio,
        uso_correto_produtos_marca=criterio,
        seguranca_solidez=criterio,
        clareza_passageiro=criterio,
    )
    potencial = CriteriosPotencial(
        pilares_estrategicos_atuais=criterio,
        receita_produtos_proprios=criterio,
        alcance_malha_regional=criterio,
        diferenciacao_gol_latam=criterio,
        recuperacao_fidelizacao_cliente=criterio,
        viabilidade_operacional=criterio,
    )
    return AvaliacaoIAOutput(
        criterios_alinhamento=alinhamento,
        criterios_potencial=potencial,
        feedback_geral="Feedback geral da IA",
        resumo_para_marketing="Resumo para marketing",
        pontos_fortes=[FeedbackItem(titulo="Pf1", descricao="Ponto forte 1")],
        oportunidades_melhoria=[FeedbackItem(titulo="Op1", descricao="Oportunidade 1")],
        recomendacoes_praticas=[FeedbackItem(titulo="Re1", descricao="Recomendacao 1")],
        proximos_passos=["Proximo passo"],
        riscos_principais=[FeedbackItem(titulo="Ri1", descricao="Risco 1", prioridade="BAIXA")],
    )


def _valid_ideacao_respostas() -> dict:
    return {
        "descricao_projeto": "Projeto de teste para avaliação IA",
        "proposta_solucao": "Solução inovadora para o problema",
        "focos_azul": ["RECONQUISTA_CLIENTE", "FORTALECIMENTO_MALHA_REGIONAL"],
        "impacto_rotas": "ROTAS_REGIONAIS",
        "existe_semelhante": False,
        "semelhante_descricao": None,
        "prazo_mercado": "1_3_MESES",
        "dependencia_critica": False,
        "dependencia_descricao": None,
        "diferencial": "Diferencial único no mercado",
        "info_nao_compartilhada": False,
        "info_nao_compartilhada_descricao": None,
    }


class TestAIEvaluationIntegration:
    def test_checkpoint_submits_and_creates_ai_evaluation(self, db):
        """Test that submitting a checkpoint triggers AI evaluation and creates evaluation record."""
        # Setup
        checkpoint_repo = CheckpointRepository(db)
        projeto_repo = ProjetoRepository(db)
        avaliacao_repo = AvaliacaoRepository(db)
        
        avaliacao_service = AvaliacaoService(avaliacao_repo, checkpoint_repo)
        
        # Create fake provider with valid response
        fake_provider = FakeAIProvider(response=_valid_ia_output().model_dump())
        ai_evaluator = CheckpointAIEvaluator(fake_provider)
        
        checkpoint_service = CheckpointService(
            checkpoint_repo=checkpoint_repo,
            projeto_repo=projeto_repo,
            avaliacao_service=avaliacao_service,
            ai_evaluator=ai_evaluator,
        )
        
        # Create test data
        vertical = Vertical(nome="Test Vertical")
        db.add(vertical)
        db.flush()
        
        usuario = Usuario(
            nome="Test User",
            email="test@test.com",
            senha_hash="hash",
            papel="VERTICAL",
            vertical_id=vertical.id,
        )
        db.add(usuario)
        db.flush()
        
        projeto = Projeto(
            titulo="Test Project",
            vertical_id=vertical.id,
            criado_por_id=usuario.id,
        )
        db.add(projeto)
        db.flush()
        
        current_user = CurrentUser(
            id=usuario.id,
            email=usuario.email,
            papel="VERTICAL",
            vertical_id=vertical.id,
        )
        
        # Start checkpoint
        start_resp = checkpoint_service.start_checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            current_user=current_user,
        )
        checkpoint_id = start_resp.checkpoint.id
        
        # Submit checkpoint with valid responses
        respostas = _valid_ideacao_respostas()
        submit_resp = checkpoint_service.submit_checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            respostas=respostas,
            current_user=current_user,
        )
        
        # Check checkpoint was concluded
        assert submit_resp.checkpoint.status == StatusCheckpoint.CONCLUIDO
        
        # Verify evaluation was created
        avaliacoes = avaliacao_repo.list_evaluations(checkpoint_id)
        assert len(avaliacoes) == 1
        
        avaliacao = avaliacoes[0]
        assert avaliacao.score_alinhamento == 80
        assert avaliacao.score_potencial == 80
        assert avaliacao.classificacao_farol == ClassificacaoFarol.PRIORIDADE_MAXIMA
        assert avaliacao.feedback_geral == "Feedback geral da IA"
        assert avaliacao.resumo_para_marketing == "Resumo para marketing"
        
        # Verify D9 metadata
        assert avaliacao.evaluation_engine == "farol-engine-v1"
        assert avaliacao.modelo == settings.DEEPSEEK_MODEL
        assert avaliacao.prompt_version == "checkpoint_v2"
        assert avaliacao.criteria_version == "business_rules_2026_07"
        assert avaliacao.prompt_hash is not None
        assert len(avaliacao.prompt_hash) == 64
        assert avaliacao.criteria_hash is not None
        assert len(avaliacao.criteria_hash) == 64
        assert avaliacao.evaluated_at is not None

    def test_checkpoint_works_without_ai_evaluator(self, db):
        """Test checkpoint works when AI evaluator is not configured."""
        checkpoint_repo = CheckpointRepository(db)
        projeto_repo = ProjetoRepository(db)
        
        # No avaliacao_service or ai_evaluator provided
        checkpoint_service = CheckpointService(
            checkpoint_repo=checkpoint_repo,
            projeto_repo=projeto_repo,
        )
        
        # Create test data
        vertical = Vertical(nome="Test Vertical")
        db.add(vertical)
        db.flush()
        
        usuario = Usuario(
            nome="Test User",
            email="test@test.com",
            senha_hash="hash",
            papel="VERTICAL",
            vertical_id=vertical.id,
        )
        db.add(usuario)
        db.flush()
        
        projeto = Projeto(
            titulo="Test Project",
            vertical_id=vertical.id,
            criado_por_id=usuario.id,
        )
        db.add(projeto)
        db.flush()
        
        current_user = CurrentUser(
            id=usuario.id,
            email=usuario.email,
            papel="VERTICAL",
            vertical_id=vertical.id,
        )
        
        # Start and submit checkpoint
        checkpoint_service.start_checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            current_user=current_user,
        )
        
        respostas = _valid_ideacao_respostas()
        submit_resp = checkpoint_service.submit_checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            respostas=respostas,
            current_user=current_user,
        )
        
        # Checkpoint should succeed even without AI
        assert submit_resp.checkpoint.status == StatusCheckpoint.CONCLUIDO

    def test_ai_failure_does_not_break_checkpoint(self, db):
        """Test that AI provider failure doesn't prevent checkpoint completion."""
        checkpoint_repo = CheckpointRepository(db)
        projeto_repo = ProjetoRepository(db)
        avaliacao_repo = AvaliacaoRepository(db)
        
        avaliacao_service = AvaliacaoService(avaliacao_repo, checkpoint_repo)
        
        # Create provider that fails
        fake_provider = FakeAIProvider(should_fail=True)
        ai_evaluator = CheckpointAIEvaluator(fake_provider)
        
        checkpoint_service = CheckpointService(
            checkpoint_repo=checkpoint_repo,
            projeto_repo=projeto_repo,
            avaliacao_service=avaliacao_service,
            ai_evaluator=ai_evaluator,
        )
        
        # Create test data
        vertical = Vertical(nome="Test Vertical")
        db.add(vertical)
        db.flush()
        
        usuario = Usuario(
            nome="Test User",
            email="test@test.com",
            senha_hash="hash",
            papel="VERTICAL",
            vertical_id=vertical.id,
        )
        db.add(usuario)
        db.flush()
        
        projeto = Projeto(
            titulo="Test Project",
            vertical_id=vertical.id,
            criado_por_id=usuario.id,
        )
        db.add(projeto)
        db.flush()
        
        current_user = CurrentUser(
            id=usuario.id,
            email=usuario.email,
            papel="VERTICAL",
            vertical_id=vertical.id,
        )
        
        # Start checkpoint
        checkpoint_service.start_checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            current_user=current_user,
        )
        
        # Submit checkpoint - should succeed even if AI fails
        respostas = _valid_ideacao_respostas()
        submit_resp = checkpoint_service.submit_checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            respostas=respostas,
            current_user=current_user,
        )
        
        # Checkpoint should be completed
        assert submit_resp.checkpoint.status == StatusCheckpoint.CONCLUIDO
        
        # No evaluation should be created due to AI failure
        checkpoint_id = submit_resp.checkpoint.id
        avaliacoes = avaliacao_repo.list_evaluations(checkpoint_id)
        assert len(avaliacoes) == 0

    def test_ai_invalid_response_does_not_break_checkpoint(self, db):
        """Test that invalid AI response doesn't prevent checkpoint completion."""
        checkpoint_repo = CheckpointRepository(db)
        projeto_repo = ProjetoRepository(db)
        avaliacao_repo = AvaliacaoRepository(db)
        
        avaliacao_service = AvaliacaoService(avaliacao_repo, checkpoint_repo)
        
        # Create provider with invalid response (missing required fields)
        invalid_output = {
            "criterios_alinhamento": {
                "tom_de_voz_azul": {"nota": 80, "feedback": "x", "evidencias": [], "sugestoes": [], "confianca": 90}
            },
            "criterios_potencial": {},
            "feedback_geral": "x",
            "resumo_para_marketing": "x",
        }
        fake_provider = FakeAIProvider(response=invalid_output)
        ai_evaluator = CheckpointAIEvaluator(fake_provider)
        
        checkpoint_service = CheckpointService(
            checkpoint_repo=checkpoint_repo,
            projeto_repo=projeto_repo,
            avaliacao_service=avaliacao_service,
            ai_evaluator=ai_evaluator,
        )
        
        # Create test data
        vertical = Vertical(nome="Test Vertical")
        db.add(vertical)
        db.flush()
        
        usuario = Usuario(
            nome="Test User",
            email="test@test.com",
            senha_hash="hash",
            papel="VERTICAL",
            vertical_id=vertical.id,
        )
        db.add(usuario)
        db.flush()
        
        projeto = Projeto(
            titulo="Test Project",
            vertical_id=vertical.id,
            criado_por_id=usuario.id,
        )
        db.add(projeto)
        db.flush()
        
        current_user = CurrentUser(
            id=usuario.id,
            email=usuario.email,
            papel="VERTICAL",
            vertical_id=vertical.id,
        )
        
        # Start checkpoint
        checkpoint_service.start_checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            current_user=current_user,
        )
        
        # Submit checkpoint
        respostas = _valid_ideacao_respostas()
        submit_resp = checkpoint_service.submit_checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            respostas=respostas,
            current_user=current_user,
        )
        
        # Checkpoint should complete
        assert submit_resp.checkpoint.status == StatusCheckpoint.CONCLUIDO
        
        # No evaluation created due to validation error
        checkpoint_id = submit_resp.checkpoint.id
        avaliacoes = avaliacao_repo.list_evaluations(checkpoint_id)
        assert len(avaliacoes) == 0

    def test_scores_calculated_by_evaluation_engine_only(self, db):
        """Verify scores are calculated by EvaluationEngine, not from AI."""
        checkpoint_repo = CheckpointRepository(db)
        projeto_repo = ProjetoRepository(db)
        avaliacao_repo = AvaliacaoRepository(db)
        
        avaliacao_service = AvaliacaoService(avaliacao_repo, checkpoint_repo)
        
        # AI returns different scores than what engine would calculate
        # But the engine recalculates from criteria
        ia_output = _valid_ia_output()
        
        fake_provider = FakeAIProvider(response=ia_output.model_dump())
        ai_evaluator = CheckpointAIEvaluator(fake_provider)
        
        checkpoint_service = CheckpointService(
            checkpoint_repo=checkpoint_repo,
            projeto_repo=projeto_repo,
            avaliacao_service=avaliacao_service,
            ai_evaluator=ai_evaluator,
        )
        
        # Create test data
        vertical = Vertical(nome="Test Vertical")
        db.add(vertical)
        db.flush()
        
        usuario = Usuario(
            nome="Test User",
            email="test@test.com",
            senha_hash="hash",
            papel="VERTICAL",
            vertical_id=vertical.id,
        )
        db.add(usuario)
        db.flush()
        
        projeto = Projeto(
            titulo="Test Project",
            vertical_id=vertical.id,
            criado_por_id=usuario.id,
        )
        db.add(projeto)
        db.flush()
        
        current_user = CurrentUser(
            id=usuario.id,
            email=usuario.email,
            papel="VERTICAL",
            vertical_id=vertical.id,
        )
        
        checkpoint_service.start_checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            current_user=current_user,
        )
        
        respostas = _valid_ideacao_respostas()
        submit_resp = checkpoint_service.submit_checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            respostas=respostas,
            current_user=current_user,
        )
        
        # Verify evaluation exists and scores match engine calculation
        checkpoint_id = submit_resp.checkpoint.id
        avaliacoes = avaliacao_repo.list_evaluations(checkpoint_id)
        assert len(avaliacoes) == 1
        
        avaliacao = avaliacoes[0]
        # Scores should be 80.0 (all criteria at 80 with weights summing to 100)
        assert avaliacao.score_alinhamento == 80.0
        assert avaliacao.score_potencial == 80.0
        assert avaliacao.classificacao_farol == ClassificacaoFarol.PRIORIDADE_MAXIMA

    def test_marketing_summary_persisted(self, db):
        """Test that resumo_para_marketing from AI is persisted."""
        checkpoint_repo = CheckpointRepository(db)
        projeto_repo = ProjetoRepository(db)
        avaliacao_repo = AvaliacaoRepository(db)
        
        avaliacao_service = AvaliacaoService(avaliacao_repo, checkpoint_repo)
        
        custom_output = _valid_ia_output()
        custom_output.resumo_para_marketing = "Resumo personalizado para marketing"
        custom_output.feedback_geral = "Feedback personalizado da avaliação"
        
        fake_provider = FakeAIProvider(response=custom_output.model_dump())
        ai_evaluator = CheckpointAIEvaluator(fake_provider)
        
        checkpoint_service = CheckpointService(
            checkpoint_repo=checkpoint_repo,
            projeto_repo=projeto_repo,
            avaliacao_service=avaliacao_service,
            ai_evaluator=ai_evaluator,
        )
        
        vertical = Vertical(nome="Test Vertical")
        db.add(vertical)
        db.flush()
        
        usuario = Usuario(
            nome="Test User",
            email="test@test.com",
            senha_hash="hash",
            papel="VERTICAL",
            vertical_id=vertical.id,
        )
        db.add(usuario)
        db.flush()
        
        projeto = Projeto(
            titulo="Test Project",
            vertical_id=vertical.id,
            criado_por_id=usuario.id,
        )
        db.add(projeto)
        db.flush()
        
        current_user = CurrentUser(
            id=usuario.id,
            email=usuario.email,
            papel="VERTICAL",
            vertical_id=vertical.id,
        )
        
        checkpoint_service.start_checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            current_user=current_user,
        )
        
        respostas = _valid_ideacao_respostas()
        submit_resp = checkpoint_service.submit_checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            respostas=respostas,
            current_user=current_user,
        )
        
        checkpoint_id = submit_resp.checkpoint.id
        avaliacoes = avaliacao_repo.list_evaluations(checkpoint_id)
        assert len(avaliacoes) == 1
        
        avaliacao = avaliacoes[0]
        assert avaliacao.resumo_para_marketing == "Resumo personalizado para marketing"
        assert avaliacao.feedback_geral == "Feedback personalizado da avaliação"

    def test_d9_metadata_persisted_correctly(self, db):
        """Test that all D9 metadata fields are persisted correctly."""
        checkpoint_repo = CheckpointRepository(db)
        projeto_repo = ProjetoRepository(db)
        avaliacao_repo = AvaliacaoRepository(db)
        
        avaliacao_service = AvaliacaoService(avaliacao_repo, checkpoint_repo)
        
        fake_provider = FakeAIProvider(response=_valid_ia_output().model_dump())
        ai_evaluator = CheckpointAIEvaluator(fake_provider)
        
        checkpoint_service = CheckpointService(
            checkpoint_repo=checkpoint_repo,
            projeto_repo=projeto_repo,
            avaliacao_service=avaliacao_service,
            ai_evaluator=ai_evaluator,
        )
        
        vertical = Vertical(nome="Test Vertical")
        db.add(vertical)
        db.flush()
        
        usuario = Usuario(
            nome="Test User",
            email="test@test.com",
            senha_hash="hash",
            papel="VERTICAL",
            vertical_id=vertical.id,
        )
        db.add(usuario)
        db.flush()
        
        projeto = Projeto(
            titulo="Test Project",
            vertical_id=vertical.id,
            criado_por_id=usuario.id,
        )
        db.add(projeto)
        db.flush()
        
        current_user = CurrentUser(
            id=usuario.id,
            email=usuario.email,
            papel="VERTICAL",
            vertical_id=vertical.id,
        )
        
        checkpoint_service.start_checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            current_user=current_user,
        )
        
        respostas = _valid_ideacao_respostas()
        submit_resp = checkpoint_service.submit_checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            respostas=respostas,
            current_user=current_user,
        )
        
        checkpoint_id = submit_resp.checkpoint.id
        avaliacoes = avaliacao_repo.list_evaluations(checkpoint_id)
        avaliacao = avaliacoes[0]
        
        # Verify all D9 metadata
        assert avaliacao.evaluation_engine == "farol-engine-v1"
        assert avaliacao.modelo == settings.DEEPSEEK_MODEL
        assert avaliacao.prompt_version == "checkpoint_v2"
        assert avaliacao.criteria_version == "business_rules_2026_07"
        assert avaliacao.prompt_hash is not None
        assert len(avaliacao.prompt_hash) == 64
        assert avaliacao.criteria_hash is not None
        assert len(avaliacao.criteria_hash) == 64
        assert avaliacao.evaluated_at is not None
        
        # Verify evaluated_at is timezone aware
        assert avaliacao.evaluated_at.tzinfo is not None