# Velora — Interview Guide

*A complete walkthrough for technical interviews, system design discussions, and portfolio presentations.*

---

## 30-Second Pitch

> Velora is a production-inspired AI gateway that routes requests across OpenAI, Anthropic, and Gemini through a single unified API. Its signature feature is the **Routing Decision Inspector** — a real-time visualization that shows exactly which providers were evaluated, how they scored, and why one was selected. The routing is deterministic (no ML), which makes every decision fully explainable. Built with FastAPI, Next.js 15, PostgreSQL, and Redis.

---

## Architecture Walkthrough

### System Overview

Velora follows a **layered monolith** pattern:

```
Client → Next.js 15 (Vercel)
              ↓  REST / SSE
         FastAPI (Railway)
         ├── api/v1/       — HTTP only (no business logic)
         ├── services/     — All business logic
         │   ├── RouterService      — deterministic provider selection
         │   ├── CacheService       — Redis prompt caching
         │   ├── RateLimitService   — fixed-window limiting
         │   └── AnalyticsService   — PostgreSQL aggregations
         ├── providers/    — LLM adapters (BaseProvider)
         └── models/       — SQLAlchemy ORM
              ↓
         PostgreSQL (Neon) + Redis (Upstash)
```

**Why a monolith instead of microservices?**
At this scale, clean module boundaries matter more than distribution. A layered monolith with clear contracts between layers is easier to reason about, test, and deploy. Extracting individual services later is trivial when the boundaries are already enforced.

---

## The Routing Engine

### Why deterministic routing?

ML-based routing is a black box. You can't explain why it chose GPT-4o-mini over Claude Haiku in this specific request. Deterministic rule-based scoring makes the **Routing Decision Inspector** possible — the feature that differentiates Velora from other gateways.

### Scoring Algorithm

Every request runs all (provider, model) pairs through a scoring function:

```python
# Auto strategy — weighted composite
score = 0.35 × quality_score      # benchmark aggregate (static config)
      + 0.30 × cost_score          # inverted: $0.00015/1K → high score
      + 0.25 × latency_score       # inverted: 820ms → medium score
      + 0.10 × health_score        # 1.0 = healthy, 0.5 = degraded

# Providers with health == "down" are excluded entirely
```

Cost and latency scores are **normalized across all candidates** so the cheapest model always gets 1.0 and the most expensive always gets 0.0.

### How it's fully explainable

Every `ChatResponse` includes a `RoutingDecision` object:

```json
{
  "strategy": "auto",
  "selected": "openai/gpt-4o-mini",
  "reason": "Selected openai/gpt-4o-mini with highest composite score (0.852)",
  "candidates": [
    {
      "provider": "openai",
      "model": "gpt-4o-mini",
      "score": 0.852,
      "score_breakdown": { "quality": 0.78, "cost": 0.91, "latency": 0.79, "health": 1.0 }
    }
  ]
}
```

This is stored in the `requests.routing_decision` JSONB column and displayed in the Inspector.

### Provider Fallback

If the primary provider fails *before* yielding any tokens, Velora retries on the next-best healthy candidate from the routing result. Fallback is recorded in the response as `fallback_provider`.

---

## Prompt Caching

### Design

- **Key**: `SHA-256(normalize(prompt) + ":" + model + ":" + temperature + ":" + max_tokens)`
- **Store**: Redis STRING with 1-hour TTL
- **Hit tracking**: Two Redis counters (`cache:stats:hits`, `cache:stats:misses`)
- **Fail-open**: If Redis is unavailable, the request proceeds without caching

### Why SHA-256?

Collision probability is negligible (2^-256 per pair). Prompt normalization (whitespace collapse) ensures "hello  world" and "hello world" hit the same cache entry.

### Cache placement in the request flow

Rate limit → **cache check** → routing → provider call → **cache write** → log

The cache check happens *after* rate limiting (to count cache hits toward the limit) but *before* routing (to avoid even running the scoring algorithm on a cache hit).

---

## Rate Limiting

### Design

Fixed-window per-user using Redis INCR+EXPIRE:

```python
key = f"rate:{user_id}:{int(time.time()) // 60}"
count = await redis.incr(key)
if count == 1:
    await redis.expire(key, 60)  # set TTL only on first increment
if count > limit:
    raise RateLimitExceededError(retry_after_seconds=60)
```

### Why fixed-window over sliding-window?

Fixed-window is O(1) in Redis operations. A sliding-window approach (sorted sets + ZREMRANGEBYSCORE) is more accurate but 3–5x more Redis operations per request. For 20 req/min limits, the boundary-burst issue of fixed-window is acceptable.

### Fail-open

If Redis is down, `check_and_increment` catches the `RedisError` and logs a warning — but does **not** raise. The request is allowed through. False 429s are worse than temporarily missing rate limiting.

---

## Authentication & Security

### JWT

- Algorithm: HS256
- Expiry: 24 hours (configurable)
- Payload: `{ sub: user_id, exp, iat }` — minimal, no user data
- No refresh tokens in v1 (complexity cost exceeds benefit at this scale)

### Passwords

- bcrypt, cost factor 12
- Never logged, never returned in any API response
- Verified with `passlib.context.CryptContext`

### API Keys

- Format: `vk-{43 URL-safe chars}` (32 random bytes → base64url)
- Storage: prefix (first 8 chars for display) + bcrypt hash
- Auth: `X-API-Key` header → prefix lookup → bcrypt.verify
- `last_used_at` updated on every successful auth
- Shown **once** at creation, never again

### Security Headers Middleware

Applied globally: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`.

---

## Database Design

### Why JSONB for `routing_decision`?

The routing decision structure evolves as we add providers, strategies, and score dimensions. JSONB stores arbitrary shapes without schema migrations while remaining queryable with PostgreSQL's `->` operators.

### Why PostgreSQL for percentiles?

PostgreSQL's `percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms)` computes P50 and P95 in a single aggregation query. This is much cleaner than computing percentiles in Python.

### Key indexes

- `requests(user_id)` — all user-scoped queries
- `requests(created_at)` — time-range analytics
- `requests(provider)` — provider breakdown analytics
- `requests(user_id, created_at)` — compound for paginated history
- `user_api_keys(key_prefix)` — fast lookup during API key auth

### Async ORM

SQLAlchemy 2's async API (`AsyncSession`) with `asyncpg` driver allows the event loop to handle other requests while waiting on slow queries. The session is created per-request and injected via FastAPI's `Depends()`.

---

## Streaming

### Why SSE over WebSockets?

SSE is simpler (HTTP/1.1, unidirectional, native browser support with `EventSource`). WebSockets add handshake complexity and bidirectional state for a use case that only ever sends data in one direction (server → client).

### Implementation

```python
async def _run_stream(routing_result, ...) -> AsyncGenerator[str, None]:
    async for token in provider.call(normalized):
        response_collector.append(token)
        yield f"data: {json.dumps({'type': 'delta', 'content': token})}\n\n"
    yield f"data: {json.dumps({'type': 'done', ...})}\n\n"

return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### Frontend consumption

```typescript
for await (const chunk of streamChat(payload, signal)) {
    if (chunk.type === "delta") accumulated += chunk.content
    else if (chunk.type === "done") setRoutingDecision(chunk.routing_decision)
}
```

The `AbortController` allows the user to stop generation mid-stream.

---

## Provider Abstraction

Every LLM provider implements `BaseProvider`:

```python
class BaseProvider(ABC):
    def get_id(self) -> str
    def get_available_models(self) -> list[ModelConfig]
    def normalize_request(self, messages, model, max_tokens, temperature) -> dict
    async def call(self, normalized_request) -> AsyncGenerator[str, None]
    def count_tokens(self, messages, model) -> int
    def handle_error(self, exception) -> VeloraException
```

Adding a new provider = one new file + entry in `COST_TABLE` + `ProviderRegistry`. The routing engine, caching, logging, and streaming are all provider-agnostic.

---

## Scalability Discussion

### Current bottlenecks

1. **Single FastAPI process** — scales to ~thousands of concurrent connections (asyncio), limited by CPU for token processing
2. **PostgreSQL** — single Neon connection pool; would need read replicas for analytics at scale
3. **Redis** — Upstash handles horizontal scaling; no changes needed

### How I'd scale to 10x traffic

1. **Horizontal backend scaling**: Add `--workers 4` to uvicorn, or deploy multiple Railway instances. Rate limiting already works correctly with shared Redis. Cache already works correctly with shared Redis.
2. **Database read replicas**: Point analytics queries to a replica to avoid contention with write operations.
3. **Connection pooling**: PgBouncer in front of PostgreSQL for connection multiplexing.
4. **CDN for static assets**: Already handled by Vercel.

### How I'd scale to 100x traffic

1. Extract the **hot path** (rate limit + cache + stream) into a dedicated service; keep auth and analytics in the monolith.
2. Add a **message queue** (SQS/Kafka) for request logging — decouple the write from the response path.
3. **Sharding** the Redis rate limit keys by user_id bucket if a single Redis instance becomes a bottleneck.

---

## Trade-offs Made

| Decision | Chose | Over | Reason |
|----------|-------|------|--------|
| Routing | Deterministic scoring | ML/embedding-based | Explainability (Inspector), zero inference cost |
| Architecture | Layered monolith | Microservices | Simplicity, single deployment, easy debugging |
| Cache placement | Redis STRING | In-memory dict | Survives restarts, shared across instances |
| Rate limiting | Fixed window | Sliding window | O(1) Redis ops, acceptable for 20 req/min |
| Streaming | SSE | WebSockets | Simpler protocol, native browser support, unidirectional |
| Auth | JWT only | Session cookies | Stateless, works for both browser and API clients |
| Token counting | 4 chars ≈ 1 token | Provider API | Zero latency, acceptable accuracy for cost estimation |
| JSONB | routing_decision column | Normalized tables | Schema flexibility as routing evolves |

---

## Common Interview Questions & Strong Answers

### "Walk me through what happens when a user sends a message in the Playground."

> The frontend sends `POST /api/v1/chat/stream` with the message history, routing strategy, and parameters. FastAPI receives it and first checks the rate limit by INCRementing a Redis counter for the current user + minute bucket. If over 20 req/min, it returns 429. Next, it builds a SHA-256 hash of the normalized prompt + model + temperature and checks Redis. On a cache miss, `RouterService.select()` evaluates all healthy (provider, model) pairs using a 4-dimension weighted score, returning a `RoutingDecision`. The endpoint then calls the selected provider, yielding token deltas as SSE events. After the stream completes, it writes the response to Redis cache and fire-and-forgets a request log to PostgreSQL with the full routing decision in a JSONB column.

### "Why not just use LiteLLM or OpenRouter directly?"

> Velora's purpose is to understand the problem deeply, not just consume a library. The Routing Decision Inspector couldn't exist with a third-party routing library because you'd lose visibility into the scoring. Building it from scratch gave me deep understanding of provider normalization, async streaming patterns, token cost models, and deterministic scoring — which is what I'd apply in a production infrastructure role.

### "How does the routing score prevent gaming? E.g., a provider with low latency but terrible quality?"

> Each dimension is normalized to 0–1 across all candidates, then combined with fixed weights (35% quality, 30% cost, 25% latency, 10% health). A provider with amazing latency but poor quality would score high on latency_score but low on quality_score. Since quality has the highest weight, a low-quality provider can't win the `auto` strategy purely on speed. The `fastest` strategy ignores quality, but the user consciously opts into that trade-off.

### "What happens if Redis goes down?"

> Both the cache and rate limiter fail open. `CacheService.get()` catches `RedisError` and returns `None` — the request proceeds without a cache hit. `RateLimitService.check_and_increment()` catches `RedisError` and returns without raising — the request is allowed through. The application logs warnings but stays operational. I prioritized availability over perfect rate limiting consistency, which is the right call for a dev-facing tool.

### "Why store routing_decision in JSONB instead of a normalized table?"

> The routing decision schema evolves — new strategies add new fields, new providers add new score dimensions. Normalizing it would require a migration every time a new dimension is added. JSONB lets the schema evolve without migrations while still being queryable. The Inspector reads the entire JSONB blob anyway, so there's no benefit to normalization in the read path.

### "How would you add a new LLM provider?"

> 1. Create `app/providers/new_provider.py` implementing `BaseProvider` (five abstract methods).
> 2. Add pricing to `COST_TABLE` in `core/constants.py`.
> 3. Add quality scores and static latency to the constants.
> 4. Register in `ProviderRegistry`.
> Everything else — routing, caching, logging, streaming, analytics — works automatically because it's all provider-agnostic.

### "What's the most complex bug you hit while building this?"

> The trickiest issue was async generator cleanup in the streaming endpoint. When the client disconnects mid-stream (e.g., user closes the tab), the `finally` block in the `event_generator` must still run to log the partial request. Initially I had the `asyncio.create_task()` for logging outside the `finally`, so it would be skipped on abort. Moving it inside `finally` ensures partial responses are always logged with the correct latency and `error_message`.

---

## Resume Bullets

### ATS-Friendly Project Description

**Velora — Multi-Provider AI Inference Platform** | FastAPI · Next.js 15 · PostgreSQL · Redis · Docker

- Engineered a production-inspired AI gateway routing LLM requests across OpenAI, Anthropic, and Google Gemini through a single unified API with deterministic 4-dimension scoring (quality, cost, latency, health)
- Built a Redis-backed prompt cache with SHA-256 key hashing achieving sub-5ms cache hit latency, reducing provider API costs by eliminating duplicate requests
- Implemented SSE streaming with `AsyncGenerator` + FastAPI `StreamingResponse`, supporting thousands of concurrent token-streaming connections via asyncio
- Designed the **Routing Decision Inspector** — a visual dashboard exposing every provider scoring decision, enabling full transparency into the routing algorithm
- Deployed on Vercel (frontend) + Railway (backend) + Neon (PostgreSQL) + Upstash (Redis) with GitHub Actions CI (lint, type-check, pytest, Docker build)

### One-Line Description

> Production-inspired AI gateway that routes LLM requests across OpenAI, Anthropic, and Gemini with smart routing, Redis caching, and a real-time decision inspector.

### LinkedIn Project Description

**Velora — AI Inference Gateway** | 2026

Built a full-stack AI gateway (inspired by OpenRouter + LiteLLM) to deepen expertise in LLM infrastructure, async Python, and production system design.

Key technical achievements:
- Deterministic routing engine scoring providers across quality, cost, latency, and health — fully explainable, no ML required
- Redis prompt cache with SHA-256 hashing — sub-5ms cache hits, fails open on Redis unavailability
- Signature feature: Routing Decision Inspector showing every scoring breakdown in real-time
- End-to-end SSE streaming from provider → FastAPI → Next.js with abort controller support
- Full observability: request history, cost analytics (P50/P95 latency), provider health monitoring

**Stack**: FastAPI · Python 3.12 · Next.js 15 · TypeScript · PostgreSQL · Redis · Docker · Vercel · Railway

---

## 5-Minute Recruiter Demo Script

**Goal**: Show the product works and looks professional.

1. **Landing page** (30s): "This is Velora — an AI gateway that routes requests across OpenAI, Anthropic, and Gemini. See the feature overview here."

2. **Playground** (90s): "Let me send a message. Watch the strategy selector — I'm using Auto routing. You can see tokens streaming in real-time. When it completes, this routing card shows which provider was selected and why."

3. **Inspector** (60s): "Now let me open the Routing Inspector — Velora's signature feature. You can see all three providers were evaluated, scored on quality, cost, latency, and health. GPT-4o-mini won because it had the best composite score. Every routing decision is fully transparent."

4. **History** (30s): "Every request is logged. I can filter by provider, sort by cost or latency, and click into any request for the full routing decision."

5. **Analytics** (30s): "The analytics dashboard shows cost over time, latency percentiles, and provider usage breakdown."

6. **Wrap** (30s): "It's deployed on Vercel + Railway. GitHub Actions CI runs linting, type checking, and tests on every push."

---

## 10-Minute Technical Demo Script

Start with the 5-minute recruiter demo, then add:

1. **Routing algorithm** (2m): "Let me explain how routing works. It's not ML — it's a deterministic 4-dimension weighted score. I'll show you the `router_service.py`..." Walk through `select()` method, `_build_candidates()`, and scoring normalization.

2. **Caching** (1m): "Send the same message twice. The second response returns instantly — that's the Redis cache. Let me show the cache stats in Settings."

3. **Code architecture** (2m): Show the layered structure: `api/v1/chat.py` → `services/cache_service.py` → `services/router_service.py` → `providers/openai_provider.py`. "The API layer never contains business logic. Providers implement a common interface."

---

## 15-Minute System Design Demo Script

Start with the 10-minute demo, then add:

1. **Request lifecycle deep dive** (2m): Walk through the exact sequence in the `chat_stream` endpoint — rate limit check, cache check, routing, SSE streaming, cache write, async log.

2. **Database design** (1m): Show the `requests` table schema, explain why `routing_decision` is JSONB, explain the indexes.

3. **Scaling discussion** (2m): "For 10x traffic, I'd add more Railway instances — rate limiting and caching already work across instances via shared Redis. For 100x, I'd extract the hot path and add a write queue for logging."
