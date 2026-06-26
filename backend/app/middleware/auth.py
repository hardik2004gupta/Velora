"""
Authentication middleware — placeholder.

In V1, authentication is handled per-route using FastAPI's Depends() system
(see ``app/dependencies/auth.py``).  This file is a placeholder for future
global authentication middleware (e.g., for WebSocket support or global API
key validation before routing).
"""

from __future__ import annotations

# TODO(phase-2): Implement global auth middleware if WebSocket support is added.
# For now, per-route Depends(get_current_user) in api/v1/ handles all auth.
