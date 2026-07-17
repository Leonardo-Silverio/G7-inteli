# Farol

Plataforma web moderna construída com Python FastAPI no backend e React com TypeScript no frontend.

> **Modo demonstração:** esta versão funciona sem OpenAI, chave de API, PostgreSQL ou
> qualquer serviço externo. Os projetos e a avaliação são fictícios e previsíveis,
> próprios para uma apresentação.

## Início rápido

Depois de instalar as dependências, um único comando inicia o backend e o frontend:

```bash
./start-demo.sh
```

Abra <http://localhost:5173>. Para encerrar os dois serviços, pressione `Ctrl+C` no
mesmo terminal.

| Serviço | Endereço |
|---|---|
| Aplicação | <http://localhost:5173> |
| API | <http://localhost:8000> |
| Documentação interativa da API | <http://localhost:8000/docs> |
| Verificação de saúde | <http://localhost:8000/api/health> |

## Rodar localmente

### Pré-requisitos

- Git;
- Python 3.12 ou mais recente;
- Node.js 22 e npm;
- Linux, macOS, WSL ou Git Bash no Windows para usar `start-demo.sh`.

Confira as versões disponíveis:

```bash
python3 --version
node --version
npm --version
```

No Windows, `python` pode ser usado no lugar de `python3`.

### 1. Clonar o repositório

```bash
git clone https://github.com/Leonardo-Silverio/G7-inteli.git
cd G7-inteli
```

### 2. Instalar o backend

Linux, macOS ou WSL:

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
deactivate
```

Windows PowerShell:

```powershell
py -3 -m venv backend/.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
deactivate
```

### 3. Instalar o frontend

Na raiz do repositório:

```bash
npm ci --prefix frontend
```

### 4. Iniciar a demonstração

Linux, macOS, WSL ou Git Bash:

```bash
chmod +x start-demo.sh
./start-demo.sh
```

O script encontra automaticamente `backend/.venv/bin/python`, `python` ou
`python3`, inicia a API na porta 8000 e o Vite na porta 5173.

### Alternativa: iniciar os serviços manualmente

Use dois terminais. No primeiro, execute o backend:

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

No PowerShell, substitua `.venv/bin/python` por `.venv\Scripts\python.exe`.

No segundo terminal, execute o frontend:

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

## Rodar no GitHub Codespaces (recomendado)

O repositório possui [`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json),
que instala automaticamente Python 3.13, Node.js 22, as dependências do backend e
as dependências do frontend.

1. No GitHub, clique em **Code → Codespaces → Create codespace on main**.
2. Aguarde o terminal concluir o comando `postCreateCommand`. Na primeira abertura,
   essa instalação pode levar alguns minutos.
3. No terminal do Codespaces, execute:

```bash
./start-demo.sh
```

4. O Codespaces deverá abrir a aplicação automaticamente. Se isso não acontecer,
   abra a aba **Ports** e clique no endereço da porta **5173 (Farol)**.

As portas 5173 e 8000 já são encaminhadas pelo Codespaces. A porta 5173 está marcada
como pública no dev container para permitir o compartilhamento do link durante a
apresentação. Não compartilhe esse endereço caso adicione dados reais ao projeto.

### Instruções para Copilot, agentes ou outra IA no Codespaces

Ao pedir para uma IA executar este projeto, forneça esta instrução:

> Trabalhe na raiz do repositório. Este é um modo de demonstração sem IA externa e
> sem banco obrigatório. Não crie chaves de API, não configure OpenAI ou PostgreSQL
> e não execute migrações. Se as dependências ainda não estiverem instaladas, rode
> `pip install -r backend/requirements.txt` e `npm ci --prefix frontend`. Depois rode
> `./start-demo.sh`, aguarde as portas 8000 e 5173 iniciarem e abra a porta 5173.

Para validar a execução pelo terminal, a IA pode rodar:

```bash
curl --fail http://localhost:8000/api/health
curl --fail --head http://localhost:5173
```

A primeira resposta deve conter `"status":"ok"`; a segunda deve retornar um código
HTTP 200.

## Como funciona o modo de demonstração

- Os projetos e indicadores vêm do endpoint local `/api/demo/dashboard`.
- A avaliação usa `/api/demo/evaluate` e sempre retorna uma resposta fictícia.
- A pequena espera ao avaliar é intencional e também simulada.
- Nenhum conteúdo é enviado pela internet.
- Não é necessário criar `.env`, cadastrar usuário, subir PostgreSQL ou executar
  `alembic upgrade head` para demonstrar o dashboard.

### Roteiro rápido de apresentação

1. Mostre os indicadores e os projetos recentes no dashboard.
2. Clique em um projeto ou em **Nova avaliação**.
3. Edite a descrição, se desejar, e clique em **Simular avaliação**.
4. Mostre a nota, pontos fortes, alertas e próximo passo sugerido.

## Testes e verificações

Frontend:

```bash
npm run build --prefix frontend
```

Backend, com o ambiente virtual criado:

```bash
backend/.venv/bin/python -m pytest backend/tests -q
```

Se o `pytest` não estiver instalado:

```bash
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
```

## Solução de problemas

### `Permission denied: ./start-demo.sh`

```bash
chmod +x start-demo.sh
./start-demo.sh
```

### `No module named uvicorn`

As dependências foram instaladas em outro Python ou ainda não foram instaladas:

```bash
backend/.venv/bin/python -m pip install -r backend/requirements.txt
```

### `npm: command not found`

Instale Node.js 22. No Codespaces, reconstrua o container pelo menu de comandos com
**Codespaces: Rebuild Container**.

### Porta 5173 ou 8000 já está em uso

Encerre a execução anterior com `Ctrl+C`. Para localizar processos remanescentes em
Linux, macOS ou Codespaces:

```bash
lsof -i :5173
lsof -i :8000
```

### O dashboard mostra que o backend está indisponível

Confirme se <http://localhost:8000/api/health> responde. Ao executar manualmente,
mantenha backend e frontend ativos em terminais diferentes. No Codespaces, confirme
que ambas as portas aparecem na aba **Ports**.

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
