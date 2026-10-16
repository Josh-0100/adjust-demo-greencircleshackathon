"""Module-local role resolution.

In demo mode an ``X-Demo-Role`` header selects the actor role so the dashboard
can be shown without real accounts. Outside demo mode, staff and admin endpoints
require a bearer token matching the configured adviser/admin tokens. This is
demonstration authentication, not production identity.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from .settings import Settings, get_settings

ROLE_RANK = {"resident": 0, "staff": 1, "admin": 2}
_VALID_ROLES = set(ROLE_RANK)


def actor_role(request: Request, settings: Settings) -> str:
    if settings.demo_mode:
        role = request.headers.get("x-demo-role", "resident").strip().lower()
        return role if role in _VALID_ROLES else "resident"

    auth = request.headers.get("authorization", "")
    token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    if token and settings.admin_api_token and token == settings.admin_api_token:
        return "admin"
    if token and settings.adviser_api_token and token == settings.adviser_api_token:
        return "staff"
    return "resident"


def _current_role(request: Request) -> str:
    return actor_role(request, get_settings())


def require_role(minimum: str):
    """Dependency factory enforcing a minimum role rank."""
    floor = ROLE_RANK[minimum]

    def _dependency(role: str = Depends(_current_role)) -> str:
        if ROLE_RANK.get(role, 0) < floor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires the '{minimum}' role.",
            )
        return role

    return _dependency


require_staff = require_role("staff")
require_admin = require_role("admin")
