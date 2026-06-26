"""Pagination helpers for list endpoints."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from app.core.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters shared by all paginated list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    limit: int = Field(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Items per page",
    )

    @property
    def offset(self) -> int:
        """Return the SQL OFFSET value for the current page."""
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard envelope for paginated list responses."""

    items: list[T]
    total: int
    page: int
    limit: int

    @property
    def total_pages(self) -> int:
        """Total number of pages given the current limit."""
        if self.limit == 0:
            return 0
        return (self.total + self.limit - 1) // self.limit

    @property
    def has_next(self) -> bool:
        """True if there is a next page."""
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """True if there is a previous page."""
        return self.page > 1
