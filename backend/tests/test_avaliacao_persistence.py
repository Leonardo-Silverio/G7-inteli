import pytest
from uuid import UUID
from datetime import datetime, timezone

from app.models.checkpoint import AvaliacaoCheckpoint, Checkpoint
from app.models.enums import ClassificacaoFarol, StatusCheckpoint, TipoCheckpoint
from app.models.projeto import Projeto
from app.models.usuario import Usuario
from app.models.vertical import Vertical
from app.models.anexo_checkpoint import AnexoCheckpoint
from app.repositories.avaliacao_repository import AvaliacaoRepository
from app.repositories.checkpoint_repository import CheckpointRepository
from app.services.avaliacao_service import AvaliacaoService, CheckpointNotFoundError
from app.services.evaluation_engine import EvaluationEngine
from app.schemas.avaliacao import (
    AvaliacaoCalculada,
    AvaliacaoIAOutput,
    CriterioAvaliacao,
    CriteriosAlinhamento,
    CriteriosPotencial,
    ClassificacaoFarol as SchemaClassificacaoFarol,
    ContribuicaoCriterio,
    FeedbackItem,
)
from app.schemas.avaliacao_response import (
    AvaliacaoCheckpointResponse,
    AvaliacaoHistoryResponse,
    AvaliacaoLatestResponse,
)


def _criterio_valido(nota: float = 80) -> CriterioAvaliacao:
    return CriterioAvaliacao(
        nota=nota,
        feedback="Feedback do criterio",
        evidencias=["ev1"],
        sugestoes=["sg1"],
        confianca=90,
    )


def _alinhamento_todos(nota: float) -> CriteriosAlinhamento:
    c = _criterio_valido(nota)
    return CriteriosAlinhamento(
        tom_de_voz_azul=c,
        identidade_visual_azul=c,
        posicionamento_malha_regional=c,
        uso_correto_produtos_marca=c,
        seguranca_solidez=c,
        clareza_passageiro=c,
    )


def _potencial_todos(nota: float) -> CriteriosPotencial:
    c = _criterio_valido(nota)
    return CriteriosPotencial(
        pilares_estrategicos_atuais=c,
        receita_produtos_proprios=c,
        alcance_malha_regional=c,
        diferenciacao_gol_latam=c,
        recuperacao_fidelizacao_cliente=c,
        viabilidade_operacional=c,
    )


def _ia_output(alinhamento: float = 80, potencial: float = 80) -> AvaliacaoIAOutput:
    return AvaliacaoIAOutput(
        criterios_alinhamento=_alinhamento_todos(alinhamento),
        criterios_potencial=_potencial_todos(potencial),
        feedback_geral="Feedback geral da avaliacao",
        resumo_para_marketing="Resumo para marketing",
        pontos_fortes=[FeedbackItem(titulo="Pf1", descricao="Ponto forte 1")],
        oportunidades_melhoria=[FeedbackItem(titulo="Op1", descricao="Oportunidade 1")],
        recomendacoes_praticas=[FeedbackItem(titulo="Re1", descricao="Recomendacao 1")],
        proximos_passos=["Proximo passo"],
        riscos_principais=[FeedbackItem(titulo="Ri1", descricao="Risco 1", prioridade="BAIXA")],
    )


class TestAvaliacaoRepository:
    def test_create_evaluation(self, db):
        repo = AvaliacaoRepository(db)

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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        avaliacao = AvaliacaoCheckpoint(
            checkpoint_id=checkpoint.id,
            score_alinhamento=85,
            score_potencial=90,
            classificacao_farol=ClassificacaoFarol.PRIORIDADE_MAXIMA,
            criterios_alinhamento={"test": "data"},
            criterios_potencial={"test": "data"},
            feedback_geral="Test feedback",
            resumo_para_marketing="Test resumo",
            evaluation_engine="farol-engine-v1",
            modelo="gpt-4o",
            prompt_version="v1",
            criteria_version="v1",
            prompt_hash="a" * 64,
            criteria_hash="b" * 64,
            evaluated_at=datetime.now(timezone.utc),
        )

        created = repo.create_evaluation(avaliacao)
        assert created.id is not None
        assert created.checkpoint_id == checkpoint.id
        assert created.score_alinhamento == 85
        assert created.modelo == "gpt-4o"
        assert created.evaluated_at is not None

    def test_get_evaluation_by_id(self, db):
        repo = AvaliacaoRepository(db)

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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        avaliacao = AvaliacaoCheckpoint(
            checkpoint_id=checkpoint.id,
            score_alinhamento=85,
            score_potencial=90,
            classificacao_farol=ClassificacaoFarol.PRIORIDADE_MAXIMA,
            criterios_alinhamento={},
            criterios_potencial={},
            evaluation_engine="farol-engine-v1",
            modelo="gpt-4o",
            prompt_version="v1",
            criteria_version="v1",
            prompt_hash="a" * 64,
            criteria_hash="b" * 64,
            evaluated_at=datetime.now(timezone.utc),
        )
        db.add(avaliacao)
        db.flush()

        found = repo.get_evaluation(avaliacao.id)
        assert found is not None
        assert found.id == avaliacao.id
        assert found.score_alinhamento == 85

    def test_list_evaluations_by_checkpoint_order(self, db):
        repo = AvaliacaoRepository(db)

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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        base_time = datetime.now(timezone.utc)
        for i in range(3):
            avaliacao = AvaliacaoCheckpoint(
                checkpoint_id=checkpoint.id,
                score_alinhamento=70 + i * 5,
                score_potencial=70 + i * 5,
                classificacao_farol=ClassificacaoFarol.VALE_INVESTIR_TEMPO,
                criterios_alinhamento={},
                criterios_potencial={},
                evaluation_engine="farol-engine-v1",
                modelo="gpt-4o",
                prompt_version=f"v{i+1}",
                criteria_version="v1",
                prompt_hash="a" * 64,
                criteria_hash="b" * 64,
                evaluated_at=base_time.replace(microsecond=i * 1000),
            )
            db.add(avaliacao)
        db.flush()

        avaliacoes = repo.list_evaluations(checkpoint.id)
        assert len(avaliacoes) == 3
        assert avaliacoes[0].evaluated_at > avaliacoes[1].evaluated_at
        assert avaliacoes[1].evaluated_at > avaliacoes[2].evaluated_at

    def test_get_latest_evaluation(self, db):
        repo = AvaliacaoRepository(db)

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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        for i in range(3):
            avaliacao = AvaliacaoCheckpoint(
                checkpoint_id=checkpoint.id,
                score_alinhamento=70 + i * 5,
                score_potencial=70 + i * 5,
                classificacao_farol=ClassificacaoFarol.VALE_INVESTIR_TEMPO,
                criterios_alinhamento={},
                criterios_potencial={},
                evaluation_engine="farol-engine-v1",
                modelo="gpt-4o",
                prompt_version=f"v{i+1}",
                criteria_version="v1",
                prompt_hash="a" * 64,
                criteria_hash="b" * 64,
                evaluated_at=datetime.now(timezone.utc),
            )
            db.add(avaliacao)
        db.flush()

        latest = repo.get_latest_evaluation(checkpoint.id)
        assert latest is not None
        assert latest.score_alinhamento == 80

    def test_count_evaluations_by_checkpoint(self, db):
        repo = AvaliacaoRepository(db)

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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        for i in range(2):
            avaliacao = AvaliacaoCheckpoint(
                checkpoint_id=checkpoint.id,
                score_alinhamento=70,
                score_potencial=70,
                classificacao_farol=ClassificacaoFarol.VALE_INVESTIR_TEMPO,
                criterios_alinhamento={},
                criterios_potencial={},
                evaluation_engine="farol-engine-v1",
                modelo="gpt-4o",
                prompt_version=f"v{i+1}",
                criteria_version="v1",
                prompt_hash="a" * 64,
                criteria_hash="b" * 64,
                evaluated_at=datetime.now(timezone.utc),
            )
            db.add(avaliacao)
        db.flush()

        count = repo.count_evaluations(checkpoint.id)
        assert count == 2


class TestAvaliacaoService:
    def test_create_evaluation(self, db):
        avaliacao_repo = AvaliacaoRepository(db)
        checkpoint_repo = CheckpointRepository(db)
        service = AvaliacaoService(avaliacao_repo, checkpoint_repo)

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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        ia_output = _ia_output(alinhamento=85, potencial=90)

        result = service.create_evaluation(
            checkpoint_id=checkpoint.id,
            ia_output=ia_output,
            modelo="gpt-4o",
            prompt_version="checkpoint1_v1",
            criteria_version="business_rules_2026_07",
            prompt_hash="a" * 64,
            criteria_hash="b" * 64,
        )

        assert isinstance(result, AvaliacaoCheckpointResponse)
        assert result.checkpoint_id == checkpoint.id
        assert result.score_alinhamento == 85.0
        assert result.score_potencial == 90.0
        assert result.classificacao_farol == ClassificacaoFarol.PRIORIDADE_MAXIMA
        assert result.modelo == "gpt-4o"
        assert result.prompt_version == "checkpoint1_v1"
        assert result.evaluation_engine == "farol-engine-v1"

    def test_create_evaluation_checkpoint_not_found(self, db):
        avaliacao_repo = AvaliacaoRepository(db)
        checkpoint_repo = CheckpointRepository(db)
        service = AvaliacaoService(avaliacao_repo, checkpoint_repo)

        ia_output = _ia_output()

        with pytest.raises(CheckpointNotFoundError):
            service.create_evaluation(
                checkpoint_id=UUID("00000000-0000-0000-0000-000000000000"),
                ia_output=ia_output,
                modelo="gpt-4o",
                prompt_version="v1",
                criteria_version="v1",
                prompt_hash="a" * 64,
                criteria_hash="b" * 64,
            )

    def test_append_only_two_evaluations_same_checkpoint(self, db):
        avaliacao_repo = AvaliacaoRepository(db)
        checkpoint_repo = CheckpointRepository(db)
        service = AvaliacaoService(avaliacao_repo, checkpoint_repo)

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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        ia_output_1 = _ia_output(alinhamento=70, potencial=65)
        result_1 = service.create_evaluation(
            checkpoint_id=checkpoint.id,
            ia_output=ia_output_1,
            modelo="gpt-4o",
            prompt_version="v1",
            criteria_version="v1",
            prompt_hash="a" * 64,
            criteria_hash="b" * 64,
        )

        ia_output_2 = _ia_output(alinhamento=85, potencial=80)
        result_2 = service.create_evaluation(
            checkpoint_id=checkpoint.id,
            ia_output=ia_output_2,
            modelo="gpt-5",
            prompt_version="v2",
            criteria_version="v2",
            prompt_hash="c" * 64,
            criteria_hash="d" * 64,
        )

        assert result_1.id != result_2.id
        assert result_1.score_alinhamento == 70.0
        assert result_2.score_alinhamento == 85.0
        assert result_1.modelo == "gpt-4o"
        assert result_2.modelo == "gpt-5"

        avaliacoes = avaliacao_repo.list_evaluations(checkpoint.id)
        assert len(avaliacoes) == 2

    def test_get_latest_evaluation(self, db):
        avaliacao_repo = AvaliacaoRepository(db)
        checkpoint_repo = CheckpointRepository(db)
        service = AvaliacaoService(avaliacao_repo, checkpoint_repo)

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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        service.create_evaluation(
            checkpoint_id=checkpoint.id,
            ia_output=_ia_output(70, 65),
            modelo="gpt-4o",
            prompt_version="v1",
            criteria_version="v1",
            prompt_hash="a" * 64,
            criteria_hash="b" * 64,
        )
        service.create_evaluation(
            checkpoint_id=checkpoint.id,
            ia_output=_ia_output(85, 80),
            modelo="gpt-5",
            prompt_version="v2",
            criteria_version="v2",
            prompt_hash="c" * 64,
            criteria_hash="d" * 64,
        )

        latest = service.get_latest(checkpoint.id)
        assert latest.avaliacao is not None
        assert latest.avaliacao.score_alinhamento == 85.0
        assert latest.avaliacao.modelo == "gpt-5"
        assert latest.total_historico == 2

    def test_list_history(self, db):
        avaliacao_repo = AvaliacaoRepository(db)
        checkpoint_repo = CheckpointRepository(db)
        service = AvaliacaoService(avaliacao_repo, checkpoint_repo)

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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        service.create_evaluation(
            checkpoint_id=checkpoint.id,
            ia_output=_ia_output(70, 65),
            modelo="gpt-4o",
            prompt_version="v1",
            criteria_version="v1",
            prompt_hash="a" * 64,
            criteria_hash="b" * 64,
        )
        service.create_evaluation(
            checkpoint_id=checkpoint.id,
            ia_output=_ia_output(85, 80),
            modelo="gpt-5",
            prompt_version="v2",
            criteria_version="v2",
            prompt_hash="c" * 64,
            criteria_hash="d" * 64,
        )

        history = service.list_history(checkpoint.id)
        assert history.total == 2
        assert len(history.items) == 2
        assert history.items[0].modelo == "gpt-5"
        assert history.items[1].modelo == "gpt-4o"

    def test_scores_persisted_correctly(self, db):
        avaliacao_repo = AvaliacaoRepository(db)
        checkpoint_repo = CheckpointRepository(db)
        service = AvaliacaoService(avaliacao_repo, checkpoint_repo)

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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        alinhamento = CriteriosAlinhamento(
            tom_de_voz_azul=_criterio_valido(100),
            identidade_visual_azul=_criterio_valido(80),
            posicionamento_malha_regional=_criterio_valido(60),
            uso_correto_produtos_marca=_criterio_valido(40),
            seguranca_solidez=_criterio_valido(20),
            clareza_passageiro=_criterio_valido(0),
        )
        potencial = CriteriosPotencial(
            pilares_estrategicos_atuais=_criterio_valido(100),
            receita_produtos_proprios=_criterio_valido(80),
            alcance_malha_regional=_criterio_valido(60),
            diferenciacao_gol_latam=_criterio_valido(40),
            recuperacao_fidelizacao_cliente=_criterio_valido(20),
            viabilidade_operacional=_criterio_valido(0),
        )
        ia_output = AvaliacaoIAOutput(
            criterios_alinhamento=alinhamento,
            criterios_potencial=potencial,
            feedback_geral="Feedback",
            resumo_para_marketing="Resumo",
            pontos_fortes=[FeedbackItem(titulo="Pf1", descricao="Ponto forte 1")],
            oportunidades_melhoria=[FeedbackItem(titulo="Op1", descricao="Oportunidade 1")],
            recomendacoes_praticas=[FeedbackItem(titulo="Re1", descricao="Recomendacao 1")],
            proximos_passos=["Proximo passo"],
        )

        result = service.create_evaluation(
            checkpoint_id=checkpoint.id,
            ia_output=ia_output,
            modelo="gpt-4o",
            prompt_version="v1",
            criteria_version="v1",
            prompt_hash="a" * 64,
            criteria_hash="b" * 64,
        )

        assert result.score_alinhamento == 61.0
        assert result.score_potencial == 59.0

    def test_classificacao_persistida_corretamente(self, db):
        avaliacao_repo = AvaliacaoRepository(db)
        checkpoint_repo = CheckpointRepository(db)
        service = AvaliacaoService(avaliacao_repo, checkpoint_repo)

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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        result = service.create_evaluation(
            checkpoint_id=checkpoint.id,
            ia_output=_ia_output(100, 59.99),
            modelo="gpt-4o",
            prompt_version="v1",
            criteria_version="v1",
            prompt_hash="a" * 64,
            criteria_hash="b" * 64,
        )

        assert result.classificacao_farol == ClassificacaoFarol.BAIXA_PRIORIDADE

        result2 = service.create_evaluation(
            checkpoint_id=checkpoint.id,
            ia_output=_ia_output(69.99, 60),
            modelo="gpt-4o",
            prompt_version="v2",
            criteria_version="v2",
            prompt_hash="c" * 64,
            criteria_hash="d" * 64,
        )

        assert result2.classificacao_farol == ClassificacaoFarol.VALE_INVESTIR_TEMPO

        result3 = service.create_evaluation(
            checkpoint_id=checkpoint.id,
            ia_output=_ia_output(70, 60),
            modelo="gpt-4o",
            prompt_version="v3",
            criteria_version="v3",
            prompt_hash="e" * 64,
            criteria_hash="f" * 64,
        )

        assert result3.classificacao_farol == ClassificacaoFarol.PRIORIDADE_MAXIMA

    def test_audit_fields_persisted(self, db):
        avaliacao_repo = AvaliacaoRepository(db)
        checkpoint_repo = CheckpointRepository(db)
        service = AvaliacaoService(avaliacao_repo, checkpoint_repo)

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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        result = service.create_evaluation(
            checkpoint_id=checkpoint.id,
            ia_output=_ia_output(),
            modelo="gpt-4o",
            prompt_version="checkpoint1_v1",
            criteria_version="business_rules_2026_07",
            prompt_hash="a" * 64,
            criteria_hash="b" * 64,
        )

        assert result.evaluation_engine == "farol-engine-v1"
        assert result.modelo == "gpt-4o"
        assert result.prompt_version == "checkpoint1_v1"
        assert result.criteria_version == "business_rules_2026_07"
        assert result.prompt_hash == "a" * 64
        assert result.criteria_hash == "b" * 64
        assert result.evaluated_at is not None

    def test_criteria_json_preserved(self, db):
        avaliacao_repo = AvaliacaoRepository(db)
        checkpoint_repo = CheckpointRepository(db)
        service = AvaliacaoService(avaliacao_repo, checkpoint_repo)

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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        alinhamento = CriteriosAlinhamento(
            tom_de_voz_azul=_criterio_valido(80),
            identidade_visual_azul=_criterio_valido(80),
            posicionamento_malha_regional=_criterio_valido(80),
            uso_correto_produtos_marca=_criterio_valido(80),
            seguranca_solidez=_criterio_valido(80),
            clareza_passageiro=_criterio_valido(80),
        )
        potencial = CriteriosPotencial(
            pilares_estrategicos_atuais=_criterio_valido(80),
            receita_produtos_proprios=_criterio_valido(80),
            alcance_malha_regional=_criterio_valido(80),
            diferenciacao_gol_latam=_criterio_valido(80),
            recuperacao_fidelizacao_cliente=_criterio_valido(80),
            viabilidade_operacional=_criterio_valido(80),
        )
        ia_output = AvaliacaoIAOutput(
            criterios_alinhamento=alinhamento,
            criterios_potencial=potencial,
            feedback_geral="Feedback",
            resumo_para_marketing="Resumo",
            pontos_fortes=[FeedbackItem(titulo="Pf1", descricao="Ponto forte 1")],
            oportunidades_melhoria=[FeedbackItem(titulo="Op1", descricao="Oportunidade 1")],
            recomendacoes_praticas=[FeedbackItem(titulo="Re1", descricao="Recomendacao 1")],
            proximos_passos=["Proximo passo"],
        )

        result = service.create_evaluation(
            checkpoint_id=checkpoint.id,
            ia_output=ia_output,
            modelo="gpt-4o",
            prompt_version="v1",
            criteria_version="v1",
            prompt_hash="a" * 64,
            criteria_hash="b" * 64,
        )

        assert result.criterios_alinhamento.tom_de_voz_azul.nota == 80
        assert result.criterios_potencial.pilares_estrategicos_atuais.nota == 80


class TestCheckpointAvaliacoesRelationship:
    def test_feedback_json_persisted_with_schema_version(self, db):
        avaliacao_repo = AvaliacaoRepository(db)
        checkpoint_repo = CheckpointRepository(db)
        service = AvaliacaoService(avaliacao_repo, checkpoint_repo)

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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        result = service.create_evaluation(
            checkpoint_id=checkpoint.id,
            ia_output=_ia_output(),
            modelo="gpt-4o",
            prompt_version="checkpoint_v2",
            criteria_version="business_rules_2026_07",
            prompt_hash="a" * 64,
            criteria_hash="b" * 64,
        )

        assert result.feedback is not None
        assert result.feedback.schema_version == "feedback_v1"
        assert len(result.feedback.pontos_fortes) > 0
        assert len(result.feedback.oportunidades_melhoria) > 0
        assert len(result.feedback.recomendacoes_praticas) > 0
        assert result.feedback.justificativa_classificacao != ""
        assert "PRIORIDADE" in result.feedback.justificativa_classificacao.upper()

    def _valid_criterios_dict(self) -> dict:
        c = {"nota": 80, "feedback": "Ok", "evidencias": [], "sugestoes": [], "confianca": 90}
        return {k: dict(c) for k in [
            "tom_de_voz_azul", "identidade_visual_azul", "posicionamento_malha_regional",
            "uso_correto_produtos_marca", "seguranca_solidez", "clareza_passageiro"
        ]}

    def _valid_potencial_dict(self) -> dict:
        c = {"nota": 80, "feedback": "Ok", "evidencias": [], "sugestoes": [], "confianca": 90}
        return {k: dict(c) for k in [
            "pilares_estrategicos_atuais", "receita_produtos_proprios", "alcance_malha_regional",
            "diferenciacao_gol_latam", "recuperacao_fidelizacao_cliente", "viabilidade_operacional"
        ]}

    def test_feedback_json_includes_scores_in_justificativa(self, db):
        avaliacao_repo = AvaliacaoRepository(db)
        checkpoint_repo = CheckpointRepository(db)
        service = AvaliacaoService(avaliacao_repo, checkpoint_repo)

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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        result = service.create_evaluation(
            checkpoint_id=checkpoint.id,
            ia_output=_ia_output(alinhamento=100, potencial=59.99),
            modelo="gpt-4o",
            prompt_version="checkpoint_v2",
            criteria_version="business_rules_2026_07",
            prompt_hash="a" * 64,
            criteria_hash="b" * 64,
        )

        assert result.classificacao_farol == ClassificacaoFarol.BAIXA_PRIORIDADE
        assert result.feedback is not None
        assert "BAIXA" in result.feedback.justificativa_classificacao.upper()
        assert "BAIXA PRIORIDADE" in result.feedback.justificativa_classificacao
        assert "100" in result.feedback.justificativa_classificacao

    def test_old_evaluation_without_feedback_json_still_readable(self, db):
        avaliacao_repo = AvaliacaoRepository(db)
        checkpoint_repo = CheckpointRepository(db)
        service = AvaliacaoService(avaliacao_repo, checkpoint_repo)

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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        # Create evaluation directly without feedback_json (simulating old record)
        old_avaliacao = AvaliacaoCheckpoint(
            checkpoint_id=checkpoint.id,
            score_alinhamento=80,
            score_potencial=80,
            classificacao_farol=ClassificacaoFarol.PRIORIDADE_MAXIMA,
            criterios_alinhamento=self._valid_criterios_dict(),
            criterios_potencial=self._valid_potencial_dict(),
            feedback_geral="Old feedback",
            resumo_para_marketing="Old resumo",
            feedback_json=None,
            evaluation_engine="farol-engine-v1",
            modelo="gpt-4o",
            prompt_version="checkpoint_v1",
            criteria_version="business_rules_2026_07",
            prompt_hash="a" * 64,
            criteria_hash="b" * 64,
            evaluated_at=datetime.now(timezone.utc),
        )
        db.add(old_avaliacao)
        db.flush()

        # Read back via service response
        latest = service.get_latest(checkpoint.id)
        assert latest.avaliacao is not None
        assert latest.avaliacao.feedback_geral == "Old feedback"
        assert latest.avaliacao.feedback is None

    def test_append_only_preserved_with_new_fields(self, db):
        avaliacao_repo = AvaliacaoRepository(db)
        checkpoint_repo = CheckpointRepository(db)
        service = AvaliacaoService(avaliacao_repo, checkpoint_repo)

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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        r1 = service.create_evaluation(
            checkpoint_id=checkpoint.id,
            ia_output=_ia_output(70, 65),
            modelo="gpt-4o",
            prompt_version="v1",
            criteria_version="v1",
            prompt_hash="a" * 64,
            criteria_hash="b" * 64,
        )
        r2 = service.create_evaluation(
            checkpoint_id=checkpoint.id,
            ia_output=_ia_output(85, 80),
            modelo="gpt-5",
            prompt_version="v2",
            criteria_version="v2",
            prompt_hash="c" * 64,
            criteria_hash="d" * 64,
        )

        assert r1.id != r2.id
        assert r2.score_alinhamento == 85.0
        assert r2.feedback is not None
        assert r2.feedback.schema_version == "feedback_v1"

        history = service.list_history(checkpoint.id)
        assert history.total == 2

    def test_checkpoint_has_avaliacoes_relationship(self, db):
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

        checkpoint = Checkpoint(
            projeto_id=projeto.id,
            tipo=TipoCheckpoint.IDEACAO,
            status=StatusCheckpoint.CONCLUIDO,
        )
        db.add(checkpoint)
        db.flush()

        for i in range(2):
            avaliacao = AvaliacaoCheckpoint(
                checkpoint_id=checkpoint.id,
                score_alinhamento=70 + i * 10,
                score_potencial=70 + i * 10,
                classificacao_farol=ClassificacaoFarol.VALE_INVESTIR_TEMPO,
                criterios_alinhamento={},
                criterios_potencial={},
                evaluation_engine="farol-engine-v1",
                modelo="gpt-4o",
                prompt_version=f"v{i+1}",
                criteria_version="v1",
                prompt_hash="a" * 64,
                criteria_hash="b" * 64,
                evaluated_at=datetime.now(timezone.utc),
            )
            db.add(avaliacao)
        db.flush()

        loaded_checkpoint = db.query(Checkpoint).filter(Checkpoint.id == checkpoint.id).first()
        assert len(loaded_checkpoint.avaliacoes) == 2
        assert loaded_checkpoint.avaliacoes[0].modelo == "gpt-4o"