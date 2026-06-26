"""User settings schemas."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from app.core.constants import ALL_STRATEGIES, STRATEGY_AUTO
from app.schemas.common import VeloraBaseModel

_VALID_STRATEGIES = Literal["auto", "cheapest", "fastest", "quality"]
_VALID_THEMES = Literal["dark", "light"]


class UserSettingsResponse(VeloraBaseModel):
    """Response for GET /settings."""

    default_routing_strategy: str
    default_model: str | None
    theme: str
    max_tokens: int
    temperature: float


class UpdateSettingsRequest(VeloraBaseModel):
    """Body for PATCH /settings — all fields optional."""

    default_routing_strategy: _VALID_STRATEGIES | None = None
    default_model: str | None = None
    theme: _VALID_THEMES | None = None
    max_tokens: Annotated[int, Field(ge=1, le=8192)] | None = None
    temperature: Annotated[float, Field(ge=0.0, le=2.0)] | None = None
