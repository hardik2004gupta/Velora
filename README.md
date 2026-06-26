# Velora

**Production-Inspired Multi-Provider AI Inference Platform**

Route requests to multiple LLM providers through a single unified API with intelligent routing, cost analytics, Redis caching, and a **Routing Decision Inspector** — see exactly why each provider was chosen.

*Designed & Engineered by Hardik Gupta*
[GitHub](https://github.com/hardik2004gupta) · [LinkedIn](https://www.linkedin.com/in/hardikgupta2004/)

---

## Features

- **Multi-provider support** — OpenAI, Anthropic, Gemini through a single endpoint
- **Smart routing** — Auto / Cheapest / Fastest / Highest Quality strategies
- **Routing Decision Inspector** — full transparency into every routing decision
- **Redis prompt caching** — identical prompts served from cache in < 5ms
- **Cost analytics** — track spending per provider, per day, per model
- **Rate limiting** — per-user fixed-window rate limiting
- **API key management** — programmatic access with revocable keys
- **Provider health monitoring** — real-time status with latency tracking
- **Admin dashboard** — platform-wide metrics

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, Python 3.12, Pydantic v2 |
| Database | PostgreSQL 16 (Neon in production) |
| Cache | Redis 7 (Upstash in production) |
| Auth | JWT (HS256), bcrypt |
| Deployment | Vercel (frontend), Railway (backend) |

---

## Quick Start

### Prerequisites

- Docker + Docker Compose
- API keys for at least one of: OpenAI, Anthropic, Gemini

### 1. Clone and configure

```bash
git clone https://github.com/hardik2004gupta/velora
cd velora
cp backend/.env.example backend/.env
# Open backend/.env and fill in your API keys and secrets
```

### 2. Start all services

```bash
docker-compose up
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Health check | http://localhost:8000/api/v1/health |

### 3. Run database migrations

```bash
docker-compose exec backend poetry run alembic upgrade head
```

---

## Development

### Backend only (without Docker)

```bash
cd backend
poetry install
cp .env.example .env    # fill in your values
poetry run uvicorn app.main:app --reload
```

### Run tests

```bash
# Unit tests (no external services required)
cd backend
poetry run pytest tests/unit/ -v

# All tests (requires running PostgreSQL + Redis)
poetry run pytest tests/ -v
```

### Linting

```bash
cd backend
poetry run ruff check app/ tests/
poetry run ruff format app/ tests/
poetry run mypy app/
```

---

## Project Structure

```
velora/
├── frontend/          # Next.js 15 app
├── backend/           # FastAPI service
│   ├── app/
│   │   ├── api/v1/    # HTTP routes
│   │   ├── services/  # Business logic
│   │   ├── providers/ # LLM adapters
│   │   ├── models/    # SQLAlchemy ORM
│   │   ├── schemas/   # Pydantic v2
│   │   ├── cache/     # Redis layer
│   │   └── core/      # Exceptions, constants, security
│   └── tests/
├── docker-compose.yml
└── .github/workflows/ # CI pipelines
```

---

## Environment Variables

See [`backend/.env.example`](backend/.env.example) for all required variables.

Critical variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `JWT_SECRET_KEY` | 64+ char random secret |
| `OPENAI_API_KEY` | Optional — enables OpenAI provider |
| `ANTHROPIC_API_KEY` | Optional — enables Anthropic provider |
| `GEMINI_API_KEY` | Optional — enables Gemini provider |

---

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full Phase 0 architecture blueprint.

---

*Designed & Engineered by Hardik Gupta*
