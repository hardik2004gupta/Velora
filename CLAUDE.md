# Velora — CLAUDE.md

Production-Inspired Multi-Provider AI Inference Platform
*Designed & Engineered by Hardik Gupta*

---

## Project Overview

Velora is an AI gateway inspired by OpenRouter, LiteLLM, and Helicone. It routes requests to multiple LLM providers (OpenAI, Anthropic, Gemini) through a single unified backend with intelligent routing, cost analytics, Redis caching, and a **Routing Decision Inspector** as its signature feature.

This is a portfolio project targeting top-tier Software Engineering / AI Infrastructure roles.

---

## Repository Layout

```
velora/
├── frontend/          # Next.js 15 app (deployed to Vercel)
├── backend/           # FastAPI app (deployed to Railway)
├── docker-compose.yml # Local dev — postgres + redis + both apps
├── .github/workflows/ # CI pipelines
└── CLAUDE.md
```

---

## Tech Stack

### Frontend
- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS + shadcn/ui
- TanStack Query (server state)
- Recharts (analytics charts)
- Framer Motion (animations)

### Backend
- FastAPI + Uvicorn
- SQLAlchemy (ORM) + Alembic (migrations)
- Pydantic v2 (validation)
- PyJWT (authentication)
- httpx (async HTTP to providers)
- APScheduler (background health checks)

### Data
- PostgreSQL via Neon (primary DB)
- Redis via Upstash (cache + rate limiting)

### Dev Tools
- Docker + Docker Compose (local dev)
- Pytest (backend tests)
- Ruff (linting + formatting)
- MyPy (type checking)
- Vitest + React Testing Library (frontend tests)
- GitHub Actions (CI)

---

## Architecture Principles

1. **Layered monolith** — single FastAPI process with clean internal module boundaries (`api/` → `services/` → `providers/`). No microservices.
2. **Separation of layers** — `api/` handles HTTP only, `services/` holds business logic, `providers/` holds external integrations. Layers never skip.
3. **No over-engineering** — solve the problem at hand. Three similar lines beats a premature abstraction.
4. **Deterministic routing** — all routing decisions are rule-based scoring, not ML. This enables the Routing Decision Inspector.
5. **Tests verify behavior** — test what the code does, not that it runs.

---

## Backend Folder Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI factory + middleware
│   ├── config.py                # Pydantic Settings (env vars)
│   ├── database.py              # SQLAlchemy engine + session
│   ├── dependencies.py          # Depends() — auth, db, redis
│   ├── api/v1/                  # HTTP layer (routes only)
│   │   ├── router.py
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── requests.py
│   │   ├── analytics.py
│   │   ├── providers.py
│   │   ├── api_keys.py
│   │   ├── settings.py
│   │   └── admin.py
│   ├── services/                # Business logic
│   │   ├── auth_service.py
│   │   ├── chat_service.py
│   │   ├── router_service.py
│   │   ├── cache_service.py
│   │   ├── rate_limit_service.py
│   │   ├── analytics_service.py
│   │   ├── health_service.py
│   │   ├── cost_service.py
│   │   ├── request_logger.py
│   │   ├── api_key_service.py
│   │   └── admin_service.py
│   ├── providers/               # LLM adapter layer
│   │   ├── base.py              # Abstract BaseProvider
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── gemini_provider.py
│   │   └── registry.py
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── api_key.py
│   │   ├── request.py
│   │   ├── provider_status.py
│   │   └── user_settings.py
│   ├── schemas/                 # Pydantic v2 schemas
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── request.py
│   │   ├── analytics.py
│   │   ├── provider.py
│   │   ├── api_key.py
│   │   └── admin.py
│   ├── core/
│   │   ├── security.py          # JWT + bcrypt
│   │   ├── exceptions.py        # Custom exception classes
│   │   ├── constants.py         # COST_TABLE, quality scores, provider names
│   │   └── logging.py
│   └── background/
│       └── health_checker.py    # Periodic provider health checks
├── alembic/
│   └── versions/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## Frontend Folder Structure

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                 # Landing page
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   └── (dashboard)/
│       ├── layout.tsx           # Sidebar + topbar shell
│       ├── dashboard/page.tsx
│       ├── playground/page.tsx
│       ├── inspector/page.tsx
│       ├── history/page.tsx
│       ├── history/[id]/page.tsx
│       ├── analytics/page.tsx
│       ├── providers/page.tsx
│       ├── api-keys/page.tsx
│       ├── settings/page.tsx
│       └── admin/page.tsx
├── components/
│   ├── ui/                      # shadcn/ui (auto-generated, never edit manually)
│   ├── layout/
│   ├── auth/
│   ├── playground/
│   ├── inspector/
│   ├── analytics/
│   ├── history/
│   └── providers/
├── hooks/
├── lib/
│   ├── api.ts                   # HTTP client with auth headers
│   ├── queryClient.ts
│   ├── streaming.ts
│   └── utils.ts
├── types/
├── store/
└── public/
```

---

## Database Schema (PostgreSQL)

### `users`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | gen_random_uuid() |
| email | VARCHAR(255) UNIQUE | Login identifier |
| hashed_password | VARCHAR(255) | bcrypt, never plain |
| full_name | VARCHAR(255) | — |
| is_active | BOOLEAN DEFAULT true | Soft disable |
| is_admin | BOOLEAN DEFAULT false | Admin gate |
| created_at / updated_at | TIMESTAMPTZ | — |

### `api_keys`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | — |
| user_id | UUID FK → users | CASCADE delete |
| name | VARCHAR(100) | Human label |
| key_prefix | VARCHAR(10) | First 8 chars, shown in UI |
| hashed_key | VARCHAR(255) | bcrypt hash of full key |
| last_used_at | TIMESTAMPTZ NULLABLE | — |
| expires_at | TIMESTAMPTZ NULLABLE | NULL = never |
| is_active | BOOLEAN DEFAULT true | Revocable |
| created_at | TIMESTAMPTZ | — |

### `requests`
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | — |
| user_id | UUID FK → users | — |
| provider | VARCHAR(50) | openai / anthropic / gemini |
| model | VARCHAR(100) | Exact model ID |
| routing_strategy | VARCHAR(20) | auto / cheapest / fastest / quality |
| prompt_tokens | INTEGER | — |
| completion_tokens | INTEGER | — |
| total_tokens | INTEGER | — |
| cost_usd | NUMERIC(12,8) | — |
| latency_ms | INTEGER | Provider call only |
| cache_hit | BOOLEAN DEFAULT false | — |
| status | VARCHAR(20) | success / error / timeout |
| error_message | TEXT NULLABLE | — |
| routing_decision | JSONB | Full RoutingDecision object |
| prompt_hash | VARCHAR(64) | SHA-256 of normalized prompt |
| created_at | TIMESTAMPTZ | — |

**Key indexes:** `(user_id)`, `(created_at)`, `(provider)`, `(user_id, created_at)`

### `provider_status`
| Column | Type | Notes |
|---|---|---|
| provider | VARCHAR(50) UNIQUE | Standalone, no FK |
| status | VARCHAR(20) | healthy / degraded / down |
| latency_ms | INTEGER NULLABLE | Latest measurement |
| avg_latency_ms | INTEGER NULLABLE | Rolling average |
| uptime_percentage | NUMERIC(5,2) NULLABLE | Last 24h |
| last_checked_at | TIMESTAMPTZ | — |
| error_message | TEXT NULLABLE | — |

### `user_settings`
| Column | Type | Notes |
|---|---|---|
| user_id | UUID FK UNIQUE → users | 1:1 enforced |
| default_routing_strategy | VARCHAR(20) DEFAULT 'auto' | — |
| default_model | VARCHAR(100) NULLABLE | — |
| theme | VARCHAR(10) DEFAULT 'dark' | — |
| max_tokens | INTEGER DEFAULT 2048 | — |
| temperature | NUMERIC(3,2) DEFAULT 0.70 | — |

---

## API Endpoints

Base: `https://api.velora.dev/api/v1`

### Auth
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/auth/register` | No | Create account |
| POST | `/auth/login` | No | Get JWT token |
| GET | `/auth/me` | JWT | Current user profile |

### Chat
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/chat/completions` | JWT or API Key | Core inference endpoint (streaming SSE) |

### Requests
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/requests` | JWT | Paginated history with filters |
| GET | `/requests/{id}` | JWT | Full request detail + routing decision |

### Analytics
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/analytics/overview` | JWT | Summary stats (period param) |
| GET | `/analytics/cost-over-time` | JWT | Daily cost series |
| GET | `/analytics/latency-over-time` | JWT | Latency by provider |
| GET | `/analytics/provider-distribution` | JWT | Usage breakdown |

### Providers
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/providers/status` | JWT | Current health of all providers |

### API Keys
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api-keys` | JWT | List user's keys |
| POST | `/api-keys` | JWT | Create key (returns full key once) |
| DELETE | `/api-keys/{id}` | JWT | Revoke key |

### Settings
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/settings` | JWT | Get user settings |
| PATCH | `/settings` | JWT | Update user settings |

### Admin
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/admin/users` | JWT + Admin | All users with stats |
| GET | `/admin/stats` | JWT + Admin | Platform-wide metrics |
| PATCH | `/admin/users/{id}/status` | JWT + Admin | Enable/disable user |

---

## Routing Logic

Routing is **deterministic and rule-based** — never ML-based. This is intentional: it enables full explainability for the Routing Decision Inspector.

### Strategies

**Cheapest** — Sort healthy providers by `cost_per_1k_tokens` ascending. Tie-break: lower latency.

**Fastest** — Sort healthy providers by `avg_latency_ms` ascending (Redis rolling average). Tie-break: lower cost.

**Highest Quality** — Sort healthy providers by `quality_score` descending (static config). Tie-break: lower latency.

**Auto** — Weighted composite score:
```
score = 0.35 × quality + 0.30 × cost_score + 0.25 × latency_score + 0.10 × health_score
```
Providers with `status = "down"` are excluded from all strategies. `"degraded"` providers receive a health_score penalty.

### Fallback
If a selected provider fails mid-request: mark it degraded in Redis (60s), retry once on next-best provider. If all providers fail, return 503.

### RoutingDecision Object
Every response includes:
```json
{
  "strategy": "cheapest",
  "candidates": [
    { "provider": "openai", "model": "gpt-4o-mini", "cost_per_1k": 0.00015, "avg_latency_ms": 820, "health": "healthy", "quality_score": 0.78, "score": 0.91 }
  ],
  "selected": "openai/gpt-4o-mini",
  "reason": "Lowest cost per token among healthy providers"
}
```

---

## Redis Key Patterns

| Purpose | Key | TTL |
|---|---|---|
| Prompt cache | `cache:{sha256_hash}` | 3600s (1h) |
| Rate limit counter | `rate:{user_id}:{minute_bucket}` | 60s |
| Provider latency list | `latency:{provider}` | Rolling, LTRIM to 100 |
| Provider health override | `health:{provider}` | 120s |

**Cache key hash input:** `normalize(prompt) + ":" + model + ":" + temperature + ":" + max_tokens`

**Rate limiting:** Fixed window. `INCR` then `EXPIRE 60`. Limit: 20 req/min (env configurable).

---

## Provider Abstraction

Every provider implements `BaseProvider` in `providers/base.py`:

- `get_id() → str`
- `get_available_models() → list[ModelConfig]`
- `normalize_request(messages, model, max_tokens, temperature) → dict`
- `call(normalized_request) → AsyncGenerator[str, None]`
- `count_tokens(messages, model) → int`
- `handle_error(exception) → VeloraException`

Adding a new provider = one new file + entry in `COST_TABLE` + register in `ProviderRegistry`.

### Cost Table (in `core/constants.py`)
```python
COST_TABLE = {
  "openai": {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
  },
  "anthropic": {
    "claude-sonnet-4-6": {"input": 0.003, "output": 0.015},
    "claude-haiku-4-5": {"input": 0.0008, "output": 0.004},
  },
  "gemini": {
    "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
    "gemini-2.0-pro": {"input": 0.0035, "output": 0.0105},
  },
}
```
Units: USD per 1K tokens.

---

## Security Rules

- **JWT:** HS256, 24h expiry. Payload: `{ sub: user_id, exp, iat }`. No refresh tokens in V1.
- **Passwords:** bcrypt cost factor 12. Never stored plain. Never logged.
- **API Keys:** `secrets.token_urlsafe(32)`. Format: `vk-{32chars}`. Store prefix + bcrypt hash only. Shown once at creation.
- **CORS:** Origins from env var. Credentials allowed.
- **SQL:** SQLAlchemy ORM only. No raw SQL. All input through Pydantic before DB.
- **Markdown rendering:** Use `react-markdown` + `rehype-sanitize`. Never `dangerouslySetInnerHTML`.
- **Env vars:** Never committed. See `.env.example` for required keys.

---

## Required Environment Variables

### Backend (`.env`)
```
DATABASE_URL=postgresql://...         # Neon connection string (SSL included)
REDIS_URL=redis://...                 # Upstash TLS URL
JWT_SECRET_KEY=...                    # 64+ char random secret
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
CORS_ORIGINS=https://velora.vercel.app,http://localhost:3000
RATE_LIMIT_PER_MINUTE=20
ENVIRONMENT=development               # or "production"
```

### Frontend (`.env.local`)
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000   # or Railway URL in prod
```

---

## Local Development

```bash
# 1. Clone and set up env files
cp backend/.env.example backend/.env
# fill in API keys

# 2. Start all services
docker-compose up

# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API docs: http://localhost:8000/docs
```

Docker Compose starts: FastAPI (port 8000), Next.js (port 3000), PostgreSQL (5432), Redis (6379).

Backend hot-reloads via `uvicorn --reload`. Frontend hot-reloads via Next.js dev server.

### Running Migrations
```bash
docker-compose exec backend alembic upgrade head
```

### Running Tests
```bash
# Backend
docker-compose exec backend pytest tests/ -v

# Frontend
cd frontend && npm run test
```

### Linting
```bash
# Backend
ruff check app/ tests/
ruff format app/ tests/
mypy app/

# Frontend
npm run lint
tsc --noEmit
```

---

## Naming Conventions

| Context | Convention | Example |
|---|---|---|
| Python files | snake_case | `router_service.py` |
| Python classes | PascalCase | `RoutingDecision` |
| Python functions/vars | snake_case | `select_provider()` |
| Python constants | SCREAMING_SNAKE | `COST_TABLE` |
| TypeScript files | kebab-case | `routing-decision-card.tsx` |
| React components | PascalCase | `RoutingDecisionCard` |
| React hooks | camelCase + `use` | `useChat` |
| TypeScript types | PascalCase | `RoutingDecision` |
| DB tables | snake_case | `provider_status` |
| DB columns | snake_case | `cost_usd` |
| API endpoints | kebab-case | `/api-keys` |

---

## Commit Convention

Format: `type(scope): description`

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`

Examples:
```
feat(router): add quality-based routing strategy
fix(cache): correct TTL expiry on cache miss
test(auth): add integration tests for login endpoint
```

---

## Branch Strategy

- `main` → production. Auto-deploys to Vercel + Railway. Direct pushes blocked.
- `feature/*` → new features. PR to main.
- `fix/*` → bug fixes. PR to main.
- `chore/*` → tooling changes. PR to main.

CI must pass before merging.

---

## Deployment

| Service | Platform | Trigger |
|---|---|---|
| Frontend | Vercel | Push to `main` |
| Backend | Railway | Push to `main` |
| Database | Neon | Managed (run `alembic upgrade head` at deploy) |
| Cache | Upstash | Managed |

All services communicate over HTTPS/TLS. API keys and secrets in platform environment variables only — never in code.

---

## CI Pipeline Summary

**Backend** (on every push + PR to main):
1. `ruff check` + `ruff format --check`
2. `mypy app/`
3. `pytest tests/` (with real Postgres + Redis as GitHub Actions services)

**Frontend** (on every push + PR to main):
1. `next lint` + `prettier --check`
2. `tsc --noEmit`
3. `next build`

---

## Pages

| Route | Purpose |
|---|---|
| `/` | Landing page — features, CTA, Routing Inspector preview |
| `/login` | Authentication |
| `/register` | Account creation |
| `/dashboard` | Stats overview + recent requests |
| `/playground` | Chat interface with streaming + routing inspector drawer |
| `/inspector` | Standalone routing decision explorer |
| `/history` | Paginated request history with filters |
| `/history/[id]` | Full request detail |
| `/analytics` | Cost + latency + provider charts |
| `/providers` | Real-time provider health |
| `/api-keys` | Manage programmatic access keys |
| `/settings` | User preferences |
| `/admin` | Platform-wide admin (admin only) |

---

## Key Design Decisions

**Why monolith?** Clean internal boundaries matter more than distribution for this scale. Extracting services later is easy when the boundaries are clear.

**Why deterministic routing?** ML-based routing can't explain its decisions. Deterministic scoring makes the Routing Decision Inspector possible — this is the signature feature.

**Why JSONB for routing_decision?** The structure evolves as providers/strategies are added. JSONB avoids migrations for new fields while remaining queryable.

**Why static cost table?** Provider pricing APIs don't exist. Static config updated periodically is accurate enough and requires zero infrastructure.

**Why Redis for rate limiting?** In-memory counters break when the backend scales horizontally. Redis is shared state.

**Why no refresh tokens in V1?** Complexity cost exceeds benefit at this stage. 24h JWT expiry is acceptable.

---

## Branding

- **Project:** Velora
- **Tagline:** Production-Inspired Multi-Provider AI Inference Platform
- **Footer:** Designed & Engineered by Hardik Gupta
- **GitHub:** https://github.com/hardik2004gupta
- **LinkedIn:** https://www.linkedin.com/in/hardikgupta2004/
