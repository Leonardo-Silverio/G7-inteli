# Farol

Plataforma web moderna construída com Python FastAPI no backend e React com TypeScript no frontend.

## Tecnologias

### Backend
- **Python 3.13** — linguagem principal
- **FastAPI** — framework web assíncrono
- **SQLAlchemy 2.0** — ORM para banco de dados
- **Alembic** — migrações de banco de dados
- **PostgreSQL** — banco de dados relacional
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
│   ├── Dockerfile
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
│   ├── nginx/             # Configuração de proxy reverso
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── .env.example
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Como instalar

### Pré-requisitos
- Python 3.13
- Node.js 22+
- PostgreSQL 16+
- (Opcional) Docker e Docker Compose

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edite o .env com suas configurações
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

Inicie o PostgreSQL e configure o banco de dados `farol`.

### Backend (desenvolvimento)

```bash
cd backend
uvicorn app.main:app --reload
```

A API estará disponível em `http://localhost:8000`.

### Frontend (desenvolvimento)

```bash
cd frontend
npm run dev
```

O frontend estará disponível em `http://localhost:5173`.

## Como rodar usando Docker

```bash
docker compose up --build
```

Isso iniciará:

- **PostgreSQL** na porta `5432`
- **Backend** na porta `8000`
- **Frontend** na porta `8080`

Acesse `http://localhost:8080` para ver a aplicação.
