# Farol

Plataforma web moderna construída com Python FastAPI no backend e React com TypeScript no frontend.

## Tecnologias

### Backend
- **Python 3.13** — linguagem principal
- **FastAPI** — framework web assíncrono
- **SQLAlchemy 2.0** — ORM para banco de dados
- **Alembic** — migrações de banco de dados
- **SQLite** — banco de dados padrão (PoC/simulação, zero setup); PostgreSQL opcional
- **Pydantic v2** — validação de dados
- **JWT** — estrutura preparada para autenticação futura

### Frontend
- **React 18** — biblioteca de interface
- **Vite** — bundler e dev server
- **TypeScript** — tipagem estática
- **TailwindCSS** — estilização utilitária
- **React Router** — navegação SPA
- **Axios** — cliente HTTP

## Estrutura de pastas

```
farol/
├── backend/
│   ├── app/
│   │   ├── config/        # Configurações e variáveis de ambiente
│   │   ├── core/          # Hashing, JWT e utilitários centrais
│   │   ├── database/      # Conexão e sessão do banco (lazy)
│   │   ├── models/        # Modelos SQLAlchemy
│   │   ├── repositories/  # Camada de acesso a dados
│   │   ├── routes/        # Endpoints FastAPI
│   │   ├── schemas/       # Schemas Pydantic
│   │   ├── services/      # Lógica de negócio
│   │   └── main.py        # Ponto de entrada da aplicação
│   ├── tests/             # Testes automatizados
│   ├── alembic/           # Migrações de banco de dados
│   ├── alembic.ini        # Configuração do Alembic
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/           # Cliente Axios e chamadas HTTP
│   │   ├── components/    # Componentes reutilizáveis
│   │   ├── pages/         # Páginas da aplicação
│   │   ├── App.tsx        # Componente raiz com rotas
│   │   ├── global.css     # Estilos globais (Tailwind)
│   │   └── main.tsx       # Ponto de entrada React
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── .env.example
├── .gitignore
└── README.md
```

## Como instalar

### Pré-requisitos
- Python 3.13 (funciona em 3.12+)
- Node.js 22+

> Esta é uma PoC/simulação: o backend usa **SQLite** por padrão, sem banco externo.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # já vem com SQLite configurado
alembic upgrade head       # cria as tabelas (passo obrigatório)
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Como executar

O banco padrão é SQLite, então não é preciso subir nenhum serviço externo. Garanta que as tabelas foram criadas com `alembic upgrade head` (veja acima).

### Backend (desenvolvimento)

```bash
cd backend
uvicorn app.main:app --reload
```

A API estará disponível em `http://localhost:8000` (docs em `http://localhost:8000/docs`).

### Frontend (desenvolvimento)

```bash
cd frontend
npm run dev
```

O frontend estará disponível em `http://localhost:5173`.

## Entidades do Domínio (Sprint 2)

Foram modeladas 8 entidades utilizando SQLAlchemy 2.0:

| Entidade | Tabela | Propósito |
|---|---|---|
| **Vertical** | `verticals` | Área da empresa (Viagens, Conecta, etc.) |
| **Usuário** | `usuarios` | Usuário da plataforma com papel (VERTICAL, MARKETING, LIDERANCA, ADMIN) |
| **Projeto** | `projetos` | Projeto criado por uma Vertical |
| **Checkpoint** | `checkpoints` | Etapa de avaliação (Ideação, Desenvolvimento, Pré-lançamento) |
| **Avaliação** | `avaliacoes_checkpoint` | Resultado da avaliação de um checkpoint |
| **Alerta** | `alertas` | Alerta gerado durante a avaliação |
| **Conversa** | `conversas` | Conversa privada entre Vertical e agente IA |
| **Mensagem** | `mensagens` | Mensagem individual dentro de uma conversa |

### Relacionamentos principais

- **Vertical** `1:N` **Usuário** — uma vertical possui vários usuários
- **Vertical** `1:N` **Projeto** — uma vertical possui vários projetos
- **Usuário** `1:N` **Projeto** — um usuário cria vários projetos
- **Projeto** `1:N` **Checkpoint** — um projeto passa por 3 checkpoints
- **Checkpoint** `1:1` **Avaliação** — cada checkpoint tem no máximo uma avaliação
- **Projeto** `1:1` **Conversa** — um projeto possui no máximo uma conversa
- **Conversa** `1:N` **Mensagem** — uma conversa possui várias mensagens
- **Projeto** `1:N` **Alerta** — um projeto pode ter vários alertas

### Enums

`PapelUsuario`, `StatusProjeto`, `TipoCheckpoint`, `StatusCheckpoint`, `ClassificacaoFarol`, `TipoAlerta`, `StatusAlerta`, `DecisaoHumana`, `AutorMensagem`

### Constraints relevantes

- `uq_checkpoint_projeto_tipo`: unique `(projeto_id, tipo)` — cada projeto só pode ter um checkpoint de cada tipo
- `ck_avaliacao_score_alinhamento` e `ck_avaliacao_score_potencial`: scores entre 0 e 100 quando preenchidos
- `uq_avaliacao_checkpoint`: um checkpoint só pode ter uma avaliação

## Migrações de Banco de Dados

### Aplicar a migração inicial

```bash
cd backend
alembic upgrade head
```

### Reverter a última migração

```bash
cd backend
alembic downgrade -1
```

### Criar uma nova migração (após alterar os modelos)

```bash
cd backend
alembic revision --autogenerate -m "descricao da alteracao"
```

Depois revise o arquivo gerado em `alembic/versions/` e aplique com `alembic upgrade head`.

### Verificar o estado do banco

```bash
cd backend
alembic current
alembic history
```

Para mais detalhes do modelo de dados, consulte `docs/database-model.md`.
