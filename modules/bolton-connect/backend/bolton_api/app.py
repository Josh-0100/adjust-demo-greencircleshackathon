"""Standalone FastAPI application for Bolton Connect.

Run directly (``scripts/run.sh`` / ``uvicorn bolton_api.app:app``) for a
self-contained demo that needs no other part of the repo. The same
``router`` can alternatively be mounted into the host CivicForge app — see
``plugin.py`` — but this module never imports or depends on the Adjust module.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .routes import router
from .settings import get_settings

# Simple in-memory sliding-window rate limiter keyed by client host. Adequate
# for a single-process demo; a real deployment would use a shared store.
_HITS: dict[str, deque[float]] = defaultdict(deque)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Adjust AI resident support",
        version="0.1.0",
        description="AI-assisted employment and community support for Bolton residents.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.demo_mode else [],
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def _guard(request: Request, call_next):
        # Body-size guard (reject oversized payloads early).
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > settings.request_max_body_bytes:
            return JSONResponse(status_code=413, content={"detail": "Request body too large."})

        # Per-client rate limit.
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = _HITS[client]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= settings.request_limit_per_minute:
            return JSONResponse(status_code=429, content={"detail": "Too many requests — please slow down."})
        window.append(now)

        return await call_next(request)

    app.include_router(router)

    @app.on_event("startup")
    def _seed() -> None:
        # Populate synthetic demonstration cases on first run (no-op if present).
        from .demo import seed_demo_cases

        seed_demo_cases(settings)

    # Serve the build-free resident/adviser frontend if present.
    if settings.frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(settings.frontend_dir), html=True), name="frontend")

    return app


app = create_app()
