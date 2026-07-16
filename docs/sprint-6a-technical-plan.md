# Plano Técnico — Sprint 6A: Checkpoints, Formulários e Anexos

**Projeto Farol** | Sprint 6A | Arquitetura & Planejamento Técnico  
**Data:** 2026-07-15  
**Status:** Para aprovação — NÃO implementar ainda

---

## 1. O que já existe e será reutilizado

### 1.1 Models já implementados (`backend/app/models/`)

| Modelo | Status | Observações |
|--------|--------|-------------|
| `Checkpoint` | ✅ Completo | `projeto_id`, `tipo` (enum), `status` (enum), `sugerido_em`, `iniciado_em`, `concluido_em`, `respostas_formulario` (JSON), `resumo_para_marketing` (Text), timestamps, `UniqueConstraint(projeto_id, tipo)` |
| `AvaliacaoCheckpoint` | ✅ Completo | Para Sprint 6B (IA/scores) |
| `Projeto` | ✅ Completo | `vertical_id`, `criado_por_id`, `status` (StatusProjeto), relacionamento `checkpoints` |
| `Usuario` | ✅ Completo | `papel` (PapelUsuario), `vertical_id` |
| `Vertical` | ✅ Completo | 6 verticais oficiais já cadastradas via seed |
| `Conversa` / `Mensagem` | ✅ Completo | Conversa privada do criador |

### 1.2 Enums já definidos (`backend/app/models/enums.py`)

```python
class TipoCheckpoint(StrEnum):
    IDEACAO = "IDEACAO"
    DESENVOLVIMENTO = "DESENVOLVIMENTO"
    PRE_LANCAMENTO = "PRE_LANCAMENTO"

class StatusCheckpoint(StrEnum):
    PENDENTE = "PENDENTE"
    SUGERIDO = "SUGERIDO"
    EM_PREENCHIMENTO = "EM_PREENCHIMENTO"
    CONCLUIDO = "CONCLUIDO"

class PapelUsuario(StrEnum):
    VERTICAL = "VERTICAL"
    MARKETING = "MARKETING"
    LIDERANCA = "LIDERANCA"
    ADMIN = "ADMIN"
```

### 1.3 Infraestrutura existente

- **FastAPI** + **SQLAlchemy 2.0** + **Alembic** + **PostgreSQL**
- **Auth JWT** com `CurrentUser` (id, email, papel, vertical_id)
- **Repository Pattern**: `ProjetoRepository`, `UserRepository`
- **Service Layer**: `ProjetoService`, `AuthService`
- **Routes**: `/projetos`, `/auth`, `/users`
- **Schemas Pydantic**: `ProjetoCreate`, `ProjetoUpdate`, `ProjetoResponse`, `MensagemCreate`, etc.
- **Testes**: `pytest` + `TestClient` + fixtures `db` + `clean_db`
- **Migrações**: `0001_initial_migration.py`, `0002_update_status_projeto_enum.py`
- **Documentação**: `docs/business-rules.md`, `docs/database-model.md`

---

## 2. Incompatibilidades reais encontradas

| Item | Atual | Necessário para Sprint 6A | Ação |
|------|-------|---------------------------|------|
| `StatusCheckpoint` enum | `PENDENTE, SUGERIDO, EM_PREENCHIMENTO, CONCLUIDO` | Precisa de `AGUARDANDO_AVALIACAO` entre `EM_PREENCHIMENTO` e `CONCLUIDO` | **Migration futura** (Sprint 6B) — não implementar agora; manter `CONCLUIDO` = "enviado e validado" na 6A |
| `Checkpoint.respostas_formulario` | `JSON` sem estrutura definida | Precisa de schema versionado (`versao_formulario`, `tipo_checkpoint`, `respostas`, `anexos`, `enviado_em`, `atualizado_em`) | **Schema Pydantic + validação no Service** — sem migration |
| Tabela `anexos_checkpoint` | Não existe | Necessária para anexos (storage local v1, S3-compatível v2) | **Nova migration** (planejada abaixo) |
| `StatusCheckpoint.CONCLUIDO` | Significa "finalizado" | Na 6A = "formulário enviado e validado"; na 6B = "avaliação IA salva" | **Decisão de negócio**: manter `CONCLUIDO` na 6A; 6B adiciona `AGUARDANDO_AVALIACAO` via migration |
| Regras de ordem (Ideação → Desenvolvimento → Pré-lançamento) | Documentadas em `business-rules.md` mas **não implementadas** | Validar no Service antes de `iniciar`/`enviar` | **Implementar no Service** |
| Criação automática dos 3 checkpoints | Não existe (criação sob demanda) | Criar os 3 ao criar projeto OU criar sob demanda no `iniciar` | **Decisão**: criar sob demanda no `iniciar` (evita lixo) |

---

## 3. Decisão: JSON estruturado em `Checkpoint.respostas_formulario`

### 3.1 Estrutura padrão (versionada)

```json
{
  "versao_formulario": "ideacao_v1",
  "tipo_checkpoint": "IDEACAO",
  "respostas": {
    "descricao_projeto": "string",
    "proposta_solucao": "string",
    "focos_azul": ["MALHA_REGIONAL"],
    "impacto_rotas": "ROTAS_REGIONAIS",
    "existe_semelhante": true,
    "semelhante_descricao": "string",
    "prazo_mercado": "1_3_MESES",
    "dependencia_critica": false,
    "dependencia_descricao": "string",
    "diferencial": "string",
    "info_nao_compartilhada": false,
    "info_nao_compartilhada_descricao": "string"
  },
  "anexos": [
    {"anexo_id": "uuid", "nome_original": "arquivo.pdf", "mime_type": "application/pdf"}
  ],
  "enviado_em": "2026-07-15T10:30:00Z",
  "atualizado_em": "2026-07-15T10:30:00Z"
}
```

### 3.2 Vantagens

| Vantagem | Descrição |
|----------|-----------|
| **Evolução sem migration** | Nova versão do formulário = novo `versao_formulario`; JSON antigo continua válido |
| **Flexibilidade por checkpoint** | Cada tipo tem estrutura própria; sem tabelas esparsas |
| **Versionamento nativo** | Histórico de versões no próprio JSON; auditoria trivial |
| **Anexos referenciados** | Apenas metadados no JSON; binários em storage/tabela `anexos_checkpoint` |
| **Performance** | Single-row read; sem JOINs para ler respostas |
| **Compatível com IA** | JSON estruturado alimenta prompts futuros direto |

### 3.3 Limitações e mitigações

| Limitação | Mitigação |
|-----------|-----------|
| **Validação no banco** | Check constraints limitados; validação forte no **Service/Schema** (Pydantic) |
| **Query por campo interno** | Não filtrar por campo interno no SQL; usar busca full-text ou extrair para colunas se necessário no futuro |
| **Tamanho do JSON** | PostgreSQL `JSONB` suporta ~1GB; formulários ~KB — irrelevante |
| **Migração de versões antigas** | Service lê `versao_formulario` e aplica transformação no read (adapter pattern) |

**Decisão**: **Manter JSON versionado em `respostas_formulario`**. Não criar tabelas por pergunta.

---

## 4. Estrutura de cada formulário (Schemas Pydantic)

### 4.1 Enums compartilhados (novo arquivo: `backend/app/schemas/checkpoint_enums.py`)

```python
class FocoAzul(str, Enum):
    RECONQUISTA_CLIENTE = "RECONQUISTA_CLIENTE"
    FORTALECIMENTO_MALHA_REGIONAL = "FORTALECIMENTO_MALHA_REGIONAL"
    DIVERSIFICACAO_RECEITA = "DIVERSIFICACAO_RECEITA"
    DISCIPLINA_FINANCEIRA = "DISCIPLINA_FINANCEIRA"
    NENHUM = "NENHUM"

class ImpactoRotas(str, Enum):
    REGIONAIS = "ROTAS_REGIONAIS"
    PRINCIPAIS_COMPETITIVAS = "ROTAS_PRINCIPAIS_COMPETITIVAS"
    AMBAS = "AMBAS"
    NAO_ROTAS = "NAO_E_SOBRE_ROTAS"

class PrazoMercado(str, Enum):
    ATE_1_MES = "ATE_1_MES"
    DE_1_A_3_MESES = "1_3_MESES"
    DE_3_A_6_MESES = "3_6_MESES"
    MAIS_DE_6_MESES = "MAIS_6_MESES"

class ProdutoAzul(str, Enum):
    AZUL_FIDELIDADE = "AZUL_FIDELIDADE"
    AZUL_VIAGENS = "AZUL_VIAGENS"
    AZUL_CARGO = "AZUL_CARGO"
    AZUL_EMPRESAS = "AZUL_EMPRESAS"
    NENHUM = "NENHUM"

class TomEscala(int, Enum):
    MUITO_PROXIMO = 1
    PROXIMO = 2
    NEUTRO = 3
    FORMAL = 4
    MUITO_FORMAL = 5

class AreasAcordo(str, Enum):
    SIM = "SIM"
    PARCIALMENTE = "PARCIALMENTE"
    NAO = "NAO"

class RevisaoJuridica(str, Enum):
    SIM = "SIM"
    NAO = "NAO"

class ComparadoCampanhas(str, Enum):
    SIM = "SIM"
    NAO = "NAO"

class SimNaoParcial(str, Enum):
    SIM = "SIM"
    PARCIALMENTE = "PARCIALMENTE"
    NAO = "NAO"
```

### 4.2 Checkpoint 1 — IDEACAO (`ideacao_v1`)

```python
# backend/app/schemas/checkpoint_forms.py

class CheckpointIdeacaoRespostas(BaseModel):
    # Obrigatórios
    descricao_projeto: str = Field(..., min_length=10, max_length=500, description="2-3 frases: o que é o projeto e por que deveria existir")
    proposta_solucao: str = Field(..., min_length=10, max_length=500, description="2-3 frases: proposta da solução")
    focos_azul: list[FocoAzul] = Field(..., min_length=1, description="Múltipla escolha")
    impacto_rotas: ImpactoRotas = Field(...)
    
    # Condicional: existe_semelhante
    existe_semelhante: bool = Field(...)
    semelhante_descricao: str | None = Field(None, max_length=300)
    
    # Obrigatório
    prazo_mercado: PrazoMercado = Field(...)
    
    # Condicional: dependencia_critica
    dependencia_critica: bool = Field(...)
    dependencia_descricao: str | None = Field(None, max_length=300)
    
    # Obrigatório
    diferencial: str = Field(..., min_length=10, max_length=1000)
    
    # Condicional: info_nao_compartilhada
    info_nao_compartilhada: bool = Field(...)
    info_nao_compartilhada_descricao: str | None = Field(None, max_length=300)

    @field_validator("semelhante_descricao")
    @classmethod
    def validar_semelhante(cls, v, info):
        if info.data.get("existe_semelhante") and not v:
            raise ValueError("Descrição obrigatória quando existe projeto semelhante")
        return v

    @field_validator("dependencia_descricao")
    @classmethod
    def validar_dependencia(cls, v, info):
        if info.data.get("dependencia_critica") and not v:
            raise ValueError("Descrição obrigatória quando existe dependência crítica")
        return v

    @field_validator("info_nao_compartilhada_descricao")
    @classmethod
    def validar_info_nao_compartilhada(cls, v, info):
        if info.data.get("info_nao_compartilhada") and not v:
            raise ValueError("Descrição obrigatória quando há informação não compartilhada")
        return v
```

### 4.3 Checkpoint 2 — DESENVOLVIMENTO (`desenvolvimento_v1`)

```python
class CheckpointDesenvolvimentoRespostas(BaseModel):
    # Obrigatório: descrição ou anexos (validado no service)
    material_desenvolvido: str = Field(..., min_length=10, max_length=2000, 
        description="Descreva ou referencie anexos do material desenvolvido")
    
    # Obrigatório: múltipla escolha
    produtos_azul: list[ProdutoAzul] = Field(..., min_length=1)
    
    # Obrigatório: 1-5
    tom_escala: TomEscala = Field(...)
    
    # Obrigatório
    mudancas_desde_ideacao: str = Field(..., min_length=10, max_length=2000)
    
    # Obrigatório: enum
    feedback_ideacao_enderecado: SimNaoParcial = Field(...)
    
    # Condicional: se PARCIALMENTE ou NAO
    feedback_explicacao: str | None = Field(None, max_length=1000)
    
    # Obrigatório: enum
    limitacoes_internas: SimNaoParcial = Field(...)  # NAO / SIM
    
    # Condicional: se SIM
    limitacoes_explicacao: str | None = Field(None, max_length=1000)

    @field_validator("feedback_explicacao")
    @classmethod
    def validar_feedback(cls, v, info):
        val = info.data.get("feedback_ideacao_enderecado")
        if val in ("PARCIALMENTE", "NAO") and not v:
            raise ValueError("Explicação obrigatória quando feedback não foi totalmente endereçado")
        return v

    @field_validator("limitacoes_explicacao")
    @classmethod
    def validar_limitacoes(cls, v, info):
        if info.data.get("limitacoes_internas") == "SIM" and not v:
            raise ValueError("Explicação obrigatória quando existem limitações internas")
        return v
```

**Referência ao Checkpoint 1**: validar no Service que `checkpoint_ideacao.status == CONCLUIDO` antes de permitir `iniciar`/`enviar` do Desenvolvimento.

### 4.4 Checkpoint 3 — PRE_LANCAMENTO (`pre_lancamento_v1`)

```python
from datetime import date

class CheckpointPreLancamentoRespostas(BaseModel):
    # Obrigatório: anexo OBRIGATÓRIO (validado no service: deve ter ≥1 anexo)
    # Campo apenas descritivo; anexo real via endpoint /anexos
    versao_final_descricao: str = Field(..., min_length=10, max_length=1000)
    
    # Obrigatório
    areas_acordo: AreasAcordo = Field(...)
    
    # Condicional: se PARCIALMENTE ou NAO
    areas_lista: str | None = Field(None, max_length=1000, description="Lista de áreas não acordadas")
    
    # Obrigatório
    dados_clientes: bool = Field(...)
    dados_clientes_descricao: str | None = Field(None, max_length=1000)
    
    # Obrigatório
    revisao_juridica: RevisaoJuridica = Field(...)
    revisao_juridica_referencia: str | None = Field(None, max_length=500, description="Ref. aprovação ou anexo")
    
    # Obrigatório
    tarifas_confirmadas: bool = Field(...)
    
    # Obrigatório
    risco_interpretacao: bool = Field(...)
    risco_interpretacao_descricao: str | None = Field(None, max_length=500)
    
    # Obrigatório
    comparado_campanhas: ComparadoCampanhas = Field(...)
    
    # Obrigatório: date
    data_prevista_lancamento: date = Field(...)
    
    # Obrigatório (curto)
    riscos_incertos: str = Field(..., min_length=1, max_length=500)

    @field_validator("areas_lista")
    @classmethod
    def validar_areas(cls, v, info):
        if info.data.get("areas_acordo") in ("PARCIALMENTE", "NAO") and not v:
            raise ValueError("Lista de áreas obrigatória quando não há acordo total")
        return v

    @field_validator("dados_clientes_descricao")
    @classmethod
    def validar_dados_clientes(cls, v, info):
        if info.data.get("dados_clientes") and not v:
            raise ValueError("Descrição obrigatória quando envolve dados de clientes")
        return v

    @field_validator("risco_interpretacao_descricao")
    @classmethod
    def validar_risco(cls, v, info):
        if info.data.get("risco_interpretacao") and not v:
            raise ValueError("Descrição obrigatória quando há risco de má interpretação")
        return v
```

### 4.3 Schemas de request/response unificados

```python
# backend/app/schemas/checkpoint.py

class CheckpointIniciarRequest(BaseModel):
    """Inicia preenchimento: PENDENTE/SUGERIDO → EM_PREENCHIMENTO, seta iniciado_em"""
    pass  # body vazio

class CheckpointSalvarRespostasRequest(BaseModel):
    """Salva rascunho (parcial ou completo); não valida obrigatórios"""
    respostas: dict  # validação solta; estrutura por tipo no service
    versao_formulario: str  # ex: "ideacao_v1"

class CheckpointEnviarRequest(BaseModel):
    """Envia para avaliação: valida TODOS obrigatórios + condicionais; status → CONCLUIDO (6A) / AGUARDANDO_AVALIACAO (6B)"""
    respostas: dict
    versao_formulario: str

class CheckpointResponse(BaseModel):
    id: UUID
    projeto_id: UUID
    tipo: TipoCheckpoint
    status: StatusCheckpoint
    sugerido_em: datetime | None
    iniciado_em: datetime | None
    concluido_em: datetime | None
    respostas_formulario: dict | None
    resumo_para_marketing: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CheckpointListResponse(BaseModel):
    items: list[CheckpointResponse]
    total: int
```

---

## 5. Enums necessários (novos)

| Enum | Valores | Onde |
|------|---------|------|
| `FocoAzul` | RECONQUISTA_CLIENTE, FORTALECIMENTO_MALHA_REGIONAL, DIVERSIFICACAO_RECEITA, DISCIPLINA_FINANCEIRA, NENHUM | `checkpoint_enums.py` |
| `ImpactoRotas` | ROTAS_REGIONAIS, ROTAS_PRINCIPAIS_COMPETITIVAS, AMBAS, NAO_E_SOBRE_ROTAS | `checkpoint_enums.py` |
| `PrazoMercado` | ATE_1_MES, 1_3_MESES, 3_6_MESES, MAIS_6_MESES | `checkpoint_enums.py` |
| `ProdutoAzul` | AZUL_FIDELIDADE, AZUL_VIAGENS, AZUL_CARGO, AZUL_EMPRESAS, NENHUM | `checkpoint_enums.py` |
| `TomEscala` | 1, 2, 3, 4, 5 | `checkpoint_enums.py` (int Enum) |
| `AreasAcordo` | SIM, PARCIALMENTE, NAO | `checkpoint_enums.py` |
| `RevisaoJuridica` | SIM, NAO | `checkpoint_enums.py` |
| `ComparadoCampanhas` | SIM, NAO | `checkpoint_enums.py` |
| `SimNaoParcial` | SIM, PARCIALMENTE, NAO | `checkpoint_enums.py` |

**StatusCheckpoint** — **NÃO ALTERAR AGORA**. Manter `PENDENTE, SUGERIDO, EM_PREENCHIMENTO, CONCLUIDO`.  
Na Sprint 6B, migration para adicionar `AGUARDANDO_AVALIACAO` entre `EM_PREENCHIMENTO` e `CONCLUIDO`.

---

## 6. Schemas necessários (novos arquivos)

| Arquivo | Conteúdo |
|---------|----------|
| `backend/app/schemas/checkpoint_enums.py` | Enums compartilhados (FocoAzul, ImpactoRotas, etc.) |
| `backend/app/schemas/checkpoint_forms.py` | `CheckpointIdeacaoRespostas`, `CheckpointDesenvolvimentoRespostas`, `CheckpointPreLancamentoRespostas` + validadores |
| `backend/app/schemas/checkpoint.py` | Request/Response: `CheckpointIniciarRequest`, `CheckpointSalvarRespostasRequest`, `CheckpointEnviarRequest`, `CheckpointResponse`, `CheckpointListResponse` |
| `backend/app/schemas/anexo.py` | `AnexoUploadResponse`, `AnexoResponse`, `AnexoListResponse` |

---

## 7. Estratégia de Anexos

### 7.1 Nova tabela: `anexos_checkpoint`

```sql
-- Migration a ser criada (descrito aqui; NÃO executar agora)
CREATE TABLE anexos_checkpoint (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    checkpoint_id UUID NOT NULL REFERENCES checkpoints(id) ON DELETE CASCADE,
    nome_original VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    tamanho_bytes BIGINT NOT NULL,
    storage_key VARCHAR(500) NOT NULL,  -- path local ou S3 key
    enviado_por_id UUID NOT NULL REFERENCES usuarios(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_anexos_checkpoint_checkpoint_id ON anexos_checkpoint(checkpoint_id);
```

### 7.2 Modelo SQLAlchemy

```python
# backend/app/models/anexo.py
class AnexoCheckpoint(UUIDIdMixin, TimestampMixin, Base):
    __tablename__ = "anexos_checkpoint"

    checkpoint_id: Mapped[UUID] = mapped_column(
        ForeignKey("checkpoints.id", name="fk_anexo_checkpoint"), nullable=False
    )
    nome_original: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    tamanho_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    enviado_por_id: Mapped[UUID] = mapped_column(
        ForeignKey("usuarios.id", name="fk_anexo_enviado_por"), nullable=False
    )

    checkpoint: Mapped[Checkpoint] = relationship()
    enviado_por: Mapped[Usuario] = relationship()
```

### 7.3 Regras por checkpoint

| Checkpoint | Anexos permitidos? | Obrigatório? |
|------------|-------------------|--------------|
| IDEACAO | Sim (opcional) | Não |
| DESENVOLVIMENTO | Sim (opcional) | Não |
| PRE_LANCAMENTO | Sim | **SIM** (mínimo 1) |

### 7.4 Limites e validações

| Regra | Valor |
|-------|-------|
| Tamanho máx. por arquivo | 10 MB |
| Tipos MIME permitidos | `application/pdf`, `image/png`, `image/jpeg`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| Máx. arquivos por checkpoint | 10 |
| Storage v1 (Sprint 6A) | Local filesystem: `./storage/anexos/{checkpoint_id}/{uuid}_{nome}` |
| Storage v2 (futuro) | S3-compatível (MinIO/AWS S3) — interface `StorageService` abstrai |

### 7.5 Políticas

- **Exclusão**: Soft delete não necessário; `DELETE` remove registro + arquivo físico (service cuida).
- **Orfãos**: Job de limpeza periódica (futuro) para arquivos sem registro.
- **Referência no JSON**: `respostas_formulario.anexos = [{"anexo_id": "...", "nome_original": "...", "mime_type": "..."}]`

---

## 8. Status e Transições

### 8.1 Máquina de estados (Sprint 6A)

```
PENDENTE
    → (sugerido pelo sistema/agente) → SUGERIDO
    → (usuário clica "Iniciar") → EM_PREENCHIMENTO  (seta iniciado_em = now())
    
EM_PREENCHIMENTO
    → (salvar rascunho) → EM_PREENCHIMENTO  (atualiza respostas_formulario, atualizado_em)
    → (enviar formulário) → CONCLUIDO       (valida obrigatórios; seta concluido_em = now())
```

### 8.2 Ambiguidade do `CONCLUIDO` na 6A vs 6B

| Sprint | Significado de `CONCLUIDO` |
|--------|----------------------------|
| 6A | Formulário enviado + validado (sem IA) |
| 6B | Avaliação da IA salva (`AvaliacaoCheckpoint` criada) |

**Recomendação**: Manter `CONCLUIDO` na 6A como "enviado e validado".  
Na Sprint 6B, **adicionar `AGUARDANDO_AVALIACAO`** via migration de enum:

```sql
-- Migration 6B (futuro)
ALTER TYPE status_checkpoint ADD VALUE 'AGUARDANDO_AVALIACAO' AFTER 'EM_PREENCHIMENTO';
-- Atualizar checkpoints CONCLUIDO sem avaliação → AGUARDANDO_AVALIACAO
-- Novo fluxo: ENVIAR → AGUARDANDO_AVALIACAO → (IA avalia) → CONCLUIDO
```

**Não implementar agora**. Documentar no plano da 6B.

---

## 9. Regras de Ordem (Checkpoints Obrigatórios)

### 9.1 Regras de negócio

1. **Ordem fixa**: IDEACAO → DESENVOLVIMENTO → PRE_LANCAMENTO
2. **Desenvolvimento** só pode ser `iniciar`/`enviar` se **Ideação == CONCLUIDO**
3. **Pré-lançamento** só pode ser `iniciar`/`enviar` se **Desenvolvimento == CONCLUIDO**
4. Usuário pode continuar trabalhando no projeto (conversa, mensagens) independentemente do status dos checkpoints
5. Nenhum checkpoint pode ser pulado para aprovação final (regra futura: `APROVADO_PARA_LANCAMENTO` exige 3× `CONCLUIDO`)

### 9.2 Implementação (Service)

```python
# backend/app/services/checkpoint_service.py

def _validar_ordem_checkpoint(self, projeto_id: UUID, tipo: TipoCheckpoint) -> None:
    checkpoints = self.repo.list_by_projeto(projeto_id)
    cp_map = {cp.tipo: cp for cp in checkpoints}
    
    if tipo == TipoCheckpoint.DESENVOLVIMENTO:
        ideacao = cp_map.get(TipoCheckpoint.IDEACAO)
        if not ideacao or ideacao.status != StatusCheckpoint.CONCLUIDO:
            raise CheckpointOrdemError("Checkpoint de Ideação deve estar CONCLUIDO antes de iniciar Desenvolvimento")
    
    if tipo == TipoCheckpoint.PRE_LANCAMENTO:
        desenvolvimento = cp_map.get(TipoCheckpoint.DESENVOLVIMENTO)
        if not desenvolvimento or desenvolvimento.status != StatusCheckpoint.CONCLUIDO:
            raise CheckpointOrdemError("Checkpoint de Desenvolvimento deve estar CONCLUIDO antes de iniciar Pré-lançamento")
```

### 9.3 Criação sob demanda

- **Não** criar 3 checkpoints ao criar projeto (evita lixo `PENDENTE`).
- Endpoint `POST /projetos/{id}/checkpoints/{tipo}/iniciar`:
  - Busca ou cria checkpoint (`get_or_create` com `UniqueConstraint`)
  - Se `status == PENDENTE` ou `SUGERIDO` → seta `EM_PREENCHIMENTO`, `iniciado_em = now()`
  - Valida ordem (acima)
  - Retorna `CheckpointResponse`

---

## 10. Permissões (Matriz de Acesso)

| Ação | Portal Vertical (Criador) | Portal Vertical (Outros mesma vertical) | Portal Marketing | Admin | Liderança |
|------|---------------------------|------------------------------------------|------------------|-------|-----------|
| `iniciar` checkpoint | ✅ | ❌ | ❌ | ❌ | ❌ |
| `salvar respostas` (rascunho) | ✅ | ❌ | ❌ | ❌ | ❌ |
| `enviar` (validar + concluir) | ✅ | ❌ | ❌ | ❌ | ❌ |
| `ver respostas` (formal) | ✅ | ✅ * | ✅ * | ✅ * | ❌ |
| `ver resumo_para_marketing` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `upload anexo` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `listar anexos` | ✅ | ✅ * | ✅ * | ✅ * | ❌ |
| `deletar anexo próprio` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `acessar conversa bruta` | ✅ | ❌ | ❌ | ❌ | ❌ |

* **Decisão de negócio pendente**: "Outros usuários da mesma vertical podem visualizar respostas formais do checkpoint?"  
  **Recomendação**: **SIM** — alinhamento entre time da vertical. Marketing **SIM** na 6A (visualizar respostas formais, não editar). Admin **SIM** (auditoria).

### 10.1 Implementação no Service

```python
def _autorizar_acesso_checkpoint(self, checkpoint: Checkpoint, user: CurrentUser, acao: str) -> None:
    projeto = checkpoint.projeto
    
    if user.papel == PapelUsuario.VERTICAL:
        if acao in ("iniciar", "salvar", "enviar", "upload_anexo", "delete_anexo"):
            if projeto.criado_por_id != user.id:
                raise AuthorizationError("Apenas o criador do projeto pode preencheckpoints")
        # visualizar: qualquer um da mesma vertical
        if projeto.vertical_id != user.vertical_id:
            raise AuthorizationError("Acesso negado")
    
    elif user.papel == PapelUsuario.MARKETING:
        if acao in ("iniciar", "salvar", "enviar", "upload_anexo", "delete_anexo"):
            raise AuthorizationError("Marketing não pode preencher checkpoints")
        # visualizar: permitido
    
    elif user.papel == PapelUsuario.ADMIN:
        if acao in ("iniciar", "salvar", "enviar", "upload_anexo", "delete_anexo"):
            raise AuthorizationError("Admin não edita checkpoints")
        # visualizar: permitido
    
    elif user.papel == PapelUsuario.LIDERANCA:
        raise AuthorizationError("Liderança não tem acesso operacional nesta sprint")
    
    else:
        raise AuthorizationError("Papel inválido")
```

### 10.2 Conversa privada permanece inacessível

- Endpoint `/projetos/{id}/conversa` e `/projetos/{id}/mensagens` **inalterados** — só criador acessa.
- Checkpoints não expõem mensagens da conversa.

---

## 11. Endpoints Finais

| Método | Path | Descrição | Auth | Body |
|--------|------|-----------|------|------|
| `GET` | `/projetos/{projeto_id}/checkpoints` | Lista 3 checkpoints do projeto | VERTICAL (mesma vert), MARKETING, ADMIN | — |
| `GET` | `/projetos/{projeto_id}/checkpoints/{tipo}` | Detalha um checkpoint | VERTICAL (mesma vert), MARKETING, ADMIN | — |
| `POST` | `/projetos/{projeto_id}/checkpoints/{tipo}/iniciar` | Cria/busca checkpoint; PENDENTE/SUGERIDO → EM_PREENCHIMENTO | VERTICAL (criador) | `{}` |
| `PATCH` | `/projetos/{projeto_id}/checkpoints/{tipo}/respostas` | Salva rascunho (validação leve) | VERTICAL (criador) | `CheckpointSalvarRespostasRequest` |
| `POST` | `/projetos/{projeto_id}/checkpoints/{tipo}/enviar` | Valida obrigatórios + condicionais; EM_PREENCHIMENTO → CONCLUIDO | VERTICAL (criador) | `CheckpointEnviarRequest` |
| `POST` | `/projetos/{projeto_id}/checkpoints/{tipo}/anexos` | Upload anexo (multipart) | VERTICAL (criador) | `multipart/form-data` |
| `GET` | `/projetos/{projeto_id}/checkpoints/{tipo}/anexos` | Lista anexos do checkpoint | VERTICAL (mesma vert), MARKETING, ADMIN | — |
| `DELETE` | `/projetos/{projeto_id}/checkpoints/{tipo}/anexos/{anexo_id}` | Remove anexo (apenas dono) | VERTICAL (criador do anexo) | — |

**Observações:**
- `tipo` no path = `IDEACAO`, `DESENVOLVIMENTO`, `PRE_LANCAMENTO` (validador no path)
- Não há endpoint de "sugerir checkpoint" na 6A (futuro: agente IA)
- Não há endpoint de avaliação IA na 6A

---

## 12. Repositories (novos arquivos)

### 12.1 `backend/app/repositories/checkpoint_repository.py`

```python
class CheckpointRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_projeto_tipo(self, projeto_id: UUID, tipo: TipoCheckpoint) -> Checkpoint | None:
        return self.db.query(Checkpoint).filter(
            Checkpoint.projeto_id == projeto_id,
            Checkpoint.tipo == tipo
        ).first()

    def get_or_create(self, projeto_id: UUID, tipo: TipoCheckpoint) -> Checkpoint:
        cp = self.get_by_projeto_tipo(projeto_id, tipo)
        if cp:
            return cp
        cp = Checkpoint(projeto_id=projeto_id, tipo=tipo, status=StatusCheckpoint.PENDENTE)
        self.db.add(cp)
        self.db.flush()
        return cp

    def list_by_projeto(self, projeto_id: UUID) -> list[Checkpoint]:
        return self.db.query(Checkpoint).filter(Checkpoint.projeto_id == projeto_id).all()

    def update_status(self, checkpoint: Checkpoint, status: StatusCheckpoint, **timestamps) -> Checkpoint:
        checkpoint.status = status
        for k, v in timestamps.items():
            setattr(checkpoint, k, v)
        self.db.flush()
        return checkpoint

    def update_respostas(self, checkpoint: Checkpoint, respostas: dict, versao: str) -> Checkpoint:
        # Merge com estrutura versionada
        data = checkpoint.respostas_formulario or {}
        data.update({
            "versao_formulario": versao,
            "tipo_checkpoint": checkpoint.tipo.value,
            "respostas": respostas,
            "anexos": data.get("anexos", []),
            "atualizado_em": datetime.now(UTC).isoformat(),
        })
        if "enviado_em" not in data:
            data["enviado_em"] = datetime.now(UTC).isoformat()
        checkpoint.respostas_formulario = data
        self.db.flush()
        return checkpoint
```

### 12.2 `backend/app/repositories/anexo_repository.py`

```python
class AnexoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, anexo: AnexoCheckpoint) -> AnexoCheckpoint:
        self.db.add(anexo)
        self.db.flush()
        return anexo

    def get_by_id(self, anexo_id: UUID) -> AnexoCheckpoint | None:
        return self.db.query(AnexoCheckpoint).filter(AnexoCheckpoint.id == anexo_id).first()

    def list_by_checkpoint(self, checkpoint_id: UUID) -> list[AnexoCheckpoint]:
        return self.db.query(AnexoCheckpoint).filter(
            AnexoCheckpoint.checkpoint_id == checkpoint_id
        ).order_by(AnexoCheckpoint.created_at.desc()).all()

    def delete(self, anexo: AnexoCheckpoint) -> None:
        self.db.delete(anexo)
        self.db.flush()
```

---

## 13. Services (novos arquivos)

### 13.1 `backend/app/services/checkpoint_service.py`

**Responsabilidades:**
- Orquestrar repository + storage + validações
- Transações (usar `get_db` que já controla commit/rollback)
- Regras de ordem, permissões, validação de formulários
- Montar JSON versionado para `respostas_formulario`

```python
class CheckpointService:
    def __init__(self, repo: CheckpointRepository, anexo_repo: AnexoRepository, storage: StorageService):
        self.repo = repo
        self.anexo_repo = anexo_repo
        self.storage = storage

    def listar_checkpoints(self, projeto_id: UUID, user: CurrentUser) -> list[CheckpointResponse]:
        # autorização de visualização
        ...

    def iniciar_checkpoint(self, projeto_id: UUID, tipo: TipoCheckpoint, user: CurrentUser) -> CheckpointResponse:
        # 1. Autorizar (criador)
        # 2. Validar ordem (Service)
        # 3. Get or create checkpoint
        # 4. Se PENDENTE/SUGERIDO → EM_PREENCHIMENTO + iniciado_em
        # 5. Return

    def salvar_respostas(self, projeto_id: UUID, tipo: TipoCheckpoint, data: CheckpointSalvarRespostasRequest, user: CurrentUser) -> CheckpointResponse:
        # 1. Autorizar (criador)
        # 2. Validar versão do formulário
        # 3. Validar estrutura leve (pydantic model do tipo)
        # 4. Update respostas_formulario (merge)
        # 5. Return

    def enviar_checkpoint(self, projeto_id: UUID, tipo: TipoCheckpoint, data: CheckpointEnviarRequest, user: CurrentUser) -> CheckpointResponse:
        # 1. Autorizar (criador)
        # 2. Validar ordem (checkpoint anterior CONCLUIDO)
        # 3. Validar TODOS campos obrigatórios + condicionais (pydantic model do tipo)
        # 4. Se PRE_LANCAMENTO: validar ≥1 anexo
        # 5. Update respostas_formulario + status=CONCLUIDO + concluido_em
        # 6. Return

    # Anexos
    def upload_anexo(self, projeto_id: UUID, tipo: TipoCheckpoint, file: UploadFile, user: CurrentUser) -> AnexoUploadResponse:
        # 1. Autorizar (criador)
        # 2. Validar checkpoint existe e status EM_PREENCHIMENTO ou CONCLUIDO
        # 3. Validar MIME, tamanho, limite 10 arquivos
        # 4. Salvar arquivo no storage (local v1)
        # 5. Criar registro AnexoCheckpoint
        # 6. Atualizar respostas_formulario.anexos (append)
        # 7. Return

    def listar_anexos(self, projeto_id: UUID, tipo: TipoCheckpoint, user: CurrentUser) -> list[AnexoResponse]:
        # Autorizar visualização
        ...

    def deletar_anexo(self, projeto_id: UUID, tipo: TipoCheckpoint, anexo_id: UUID, user: CurrentUser) -> None:
        # 1. Autorizar (criador do anexo)
        # 2. Deletar arquivo físico
        # 3. Deletar registro
        # 4. Atualizar respostas_formulario.anexos (remove)
```

### 13.2 `backend/app/services/storage_service.py`

```python
class StorageService:
    """Abstração para storage local (v1) / S3 (v2)"""
    
    def __init__(self, base_path: str = "./storage/anexos"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, checkpoint_id: UUID, filename: str, content: bytes) -> str:
        """Retorna storage_key (path relativo)"""
        safe_name = f"{uuid4()}_{filename}"
        dest = self.base_path / str(checkpoint_id) / safe_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        return str(dest.relative_to(self.base_path))

    def delete(self, storage_key: str) -> None:
        path = self.base_path / storage_key
        if path.exists():
            path.unlink()
            # Remover diretórios vazios (opcional)

    def get_path(self, storage_key: str) -> Path:
        return self.base_path / storage_key
```

**Configuração**: `settings.STORAGE_PATH` (default `./storage/anexos`)

---

## 14. Routes (novo arquivo)

### 14.1 `backend/app/routes/checkpoints.py`

```python
router = APIRouter(prefix="/projetos/{projeto_id}/checkpoints", tags=["Checkpoints"])

# Dependency injection
def get_checkpoint_service(db: Session = Depends(get_db)) -> CheckpointService:
    return CheckpointService(
        CheckpointRepository(db),
        AnexoRepository(db),
        StorageService()
    )

@router.get("", response_model=CheckpointListResponse)
def listar_checkpoints(
    projeto_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: CheckpointService = Depends(get_checkpoint_service),
):
    return service.listar_checkpoints(projeto_id, current_user)

@router.get("/{tipo}", response_model=CheckpointResponse)
def obter_checkpoint(
    projeto_id: UUID,
    tipo: TipoCheckpoint,
    current_user: CurrentUser = Depends(get_current_user),
    service: CheckpointService = Depends(get_checkpoint_service),
):
    return service.obter_checkpoint(projeto_id, tipo, current_user)

@router.post("/{tipo}/iniciar", response_model=CheckpointResponse, status_code=201)
def iniciar_checkpoint(
    projeto_id: UUID,
    tipo: TipoCheckpoint,
    current_user: CurrentUser = Depends(get_current_user),
    service: CheckpointService = Depends(get_checkpoint_service),
):
    return service.iniciar_checkpoint(projeto_id, tipo, current_user)

@router.patch("/{tipo}/respostas", response_model=CheckpointResponse)
def salvar_respostas(
    projeto_id: UUID,
    tipo: TipoCheckpoint,
    data: CheckpointSalvarRespostasRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CheckpointService = Depends(get_checkpoint_service),
):
    return service.salvar_respostas(projeto_id, tipo, data, current_user)

@router.post("/{tipo}/enviar", response_model=CheckpointResponse)
def enviar_checkpoint(
    projeto_id: UUID,
    tipo: TipoCheckpoint,
    data: CheckpointEnviarRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CheckpointService = Depends(get_checkpoint_service),
):
    return service.enviar_checkpoint(projeto_id, tipo, data, current_user)

# Anexos
@router.post("/{tipo}/anexos", response_model=AnexoUploadResponse, status_code=201)
async def upload_anexo(
    projeto_id: UUID,
    tipo: TipoCheckpoint,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    service: CheckpointService = Depends(get_checkpoint_service),
):
    return await service.upload_anexo(projeto_id, tipo, file, current_user)

@router.get("/{tipo}/anexos", response_model=AnexoListResponse)
def listar_anexos(
    projeto_id: UUID,
    tipo: TipoCheckpoint,
    current_user: CurrentUser = Depends(get_current_user),
    service: CheckpointService = Depends(get_checkpoint_service),
):
    return service.listar_anexos(projeto_id, tipo, current_user)

@router.delete("/{tipo}/anexos/{anexo_id}", status_code=204)
def deletar_anexo(
    projeto_id: UUID,
    tipo: TipoCheckpoint,
    anexo_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: CheckpointService = Depends(get_checkpoint_service),
):
    service.deletar_anexo(projeto_id, tipo, anexo_id, current_user)
```

### 14.2 Registro no `main.py`

```python
from app.routes import checkpoints
app.include_router(checkpoints.router)
```

---

## 15. Migrações necessárias

| Migration | Descrição | Quando |
|-----------|-----------|--------|
| `0003_create_anexos_checkpoint.py` | Cria tabela `anexos_checkpoint` + índices + FKs | **Sprint 6A** (antes de implementar anexos) |
| `0004_add_aguardando_avaliacao_status.py` | Adiciona `AGUARDANDO_AVALIACAO` ao enum `status_checkpoint` | **Sprint 6B** (NÃO AGORA) |

### 15.1 Conteúdo da Migration 0003 (descritivo)

```python
"""create anexos_checkpoint table

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-15
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"

def upgrade():
    op.create_table(
        "anexos_checkpoint",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("checkpoint_id", sa.Uuid(), nullable=False),
        sa.Column("nome_original", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("tamanho_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("enviado_por_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_anexos_checkpoint"),
        sa.ForeignKeyConstraint(["checkpoint_id"], ["checkpoints.id"], name="fk_anexos_checkpoint_checkpoint_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["enviado_por_id"], ["usuarios.id"], name="fk_anexos_checkpoint_enviado_por_id"),
    )
    op.create_index("ix_anexos_checkpoint_checkpoint_id", "anexos_checkpoint", ["checkpoint_id"])

def downgrade():
    op.drop_index("ix_anexos_checkpoint_checkpoint_id", table_name="anexos_checkpoint")
    op.drop_table("anexos_checkpoint")
```

---

## 16. Estratégia de Testes

### 16.1 Arquivos de teste novos

| Arquivo | Foco |
|---------|------|
| `backend/tests/test_checkpoints.py` | Endpoints + regras de negócio + permissões |
| `backend/tests/test_checkpoint_forms.py` | Validação Pydantic de cada formulário (unitário) |
| `backend/tests/test_checkpoint_attachments.py` | Upload, listagem, deleção, validações de MIME/tamanho |

### 16.2 Cenários a cobrir

| Categoria | Cenários |
|-----------|----------|
| **Permissões** | Apenas criador inicia/salva/envia; outros da mesma vertical só leem; Marketing lê mas não edita; Admin lê mas não edita; Liderança 403; conversa privada inacessível |
| **Ordem** | Desenvolvimento bloqueado sem Ideação CONCLUIDO; Pré-lançamento bloqueado sem Desenvolvimento CONCLUIDO; Projeto pode continuar (conversa) sem checkpoints |
| **Duplicidade** | `iniciar` duas vezes mesmo tipo → retorna mesmo checkpoint (UniqueConstraint) |
| **Rascunho** | `salvar_respostas` aceita parcial; não valida obrigatórios; não muda status |
| **Envio** | `enviar` valida TODOS obrigatórios + condicionais; falha → 422; sucesso → CONCLUIDO + concluido_em |
| **Checkpoint 3** | Upload obrigatório (≥1 anexo); sem anexo → 422 |
| **Anexos** | MIME inválido → 415; >10MB → 413; >10 arquivos → 400; deletar só dono |
| **Regressão** | Endpoints `/projetos`, `/projetos/{id}/conversa`, `/projetos/{id}/mensagens` continuam funcionando |

### 16.3 Fixtures sugeridas

```python
# conftest.py additions
@pytest.fixture
def checkpoint_ideacao_respostas_valida():
    return {
        "descricao_projeto": "Projeto para melhorar experiência do cliente...",
        "proposta_solucao": "App mobile com notificações...",
        "focos_azul": ["RECONQUISTA_CLIENTE", "FORTALECIMENTO_MALHA_REGIONAL"],
        "impacto_rotas": "ROTAS_REGIONAIS",
        "existe_semelhante": False,
        "semelhante_descricao": None,
        "prazo_mercado": "1_3_MESES",
        "dependencia_critica": False,
        "dependencia_descricao": None,
        "diferencial": "Integração nativa com programa de fidelidade...",
        "info_nao_compartilhada": False,
        "info_nao_compartilhada_descricao": None,
    }
```

---

## 17. Riscos Técnicos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| JSON `respostas_formulario` crescer além do esperado | Baixa | Médio | Monitorar tamanho; migração para JSONB + colunas extraídas se necessário |
| Validação condicional complexa no Pydantic v2 | Média | Médio | Testes unitários exaustivos em `test_checkpoint_forms.py`; usar `model_validator(mode='after')` para cross-field |
| Storage local em container não persistir | Alta (dev) | Alto | Documentar volume Docker; CI usa tmpfs; produção usa S3 |
| Enum `StatusCheckpoint` migration na 6B quebrar dados | Baixa | Alto | Testar migration 6B em staging; backup antes |
| Permissão "outros da vertical veem respostas" mudar | Média | Baixo | Configurar via feature flag ou policy class injetável |
| Race condition `iniciar` checkpoint duplicado | Baixa | Médio | `UniqueConstraint` no banco + `get_or_create` com `flush` |

---

## 18. Critérios de Aceite da Sprint 6A

| ID | Critério | Como validar |
|----|----------|--------------|
| **CA-01** | `GET /projetos/{id}/checkpoints` retorna 3 checkpoints com status `PENDENTE` | Teste integração + manual |
| **CA-02** | Criador pode `POST /iniciar` → status `EM_PREENCHIMENTO`, `iniciado_em` preenchido | Teste + Swagger |
| **CA-03** | Criador pode `PATCH /respostas` com payload parcial → salva, status mantido | Teste unitário + integração |
| **CA-04** | `POST /enviar` valida todos obrigatórios + condicionais de cada checkpoint | Testes `test_checkpoint_forms.py` + integração |
| **CA-05** | Envio bem-sucedido → status `CONCLUIDO`, `concluido_em` preenchido, JSON versionado | Teste integração |
| **CA-06** | Desenvolvimento bloqueado se Ideação != CONCLUIDO | Teste integração (403/400) |
| **CA-07** | Pré-lançamento bloqueado se Desenvolvimento != CONCLUIDO | Teste integração |
| **CA-08** | Upload anexo: MIME/tamanho/quantidade validados; arquivo salvo em storage local | Teste `test_checkpoint_attachments.py` |
| **CA-09** | Pré-lançamento exige ≥1 anexo no `enviar` | Teste integração |
| **CA-10** | Apenas criador edita; mesma vertical lê; Marketing lê; Admin lê; Liderança 403 | Testes permissão |
| **CA-11** | Conversa privada (`/conversa`, `/mensagens`) inalterada e restrita ao criador | Regressão `test_conversa.py` |
| **CA-12** | Migração `0003` roda limpo (up/down) | `alembic upgrade head` + `downgrade -1` |
| **CA-13** | Cobertura de testes ≥ 85% nos novos módulos | `pytest --cov=app/services/checkpoint_service --cov=app/repositories/checkpoint_repository` |

---

## 19. Dúvidas que exigem decisão humana

| # | Dúvida | Opções | Recomendação |
|---|--------|--------|--------------|
| **D1** | Outros usuários da **mesma vertical** podem ver **respostas formais** do checkpoint? | A) Sim (recomendado) B) Não (só criador) | **A** — alinhamento do time |
| **D2** | **Marketing** pode ver respostas formais na Sprint 6A? | A) Sim (read-only) B) Não (só na 6B com resumo) | **A** — antecipa valor |
| **D3** | `StatusCheckpoint.CONCLUIDO` na 6A significa "enviado" ou "avaliado"? | A) Enviado+validado (6A) B) Reservar para 6B | **A** — pragmático; 6B adiciona `AGUARDANDO_AVALIACAO` |
| **D4** | Criar 3 checkpoints `PENDENTE` ao criar projeto OU criar sob demanda no `iniciar`? | A) Sob demanda (recomendado) B) Auto-criar | **A** — evita lixo; `UniqueConstraint` garante idempotência |
| **D5** | Limite de 10 anexos por checkpoint é suficiente? | A) Sim B) Aumentar para 20 | **A** — ajustável via config depois |
| **D6** | Storage local path `./storage/anexos` é aceitável para dev/staging? | A) Sim B) Usar `/tmp` | **A** — volume Docker mapeado |
| **D7** | Validar `data_prevista_lancamento` (Checkpoint 3) como `date` ou `datetime`? | A) `date` (apenas data) B) `datetime` | **A** — data de lançamento não precisa de hora |
| **D8** | **Versionamento dos formulários**: como evoluir perguntas/validações sem quebrar projetos antigos? | Ver seção 21 | **Estratégia: JSON versionado com `versao_formulario` + `versao_business`** (seção 21) |
| **D9** | **Versionamento da avaliação IA**: como auditar modelo/prompt/critérios em cada avaliação futura? | Ver seção 22 | **Estratégia: campos em `AvaliacaoCheckpoint` para `modelo`, `prompt_version`, `criteria_version`, `evaluated_at`** (seção 22) |

---

## 21. D8 — Estratégia de Versionamento dos Formulários

### 21.1 Estrutura do JSON armazenado

```json
{
  "versao_formulario": "ideacao_v1",
  "versao_business": "2026-07",
  "tipo_checkpoint": "IDEACAO",
  "respostas": { ... },
  "anexos": [...],
  "enviado_em": "2026-07-15T10:30:00Z",
  "atualizado_em": "2026-07-15T10:30:00Z"
}
```

### 21.2 Vantagens

| Vantagem | Descrição |
|----------|-----------|
| **Compatibilidade total** | Registros antigos (`ideacao_v1`) permanecem intactos; novo código lê `versao_formulario` e aplica adapter |
| **Sem migration de dados** | Nova versão = novo schema Pydantic (`CheckpointIdeacaoRespostasV2`); JSON antigo não é tocado |
| **Rastreabilidade de negócio** | `versao_business` (ex.: `2026-07`) vincula formulário às regras de negócio vigentes na época |
| **Auditoria** | Histórico completo: qual versão o usuário preencheu, quando, sob quais regras |
| **Migração preguiçosa (lazy)** | Ao ler checkpoint antigo, service detecta versão e converte para estrutura atual se necessário |

### 21.3 Possíveis problemas e mitigações

| Problema | Mitigação |
|----------|-----------|
| **Código de leitura fica complexo** | Isolar em `FormVersionAdapter` com método `normalize_to_latest(data: dict) -> dict` |
| **Validação de versões antigas** | Não revalidar dados antigos com regras novas; apenas normalizar campos obrigatórios que faltam |
| **Relatórios/BI quebram** | Views SQL ou materialized views que normalizam `respostas_formulario` para colunas planas |
| **Anexos referenciados** | `anexos` array guarda apenas metadados; storage key imutável |

### 21.4 Impacto em migrations

- **Zero migrations** para evoluir formulários
- Apenas novo arquivo de schema: `schemas/checkpoint_forms_v2.py`
- `CheckpointService` importa versão baseada em `versao_formulario` do registro

### 21.5 Leitura de dados antigos

```python
# backend/app/services/form_adapter.py
class FormVersionAdapter:
    VERSIONS = {
        "ideacao_v1": CheckpointIdeacaoRespostasV1,
        "ideacao_v2": CheckpointIdeacaoRespostasV2,
        # ...
    }
    
    @classmethod
    def normalize(cls, data: dict) -> dict:
        version = data.get("versao_formulario", "ideacao_v1")
        model_class = cls.VERSIONS.get(version)
        if not model_class:
            # fallback: assume v1
            model_class = cls.VERSIONS["ideacao_v1"]
        # Validar e normalizar para estrutura mais recente
        validated = model_class(**data.get("respostas", {}))
        return validated.model_dump()
```

### 21.6 Futuras versões (ex.: `ideacao_v2`)

1. Criar `CheckpointIdeacaoRespostasV2` em `schemas/checkpoint_forms_v2.py`
2. Registrar no `FormVersionAdapter.VERSIONS`
3. Endpoint `/enviar` salva com `"versao_formulario": "ideacao_v2"`
4. Registros `v1` continuam funcionando — adapter normaliza na leitura

---

## 22. D9 — Estratégia de Versionamento da Avaliação IA (Sprint 6B+)

### 22.1 Onde armazenar (entidade `AvaliacaoCheckpoint`)

Adicionar à tabela `avaliacoes_checkpoint` (futura migration 6B):

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `modelo` | VARCHAR(100) | Ex.: `gpt-5.5`, `claude-4-opus` |
| `prompt_version` | VARCHAR(50) | Ex.: `checkpoint1_v3` |
| `criteria_version` | VARCHAR(50) | Ex.: `business_rules_2026_07` |
| `evaluated_at` | TIMESTAMPTZ | Momento da avaliação |
| `prompt_hash` | VARCHAR(64) | SHA-256 do prompt completo (auditoria imutável) |
| `criteria_hash` | VARCHAR(64) | SHA-256 dos critérios (auditoria imutável) |

### 22.2 Por que em `AvaliacaoCheckpoint` e não no `Checkpoint`?

| Razão | Explicação |
|-------|------------|
| **Separação de responsabilidades** | Checkpoint = respostas do usuário; Avaliação = output da IA |
| **Uma avaliação por checkpoint** | `AvaliacaoCheckpoint.checkpoint_id` é UNIQUE — 1:1 natural |
| **Reavaliação = nova linha** | Se rodar IA novamente, cria nova `AvaliacaoCheckpoint` (ou versiona com `versao_avaliacao`) |
| **Histórico imutável** | Cada avaliação guarda *exatamente* o que foi usado (modelo, prompt, critérios) |

### 22.3 Permitir reavaliação sem perder histórico

```json
// Exemplo: primeira avaliação
{
  "modelo": "gpt-4o",
  "prompt_version": "checkpoint1_v2",
  "criteria_version": "business_rules_2026_06",
  "evaluated_at": "2026-07-10T14:00:00Z",
  "score_alinhamento": 72,
  "score_potencial": 65,
  "classificacao_farol": "VALE_INVESTIR_TEMPO"
}

// Reavaliação posterior (nova linha na tabela)
{
  "modelo": "gpt-5.5",
  "prompt_version": "checkpoint1_v3",
  "criteria_version": "business_rules_2026_07",
  "evaluated_at": "2026-08-15T09:30:00Z",
  "score_alinhamento": 78,
  "score_potencial": 71,
  "classificacao_farol": "PRIORIDADE_MAXIMA"
}
```

### 22.4 Estratégia de migration (Sprint 6B)

```sql
-- 0005_add_ia_versioning_to_avaliacao.sql
ALTER TABLE avaliacoes_checkpoint
  ADD COLUMN modelo VARCHAR(100),
  ADD COLUMN prompt_version VARCHAR(50),
  ADD COLUMN criteria_version VARCHAR(50),
  ADD COLUMN evaluated_at TIMESTAMPTZ,
  ADD COLUMN prompt_hash VARCHAR(64),
  ADD COLUMN criteria_hash VARCHAR(64);

-- Índice para auditoria
CREATE INDEX ix_avaliacao_modelo_version ON avaliacoes_checkpoint(modelo, prompt_version);
```

### 22.5 Compatibilidade futura

- **Sprint 6A**: não adicionar campos (tabela `avaliacoes_checkpoint` já existe, vazia)
- **Sprint 6B**: migration 0005 adiciona campos; service popula obrigatoriamente
- **Sprint 7+**: se mudar estrutura de avaliação, criar `avaliacoes_checkpoint_v2` ou adicionar `versao_avaliacao` JSON

---

## 23. D10 — Reavaliação de Checkpoints (Auditoria Imutável)

### 23.1 Requisito Fundamental

Uma avaliação **NUNCA** deve ser sobrescrita (UPDATE). Sempre que um checkpoint for reavaliado, cria-se uma **nova linha** em `avaliacoes_checkpoint`.

```
Checkpoint (1)
    ↓
Avaliação #1 — modelo=GPT-5.5, prompt_version=checkpoint1_v1, criteria_version=business_rules_2026_07
    ↓
Avaliação #2 — modelo=GPT-6,   prompt_version=checkpoint1_v2, criteria_version=business_rules_2027_01
    ↓
Avaliação #3 — modelo=GPT-6.5, prompt_version=checkpoint1_v4, criteria_version=business_rules_2027_05
```

Todas permanecem armazenadas — histórico imutável.

### 23.2 Como determinar a avaliação vigente: Opção A vs Opção B

| Critério | Opção A: Maior `evaluated_at` (Recomendada) | Opção B: Campo `is_current` BOOLEAN |
|----------|---------------------------------------------|-------------------------------------|
| **Implementação** | `ORDER BY evaluated_at DESC LIMIT 1` | `WHERE is_current = true` (unique partial index) |
| **Integridade** | Natural — timestamp não mente | Requer transação para flip (desmarcar antiga, marcar nova) |
| **Race condition** | Impossível — append-only | Possível se duas avaliações simultâneas |
| **Auditoria** | Completa — ordem temporal inequívoca | Requer confiar no flag; pode haver inconsistência |
| **Query performance** | Index em `(checkpoint_id, evaluated_at DESC)` — rápido | Index parcial `WHERE is_current` — rápido |
| **Reprocessamento** | Trivial — nova linha com `evaluated_at = now()` | Precisa atualizar flags antigas |
| **Compliance** | Ideal — rastreabilidade temporal nativa | Requer controle extra de flags |

**Recomendação: Opção A** — append-only, zero race conditions, auditoria nativa, alinhado com "nunca UPDATE".

### 23.3 Modelo futuro (Sprint 6B migration 0005)

```python
# backend/app/models/checkpoint.py (futuro)
class AvaliacaoCheckpoint(UUIDIdMixin, TimestampMixin, Base):
    __tablename__ = "avaliacoes_checkpoint"
    
    checkpoint_id: Mapped[UUID] = mapped_column(
        ForeignKey("checkpoints.id", name="fk_avaliacao_checkpoint"),
        nullable=False,
    )
    # ... campos existentes ...
    
    # NOVOS (D9 + D10)
    modelo: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    criteria_version: Mapped[str] = mapped_column(String(50), nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    criteria_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    
    # Constraint para query eficiente da vigente
    __table_args__ = (
        Index("ix_avaliacao_checkpoint_evaluated_desc", "checkpoint_id", "evaluated_at.desc()"),
        # Opção B (não recomendada): 
        # Index("ix_avaliacao_current", "checkpoint_id", unique=True, postgresql_where=text("is_current")),
    )
```

### 23.4 Consultas planejadas

| Consulta | SQL/ORM |
|----------|---------|
| **Todas as avaliações** | `SELECT * FROM avaliacoes_checkpoint WHERE checkpoint_id = ? ORDER BY evaluated_at DESC` |
| **Avaliação vigente** | `SELECT * FROM avaliacoes_checkpoint WHERE checkpoint_id = ? ORDER BY evaluated_at DESC LIMIT 1` |
| **Comparar duas versões** | App lê duas linhas e faz diff nos scores/critérios |
| **Por modelo/prompt** | `WHERE modelo = ? AND prompt_version = ?` |
| **Auditoria completa** | `SELECT * FROM avaliacoes_checkpoint ORDER BY evaluated_at` |

### 23.5 Impacto nos requisitos

| Requisito | Como é atendido |
|-----------|-----------------|
| **Auditoria completa** | Cada avaliação é linha imutável com modelo/prompt/critérios/hash/timestamp |
| **Comparação entre versões** | App busca N linhas do mesmo `checkpoint_id` e compara campos |
| **Reprocessamento antigos** | Job cria nova `AvaliacaoCheckpoint` com modelo novo; original intacta |
| **Evolução sem perda** | Append-only garante que nada é apagado ou sobrescrito |
| **Rastreabilidade compliance** | `prompt_hash` + `criteria_hash` provam exatamente o que foi executado |

### 23.6 Service pattern (Sprint 6B)

```python
# backend/app/services/avaliacao_service.py (futuro)
class AvaliacaoService:
    def criar_avaliacao(self, checkpoint_id: UUID, resultado: AvaliacaoResultado) -> AvaliacaoCheckpoint:
        # SEMPRE INSERT — nunca UPDATE
        avaliacao = AvaliacaoCheckpoint(
            checkpoint_id=checkpoint_id,
            modelo=resultado.modelo,
            prompt_version=resultado.prompt_version,
            criteria_version=resultado.criteria_version,
            evaluated_at=datetime.now(UTC),
            prompt_hash=sha256(resultado.prompt_completo),
            criteria_hash=sha256(resultado.criterios_json),
            score_alinhamento=resultado.score_alinhamento,
            score_potencial=resultado.score_potencial,
            classificacao_farol=resultado.classificacao,
            criterios_alinhamento=resultado.criterios_alinhamento,
            criterios_potencial=resultado.criterios_potencial,
            explicacoes=resultado.explicacoes,
        )
        self.repo.create(avaliacao)
        return avaliacao
    
    def obter_vigente(self, checkpoint_id: UUID) -> AvaliacaoCheckpoint | None:
        return self.repo.get_latest_by_checkpoint(checkpoint_id)
    
    def listar_historico(self, checkpoint_id: UUID) -> list[AvaliacaoCheckpoint]:
        return self.repo.list_by_checkpoint_ordered(checkpoint_id)
```

---

## 20. Próximos Passos (após aprovação)

1. **Aprovar este plano** (responder "aprovado" ou com ajustes)
2. Criar migration `0003_create_anexos_checkpoint.py`
3. Implementar enums em `schemas/checkpoint_enums.py`
4. Implementar forms em `schemas/checkpoint_forms.py`
5. Implementar schemas request/response em `schemas/checkpoint.py`, `schemas/anexo.py`
6. Implementar `AnexoCheckpoint` model + registro em `models/__init__.py`
7. Implementar repositories: `checkpoint_repository.py`, `anexo_repository.py`
8. Implementar `StorageService` + config
9. Implementar `CheckpointService` com todas as regras
10. Implementar `routes/checkpoints.py` + registrar no `main.py`
11. Escrever testes: `test_checkpoints.py`, `test_checkpoint_forms.py`, `test_checkpoint_attachments.py`
12. Rodar `pytest`, `ruff`, `mypy` (se configurado)
13. Atualizar `docs/database-model.md` e `docs/business-rules.md` se necessário

---

**Fim do Plano Técnico — Sprint 6A**  
*Aguardando aprovação para iniciar implementação.*