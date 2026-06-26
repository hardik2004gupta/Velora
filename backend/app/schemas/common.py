"""Shared schema primitives used across multiple endpoints."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class VeloraBaseModel(BaseModel):
    """
    Base class for all Velora schemas.

    - ``from_attributes=True`` so models can be constructed from ORM instances.
    - ``populate_by_name=True`` to allow both alias and field name on input.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
