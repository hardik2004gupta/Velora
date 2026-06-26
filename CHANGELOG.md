# Changelog

All notable changes to Velora are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-06-27

### 🎉 Initial public release — Velora v1.0

---

### Backend

#### Added
- **FastAPI gateway** with layered monolith architecture (`api/` → `services/` → `providers/`)
- **Multi-provider LLM support** — OpenAI, Anthropic (Claude), Google Gemini
- **Deterministic routing engine** (`RouterService`) with four strategies:
  - `auto` — weighted composite score (quality 35%, cost 30%, latency 25%, health 10%)
  - `cheapest` — lowest cost per token
  - `fastest` — lowest rolling-average latency
  - `quality` — highest quality score
  - `manual` — user-specified provider + model
- **Provider fallback** — automatic retry on next-best healthy candidate if primary fails
- **Redis prompt caching** (`CacheService`) — SHA-256 key hash, 1-hour TTL, hit/miss counters, fails open
- **Rate limiting** (`RateLimitService`) — fixed-window per-user (20 req/min), Redis-backed, fails open
- **Personal API keys** (`user_api_keys` table) — `vk-` prefix, bcrypt-hashed, revocable, `X-API-Key` auth
- **JWT authentication** — HS256, 24-hour expiry, bcrypt passwords (cost factor 12)
- **SSE streaming** — `AsyncGenerator` + `StreamingResponse` for token-by-token delivery
- **Request logging** — async fire-and-forget, full routing decision in JSONB column
- **Analytics service** — cost over time (by provider), latency with PostgreSQL P50/P95 percentiles, token analytics, routing insights
- **Provider health monitoring** — live checks, EMA rolling average, DB persistence
- **Admin endpoints** — platform-wide stats, user management
- **Middleware stack** — RequestID, Security headers, Timing, GZip, CORS
- **Structured logging** — JSON in production, console in development

#### Database
- `users` — accounts with bcrypt passwords
- `requests` — full request log with `routing_decision` JSONB, `cache_hit`, `cost_usd`
- `user_api_keys` — personal API key management
- `provider_status` — health check results with EMA latency
- `user_settings` — per-user inference defaults
- Alembic migrations 001–003

#### API Endpoints
- `POST /auth/register` · `POST /auth/login` · `GET /auth/me`
- `POST /chat/stream` · `POST /chat`
- `GET /requests` · `GET /requests/{id}`
- `GET /analytics/overview|cost|latency|providers|tokens|conversations|routing`
- `GET /providers/status`
- `GET|POST|DELETE /api-keys`
- `GET /cache/stats` · `POST /cache/clear`
- `GET|PATCH /settings`
- `GET|PATCH /admin/users` · `GET /admin/stats`

---

### Frontend

#### Added
- **Next.js 15** App Router with full TypeScript
- **Landing page** — hero, feature grid, architecture preview, tech stack
- **AI Playground** — multi-turn streaming chat, routing decision card, strategy selector
- **Routing Decision Inspector** — visualizes every routing decision with score bars, candidate comparison, breakdown by dimension (quality, cost, latency, health); shows cache hit and fallback info
- **Request History** — paginated table with provider/status filters, CSV/JSON export
- **Request Detail** — full prompt/response view with routing decision
- **Analytics Dashboard** — 6 Recharts charts (cost area, latency line, provider pie, status donut, token bar, routing bar), period selector, provider comparison table
- **Provider Health** — live cards with 60-second auto-refresh, comparison table
- **API Keys** — create/revoke personal keys with once-visible key reveal + copy button
- **Settings** — live cache stats, clear cache, inference defaults
- **Dashboard** — overview stats, recent requests, cache hit rate card
- **Admin** — platform-wide metrics (admin-gated)
- **Auth pages** — login, register with form validation
- **Dark mode** — consistent across all pages via Tailwind CSS variables
- Zustand stores: auth (persisted), playground (routing decisions, conversation state)
- TanStack Query data hooks for all API endpoints
- SSE streaming hook with abort controller support

---

### Infrastructure

#### Added
- **Docker Compose** — Postgres 16, Redis 7, backend, frontend with health checks
- **Multi-stage Dockerfiles** — non-root users, minimal runtime images
- **GitHub Actions CI**
  - Backend: Ruff lint + format, MyPy type check, Pytest (unit + integration), Docker build
  - Frontend: ESLint, TypeScript check, Next.js build
- **MIT License**
- **Comprehensive README** with Mermaid architecture diagrams

---

## [Unreleased]

### Planned
- Webhook support for async completion callbacks
- Usage budgets and spending alerts
- Team workspace sharing
- Custom provider adapters
- A/B routing strategy testing

---

[1.0.0]: https://github.com/hardik2004gupta/Velora/releases/tag/v1.0.0
