<div align="center">

# ⚡ Velora

**Production-Inspired Multi-Provider AI Inference Platform**

[![Backend CI](https://github.com/hardik2004gupta/Velora/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/hardik2004gupta/Velora/actions/workflows/backend-ci.yml)
[![Frontend CI](https://github.com/hardik2004gupta/Velora/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/hardik2004gupta/Velora/actions/workflows/frontend-ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org)

Route LLM requests across **OpenAI**, **Anthropic**, and **Google Gemini** through a single unified API — with deterministic smart routing, Redis prompt caching, cost analytics, and a **Routing Decision Inspector** that explains every provider choice in plain English.

[**Live Demo**](https://velora.vercel.app) · [**API Docs**](https://api.velora.dev/docs) · [**GitHub**](https://github.com/hardik2004gupta/Velora)

</div>

---

## What Is Velora?

Velora is an AI gateway inspired by OpenRouter, LiteLLM, and Helicone. Instead of hardcoding a single LLM provider into your application, you send requests to Velora and it:

1. **Scores** every available provider across quality, cost, latency, and health
2. **Selects** the best provider for your routing strategy (auto / cheapest / fastest / quality)
3. **Streams** the response token-by-token via Server-Sent Events
4. **Explains** the decision through the Routing Decision Inspector
5. **Caches** identical prompts in Redis to return sub-5ms responses on repeats
6. **Logs** every request with full cost and latency tracking

The signature feature is the **Routing Decision Inspector** — a visual dashboard showing exactly which providers were considered, how they scored across 4 dimensions, and why one was chosen. No black-box decisions.

---

## Architecture

```mermaid
graph TB
    subgraph Client
        Browser[Browser / API Client]
    end

    subgraph Frontend["Frontend (Vercel)"]
        NextJS[Next.js 15\nApp Router]
    end

    subgraph Backend["Backend (Railway)"]
        FastAPI[FastAPI + Uvicorn]
        Router[RouterService\nDeterministic Scoring]
        Cache[CacheService]
        RateLimit[RateLimitService]
        Logger[RequestLogger\nAsync Fire-and-Forget]
    end

    subgraph Providers["LLM Providers"]
        OpenAI[OpenAI API]
        Anthropic[Anthropic API]
        Gemini[Google Gemini]
    end

    subgraph Data["Data Layer"]
        PG[(PostgreSQL\nNeon)]
        Redis[(Redis\nUpstash)]
    end

    Browser --> NextJS
    NextJS -->|REST / SSE| FastAPI
    FastAPI --> RateLimit --> Redis
    FastAPI --> Cache --> Redis
    FastAPI --> Router
    Router --> OpenAI
    Router --> Anthropic
    Router --> Gemini
    FastAPI --> Logger --> PG
```

---

## Request Lifecycle

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant RL as Rate Limiter
    participant CA as Cache
    participant RT as Router
    participant P as Provider
    participant DB as PostgreSQL

    C->>API: POST /api/v1/chat/stream
    API->>RL: check_and_increment(user_id)
    alt Over limit
        RL-->>C: 429 Too Many Requests
    end
    API->>CA: get(SHA-256 hash)
    alt Cache Hit
        CA-->>API: cached_response
        API-->>C: SSE done {cache_hit: true}
    else Cache Miss
        CA-->>API: null
        API->>RT: select(strategy)
        Note over RT: Score all providers by\nquality · cost · latency · health
        RT-->>API: RoutingDecision
        API->>P: stream(messages, model)
        P-->>API: token deltas
        API-->>C: SSE delta events
        API->>CA: set(hash, response, ttl=3600)
        API->>DB: log_request [async]
        API-->>C: SSE done {routing_decision, cache_hit: false}
    end
```

---

## Routing Algorithm

Routing is **deterministic and rule-based** — not ML. Every decision is fully explainable.

```
Auto Strategy Composite Score:
  score = 0.35 × quality_score
        + 0.30 × cost_score        (inverted: lower cost → higher score)
        + 0.25 × latency_score     (inverted: lower latency → higher score)
        + 0.10 × health_score      (degraded providers receive a penalty)

Providers with status = "down" are excluded entirely.
Fallback: if primary provider fails before yielding tokens, retry on next-best.
```

| Strategy  | Selection Criteria | Tie-break |
|-----------|--------------------|-----------|
| `auto` | Highest composite score (4 weighted dimensions) | — |
| `cheapest` | Lowest `cost_per_1k_tokens` | Lower latency |
| `fastest` | Lowest `avg_latency_ms` (Redis rolling average) | Lower cost |
| `quality` | Highest `quality_score` (static config) | Lower latency |
| `manual` | User-specified provider + model | — |

---

## Features

| Feature | Description |
|---------|-------------|
| 🧠 **Smart Routing** | Auto / Cheapest / Fastest / Quality strategies with deterministic scoring |
| 🔍 **Routing Inspector** | Visual breakdown of every routing decision — scores, reasons, candidates |
| ⚡ **Redis Caching** | SHA-256 prompt hash, 1h TTL, sub-5ms cache hits, hit/miss tracking |
| 🛡️ **Rate Limiting** | Fixed-window per-user limiting (20 req/min), Redis-backed, fails open |
| 🔀 **Provider Fallback** | Automatic retry on next-best provider if primary fails |
| 📊 **Cost Analytics** | Per-provider daily cost, latency P50/P95, token usage, routing insights |
| 🏥 **Health Monitoring** | Real-time health checks with EMA latency rolling average |
| 🔑 **API Keys** | Personal `vk-` prefixed keys, bcrypt-hashed, revocable |
| 📋 **Request History** | Full request log with routing decision, prompt, response, cost |
| 🌊 **SSE Streaming** | Token-by-token streaming with `AsyncGenerator` + `StreamingResponse` |
| 👤 **JWT Auth** | HS256 tokens, bcrypt passwords (cost 12), secure sessions |
| 🔧 **Admin Dashboard** | Platform-wide metrics and user management |

---

## Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page — product overview, architecture preview |
| `/login` · `/register` | Authentication |
| `/dashboard` | Stats overview, recent requests, cache hit rate |
| `/playground` | Multi-turn chat with streaming + routing decision card |
| `/inspector` | **Signature feature** — full routing decision visualization |
| `/history` | Paginated request log with filters (provider, status, sort) |
| `/history/[id]` | Full request detail — prompt, response, routing decision |
| `/analytics` | Charts: cost over time, latency, provider distribution, tokens |
| `/providers` | Real-time provider health (60s auto-refresh) |
| `/api-keys` | Create / revoke personal API keys |
| `/settings` | Cache stats, cache clear, inference defaults |
| `/admin` | Platform-wide metrics (admin only) |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 15 (App Router) | SSR, routing, streaming |
| | TypeScript | Type safety |
| | Tailwind CSS + shadcn/ui | UI components |
| | TanStack Query | Server state |
| | Zustand | Client state (auth, playground) |
| | Recharts | Analytics charts |
| | Framer Motion | Animations |
| **Backend** | FastAPI + Uvicorn | Async HTTP server |
| | Python 3.12 | Runtime |
| | Pydantic v2 | Validation |
| | SQLAlchemy 2 (async) | ORM |
| | Alembic | Database migrations |
| | PyJWT + passlib | Auth |
| | redis.asyncio | Redis client |
| **Data** | PostgreSQL 16 (Neon) | Primary database |
| | Redis 7 (Upstash) | Cache + rate limiting |
| **DevOps** | Docker + Compose | Local dev |
| | GitHub Actions | CI/CD |
| | Vercel | Frontend deployment |
| | Railway | Backend deployment |

---

## Quick Start

### Prerequisites

- Docker + Docker Compose
- API key for at least one provider (OpenAI, Anthropic, or Gemini)

### 1. Clone and configure

```bash
git clone https://github.com/hardik2004gupta/Velora.git
cd Velora
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials
```

### 2. Start all services

```bash
docker-compose up
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Health | http://localhost:8000/api/v1/health |

### 3. Run migrations

```bash
docker-compose exec backend poetry run alembic upgrade head
```

### 4. Register and explore

Navigate to http://localhost:3000, create an account, and try the Playground.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://user:pass@host/db` |
| `REDIS_URL` | ✅ | `redis://host:6379/0` |
| `JWT_SECRET_KEY` | ✅ | 64+ char random secret |
| `OPENAI_API_KEY` | ⚠️ one required | OpenAI provider |
| `ANTHROPIC_API_KEY` | ⚠️ | Anthropic provider |
| `GEMINI_API_KEY` | ⚠️ | Gemini provider |
| `CORS_ORIGINS` | ✅ | Comma-separated allowed origins |
| `RATE_LIMIT_PER_MINUTE` | — | Default: `20` |
| `ENVIRONMENT` | — | `development` or `production` |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | ✅ | Backend URL |

---

## Development

```bash
# Backend without Docker
cd backend && poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload

# Frontend without Docker
cd frontend && npm install && npm run dev

# Tests
cd backend && poetry run pytest tests/unit/ -v
cd frontend && npm run test

# Linting
cd backend && poetry run ruff check app/ tests/ && poetry run mypy app/
cd frontend && npm run lint && npx tsc --noEmit
```

---

## API Reference

Base URL: `https://api.velora.dev/api/v1`  
Auth: `Authorization: Bearer <jwt>` or `X-API-Key: vk-<key>`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Create account |
| `POST` | `/auth/login` | Get JWT |
| `POST` | `/chat/stream` | **Streaming chat (SSE)** |
| `POST` | `/chat` | Non-streaming chat |
| `GET` | `/requests` | Paginated history |
| `GET` | `/analytics/overview` | Summary stats |
| `GET` | `/providers/status` | Live health |
| `GET/POST/DELETE` | `/api-keys` | Personal key management |
| `GET` | `/cache/stats` | Cache metrics |
| `POST` | `/cache/clear` | Clear cache |

Full Swagger docs at `/docs` (development mode).

---

## Database Schema

```mermaid
erDiagram
    users {
        uuid id PK
        varchar email UK
        varchar hashed_password
        boolean is_active
        boolean is_admin
        timestamptz created_at
    }
    requests {
        uuid id PK
        uuid user_id FK
        varchar provider
        varchar model
        varchar routing_strategy
        numeric cost_usd
        integer latency_ms
        boolean cache_hit
        jsonb routing_decision
        timestamptz created_at
    }
    user_api_keys {
        uuid id PK
        uuid user_id FK
        varchar key_prefix
        varchar hashed_key
        boolean is_active
    }
    provider_status {
        varchar provider PK
        varchar status
        integer avg_latency_ms
        timestamptz last_checked_at
    }
    users ||--o{ requests : makes
    users ||--o{ user_api_keys : owns
```

---

## Project Structure

```
velora/
├── frontend/
│   ├── app/(dashboard)/
│   │   ├── playground/     # Chat + streaming
│   │   ├── inspector/      # Routing Decision Inspector ⭐
│   │   ├── analytics/      # Charts + metrics
│   │   └── ...
│   ├── components/
│   │   ├── playground/     # Chat UI, routing card
│   │   └── analytics/      # Recharts components
│   ├── store/              # Zustand stores
│   └── hooks/              # Data hooks
│
├── backend/app/
│   ├── api/v1/             # HTTP layer (routes only)
│   ├── services/
│   │   ├── router_service.py     # Routing engine ⭐
│   │   ├── cache_service.py      # Redis cache
│   │   └── rate_limit_service.py # Rate limiting
│   ├── providers/          # LLM adapters (BaseProvider)
│   ├── models/             # SQLAlchemy ORM
│   └── cache/              # Redis client + key builders
│
├── docker-compose.yml
└── .github/workflows/
```

---

## System Design Decisions

**Why a layered monolith?** Clean internal boundaries (`api/` → `services/` → `providers/`) give separation of concerns without distribution complexity.

**Why deterministic routing?** ML-based routing cannot explain its decisions. Rule-based scoring makes the Routing Decision Inspector possible — the project's key differentiator.

**Why JSONB for `routing_decision`?** The structure evolves as providers and strategies change. JSONB stores arbitrary shapes without schema migrations.

**Why Redis for rate limiting?** In-memory counters break when the backend scales horizontally.

**Why fail-open for cache and rate limiting?** If Redis is unavailable, requests should still succeed — just without caching or rate limiting. Service degradation beats false 429s or 503s.

**Why async throughout?** LLM calls take 2–30 seconds. FastAPI + asyncio handles thousands of concurrent streaming connections without blocking threads.

---

## Future Roadmap

- [ ] Webhook support for async completion callbacks
- [ ] Usage budgets and spending alerts
- [ ] Team workspace sharing
- [ ] Custom provider adapters
- [ ] A/B routing strategy testing
- [ ] Prompt template library

---

## Contributing

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Follow commit convention: `type(scope): description`
4. Ensure CI passes (lint, type check, tests)
5. Open a pull request using the [PR template](.github/pull_request_template.md)

---

## License

[MIT](LICENSE) © 2026 Hardik Gupta

---

<div align="center">

**Designed & Engineered by [Hardik Gupta](https://github.com/hardik2004gupta)**

[![GitHub](https://img.shields.io/badge/GitHub-hardik2004gupta-181717?logo=github)](https://github.com/hardik2004gupta)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-hardikgupta2004-0A66C2?logo=linkedin)](https://www.linkedin.com/in/hardikgupta2004/)

</div>
