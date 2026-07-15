import pytest
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models import (
    Alerta,
    AvaliacaoCheckpoint,
    Checkpoint,
    Conversa,
    Mensagem,
    Projeto,
    Usuario,
    Vertical,
)
from app.models.enums import (
    AutorMensagem,
    ClassificacaoFarol,
    DecisaoHumana,
    PapelUsuario,
    StatusAlerta,
    StatusCheckpoint,
    StatusProjeto,
    TipoAlerta,
    TipoCheckpoint,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_import_models():
    assert Vertical is not None
    assert Usuario is not None
    assert Projeto is not None
    assert Checkpoint is not None
    assert AvaliacaoCheckpoint is not None
    assert Alerta is not None
    assert Conversa is not None
    assert Mensagem is not None


def test_metadata_contains_tables():
    tables = Base.metadata.tables
    expected = {
        "verticals",
        "usuarios",
        "projetos",
        "checkpoints",
        "avaliacoes_checkpoint",
        "alertas",
        "conversas",
        "mensagens",
    }
    assert expected.issubset(tables.keys())


def test_enums_values():
    assert list(PapelUsuario) == [
        PapelUsuario.VERTICAL,
        PapelUsuario.MARKETING,
        PapelUsuario.LIDERANCA,
        PapelUsuario.ADMIN,
    ]
    assert list(StatusProjeto) == [
        StatusProjeto.EM_IDEACAO,
        StatusProjeto.EM_DESENVOLVIMENTO,
        StatusProjeto.AGUARDANDO_PRE_LANCAMENTO,
        StatusProjeto.APROVADO_PARA_LANCAMENTO,
        StatusProjeto.LANCADO,
        StatusProjeto.EM_ALERTA,
        StatusProjeto.ENCERRADO,
    ]
    assert list(TipoCheckpoint) == [
        TipoCheckpoint.IDEACAO,
        TipoCheckpoint.DESENVOLVIMENTO,
        TipoCheckpoint.PRE_LANCAMENTO,
    ]
    assert list(StatusCheckpoint) == [
        StatusCheckpoint.PENDENTE,
        StatusCheckpoint.SUGERIDO,
        StatusCheckpoint.EM_PREENCHIMENTO,
        StatusCheckpoint.CONCLUIDO,
    ]
    assert list(ClassificacaoFarol) == [
        ClassificacaoFarol.PRIORIDADE_MAXIMA,
        ClassificacaoFarol.VALE_INVESTIR_TEMPO,
        ClassificacaoFarol.BAIXA_PRIORIDADE,
    ]
    assert list(TipoAlerta) == [
        TipoAlerta.COMPLIANCE_LEGAL,
        TipoAlerta.REPUTACAO_MARCA,
        TipoAlerta.POSSIVEL_DUPLICACAO,
        TipoAlerta.CUSTO_DESPROPORCIONAL,
        TipoAlerta.OUTRO,
    ]
    assert list(StatusAlerta) == [
        StatusAlerta.ABERTO,
        StatusAlerta.EM_ANALISE,
        StatusAlerta.RESOLVIDO,
        StatusAlerta.DESCARTADO,
    ]
    assert list(DecisaoHumana) == [
        DecisaoHumana.SOLICITAR_ADAPTACAO,
        DecisaoHumana.ENCERRAR_PROJETO,
        DecisaoHumana.PERMITIR_CONTINUIDADE,
    ]
    assert list(AutorMensagem) == [
        AutorMensagem.USUARIO,
        AutorMensagem.AGENTE,
        AutorMensagem.SISTEMA,
    ]


def test_create_vertical_and_user(db):
    vertical = Vertical(nome="Viagens", descricao="Vertical de viagens")
    db.add(vertical)
    db.flush()

    usuario = Usuario(
        nome="João Silva",
        email="joao@exemplo.com",
        senha_hash="hash123",
        papel=PapelUsuario.VERTICAL,
        vertical_id=vertical.id,
    )
    db.add(usuario)
    db.flush()

    assert usuario.vertical is not None
    assert usuario.vertical.nome == "Viagens"
    assert vertical.usuarios[0].nome == "João Silva"


def test_create_project(db):
    vertical = Vertical(nome="Conecta")
    db.add(vertical)
    db.flush()

    criador = Usuario(
        nome="Maria",
        email="maria@exemplo.com",
        senha_hash="hash456",
        papel=PapelUsuario.VERTICAL,
        vertical_id=vertical.id,
    )
    db.add(criador)
    db.flush()

    projeto = Projeto(
        titulo="App Conecta",
        descricao="Projeto de aplicativo",
        vertical_id=vertical.id,
        criado_por_id=criador.id,
    )
    db.add(projeto)
    db.flush()

    assert projeto.vertical.nome == "Conecta"
    assert projeto.criador.nome == "Maria"
    assert vertical.projetos[0].titulo == "App Conecta"


def test_checkpoint_unique_constraint(db):
    vertical = Vertical(nome="Fidelidade")
    db.add(vertical)
    db.flush()

    usuario = Usuario(
        nome="Admin",
        email="admin@exemplo.com",
        senha_hash="hash",
        papel=PapelUsuario.ADMIN,
    )
    db.add(usuario)
    db.flush()

    projeto = Projeto(
        titulo="Projeto Único",
        vertical_id=vertical.id,
        criado_por_id=usuario.id,
    )
    db.add(projeto)
    db.flush()

    cp1 = Checkpoint(projeto_id=projeto.id, tipo=TipoCheckpoint.IDEACAO)
    db.add(cp1)
    db.flush()

    cp2 = Checkpoint(projeto_id=projeto.id, tipo=TipoCheckpoint.IDEACAO)
    db.add(cp2)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db.flush()


def test_checkpoint_score_constraint(db):
    vertical = Vertical(nome="ScoreTest")
    db.add(vertical)
    db.flush()

    usuario = Usuario(
        nome="User",
        email="user@exemplo.com",
        senha_hash="hash",
        papel=PapelUsuario.VERTICAL,
        vertical_id=vertical.id,
    )
    db.add(usuario)
    db.flush()

    projeto = Projeto(
        titulo="Score Test",
        vertical_id=vertical.id,
        criado_por_id=usuario.id,
    )
    db.add(projeto)
    db.flush()

    cp = Checkpoint(projeto_id=projeto.id, tipo=TipoCheckpoint.IDEACAO)
    db.add(cp)
    db.flush()

    aval = AvaliacaoCheckpoint(
        checkpoint_id=cp.id,
        score_alinhamento=150,
        score_potencial=50,
    )
    db.add(aval)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db.flush()


def test_valid_scores(db):
    vertical = Vertical(nome="ValidScore")
    db.add(vertical)
    db.flush()

    usuario = Usuario(
        nome="User2",
        email="user2@exemplo.com",
        senha_hash="hash",
        papel=PapelUsuario.VERTICAL,
        vertical_id=vertical.id,
    )
    db.add(usuario)
    db.flush()

    projeto = Projeto(
        titulo="Valid Score",
        vertical_id=vertical.id,
        criado_por_id=usuario.id,
    )
    db.add(projeto)
    db.flush()

    cp = Checkpoint(projeto_id=projeto.id, tipo=TipoCheckpoint.IDEACAO)
    db.add(cp)
    db.flush()

    aval = AvaliacaoCheckpoint(
        checkpoint_id=cp.id,
        score_alinhamento=85,
        score_potencial=92,
        classificacao_farol=ClassificacaoFarol.VALE_INVESTIR_TEMPO,
    )
    db.add(aval)
    db.flush()
    assert aval.score_alinhamento == 85
    assert aval.score_potencial == 92
    assert aval.classificacao_farol == ClassificacaoFarol.VALE_INVESTIR_TEMPO


def test_conversa_e_mensagem(db):
    vertical = Vertical(nome="Teste")
    db.add(vertical)
    db.flush()

    usuario = Usuario(
        nome="User",
        email="user3@exemplo.com",
        senha_hash="hash",
        papel=PapelUsuario.VERTICAL,
        vertical_id=vertical.id,
    )
    db.add(usuario)
    db.flush()

    projeto = Projeto(
        titulo="Chat Test",
        vertical_id=vertical.id,
        criado_por_id=usuario.id,
    )
    db.add(projeto)
    db.flush()

    conversa = Conversa(projeto_id=projeto.id)
    db.add(conversa)
    db.flush()

    msg = Mensagem(
        conversa_id=conversa.id,
        autor_tipo=AutorMensagem.USUARIO,
        usuario_id=usuario.id,
        conteudo="Olá, agente!",
    )
    db.add(msg)
    db.flush()

    assert msg.conversa_id == conversa.id
    assert conversa.mensagens[0].conteudo == "Olá, agente!"
    assert conversa.projeto_id == projeto.id
    assert projeto.conversa is not None
