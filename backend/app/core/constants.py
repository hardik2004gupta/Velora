"""
Application-wide constants.

This module contains:
- Provider and model identifiers
- Routing strategy names
- Cost table (USD per 1K tokens)
- Quality scores (static, updated periodically from public benchmarks)
- Redis key prefixes and TTL values
- Request status values
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Provider identifiers
# ---------------------------------------------------------------------------

PROVIDER_OPENAI = "openai"
PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_GEMINI = "gemini"

ALL_PROVIDERS = {PROVIDER_OPENAI, PROVIDER_ANTHROPIC, PROVIDER_GEMINI}

# ---------------------------------------------------------------------------
# Routing strategies
# ---------------------------------------------------------------------------

STRATEGY_AUTO = "auto"
STRATEGY_CHEAPEST = "cheapest"
STRATEGY_FASTEST = "fastest"
STRATEGY_QUALITY = "quality"

ALL_STRATEGIES = {STRATEGY_AUTO, STRATEGY_CHEAPEST, STRATEGY_FASTEST, STRATEGY_QUALITY}

# ---------------------------------------------------------------------------
# Provider health statuses
# ---------------------------------------------------------------------------

STATUS_HEALTHY = "healthy"
STATUS_DEGRADED = "degraded"
STATUS_DOWN = "down"

HEALTHY_STATUSES = {STATUS_HEALTHY, STATUS_DEGRADED}

# ---------------------------------------------------------------------------
# Request statuses
# ---------------------------------------------------------------------------

REQUEST_STATUS_SUCCESS = "success"
REQUEST_STATUS_ERROR = "error"
REQUEST_STATUS_TIMEOUT = "timeout"

# ---------------------------------------------------------------------------
# Cost table — USD per 1K tokens (input / output)
# Last updated: 2025-Q4
# ---------------------------------------------------------------------------

COST_TABLE: dict[str, dict[str, dict[str, float]]] = {
    PROVIDER_OPENAI: {
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    },
    PROVIDER_ANTHROPIC: {
        "claude-sonnet-4-6": {"input": 0.003, "output": 0.015},
        "claude-haiku-4-5-20251001": {"input": 0.0008, "output": 0.004},
    },
    PROVIDER_GEMINI: {
        "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
        "gemini-2.0-pro": {"input": 0.0035, "output": 0.0105},
    },
}

# ---------------------------------------------------------------------------
# Quality scores — 0.0 to 1.0 (higher is better)
# Based on publicly available benchmark aggregates (MMLU, HumanEval, etc.)
# ---------------------------------------------------------------------------

QUALITY_SCORES: dict[str, float] = {
    # OpenAI
    "gpt-4o": 0.95,
    "gpt-4o-mini": 0.78,
    # Anthropic
    "claude-sonnet-4-6": 0.89,
    "claude-haiku-4-5-20251001": 0.75,
    # Gemini
    "gemini-2.0-pro": 0.91,
    "gemini-2.0-flash": 0.73,
}

# ---------------------------------------------------------------------------
# Static latency estimates (ms) — Time To First Token approximations
# Replaced by Redis rolling average in Phase 4.
# ---------------------------------------------------------------------------

STATIC_LATENCY_MS: dict[str, int] = {
    "gpt-4o": 1200,
    "gpt-4o-mini": 820,
    "claude-sonnet-4-6": 1400,
    "claude-haiku-4-5-20251001": 950,
    "gemini-2.0-pro": 1800,
    "gemini-2.0-flash": 650,
}

# ---------------------------------------------------------------------------
# Auto-routing weights
# Must sum to 1.0
# ---------------------------------------------------------------------------

AUTO_WEIGHT_QUALITY = 0.35
AUTO_WEIGHT_COST = 0.30
AUTO_WEIGHT_LATENCY = 0.25
AUTO_WEIGHT_HEALTH = 0.10

# ---------------------------------------------------------------------------
# Redis key patterns and TTL values
# ---------------------------------------------------------------------------

REDIS_PREFIX_CACHE = "cache"
REDIS_PREFIX_RATE_LIMIT = "rate"
REDIS_PREFIX_LATENCY = "latency"
REDIS_PREFIX_HEALTH = "health"

REDIS_TTL_CACHE = 3600          # 1 hour — prompt response cache
REDIS_TTL_RATE_LIMIT = 60       # 1 minute — fixed window counter
REDIS_TTL_HEALTH_OVERRIDE = 120 # 2 minutes — manual health override
REDIS_LATENCY_WINDOW = 100      # keep last N latency measurements per provider

# Degraded-provider suppression after a failed call
REDIS_TTL_PROVIDER_DEGRADED = 60  # 60 seconds

# ---------------------------------------------------------------------------
# API Key format
# ---------------------------------------------------------------------------

API_KEY_PREFIX = "vk-"
API_KEY_LENGTH = 32  # bytes from secrets.token_urlsafe

# ---------------------------------------------------------------------------
# Pagination defaults
# ---------------------------------------------------------------------------

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ---------------------------------------------------------------------------
# Health check endpoint paths
# ---------------------------------------------------------------------------

HEALTH_PATH = "/health"
READINESS_PATH = "/health/ready"
LIVENESS_PATH = "/health/live"
VERSION_PATH = "/version"
