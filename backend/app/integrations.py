"""Composition adapters for the existing, independently runnable modules.

Dispatch uses each application's original full URL. A Starlette path mount
would strip their already namespaced API prefixes and bypassing the apps in
favour of their routers would discard middleware and current Adjust routes.
"""
from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
import sqlite3
import sys

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.engine import make_url

from app.core.settings import PROJECT_ROOT, Settings


# Packages have distinct names, and all paths derive from the repository rather
# than the current working directory or the caller's shell configuration.
for module in ("bolton-connect", "adjust"):
    backend = str(PROJECT_ROOT / "modules" / module / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)

from adjust_api.main import create_app as create_adjust_app  # noqa: E402
from bolton_api.app import create_app as create_bolton_app  # noqa: E402
from bolton_api.settings import (  # noqa: E402
    Settings as BoltonSettings,
    get_settings as get_bolton_settings,
    scoped_settings,
)


class BoltonPrivacyGuard:
    """Bound actual request bodies and prevent caching private module responses.

    The module's own middleware still owns its rate limit. This adds no second
    counter and also handles bodies sent without Content-Length.
    """

    def __init__(self, app, max_bytes: int):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def private_send(message):
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).extend([
                    (b"cache-control", b"no-store"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"x-content-type-options", b"nosniff"),
                ])
            await send(message)

        messages, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.max_bytes:
                return await JSONResponse({"detail": "Request body too large."}, 413)(scope, receive, private_send)
            messages.append(message)
            if not message.get("more_body", False):
                break

        async def replay():
            return messages.pop(0) if messages else await receive()

        await self.app(scope, replay, private_send)


def _check_separate_store(host: Settings, bolton: BoltonSettings) -> None:
    host_url = make_url(host.database_url)
    if host_url.get_backend_name() != "sqlite" or not host_url.database or host_url.database == ":memory:":
        return
    host_path, module_path = Path(host_url.database).resolve(), bolton.database_path.resolve()
    same_file = host_path.exists() and module_path.exists() and host_path.samefile(module_path)
    if host_path == module_path or same_file:
        raise ValueError("Resident Support and the host must use separate database files.")


@dataclass
class IntegratedModules:
    bolton: FastAPI
    adjust: FastAPI
    bolton_settings: BoltonSettings

    @asynccontextmanager
    async def lifespan(self):
        # Sub-applications reached by dispatch do not receive ASGI lifespan
        # messages automatically, so enter their real contexts explicitly.
        with scoped_settings(self.bolton_settings):
            async with AsyncExitStack() as stack:
                await stack.enter_async_context(self.bolton.router.lifespan_context(self.bolton))
                await stack.enter_async_context(self.adjust.router.lifespan_context(self.adjust))
                yield


def create_integrated_modules(host: Settings, bolton_settings: dict | BoltonSettings | None = None) -> IntegratedModules:
    overrides = bolton_settings.model_dump() if isinstance(bolton_settings, BoltonSettings) else (bolton_settings or {})
    # Host identity is authoritative in integrated mode. Caller overrides may
    # select an isolated store, provider or limits, but cannot re-enable demo
    # access or supply separate staff credentials under a non-demo host.
    settings = BoltonSettings(**(get_bolton_settings().model_dump() | overrides | {
        "demo_mode": host.demo_mode,
        "adviser_api_token": host.staff_api_token,
        "admin_api_token": host.admin_api_token,
    }))
    _check_separate_store(host, settings)
    with scoped_settings(settings):
        bolton = create_bolton_app()
    bolton.state.settings = settings
    bolton.add_middleware(BoltonPrivacyGuard, max_bytes=settings.request_max_body_bytes)

    @bolton.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        # The standalone default includes supplied input. Integrated errors use
        # the same redacted shape as the host and Adjust.
        return JSONResponse(status_code=422, content={"detail": [
            {"loc": list(item["loc"]), "msg": item["msg"], "type": item["type"]}
            for item in error.errors()
        ]})

    @bolton.exception_handler(sqlite3.Error)
    async def store_error(request: Request, error: sqlite3.Error):
        return JSONResponse(status_code=503, content={"detail": "The resident support store is temporarily unavailable."})

    @bolton.exception_handler(Exception)
    async def module_error(request: Request, error: Exception):
        return JSONResponse(status_code=503, content={"detail": "Resident support could not complete this request. Please retry."},
                            headers={"Cache-Control": "no-store"})

    return IntegratedModules(bolton=bolton, adjust=create_adjust_app(), bolton_settings=settings)


class ModuleDispatcher:
    def __init__(self, app, modules: IntegratedModules):
        self.app, self.modules = app, modules

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            root_path = scope.get("root_path", "")
            if root_path and (path == root_path or path.startswith(root_path + "/")):
                path = path[len(root_path):]

            async def private_send(message):
                if message["type"] == "http.response.start":
                    headers = message.setdefault("headers", [])
                    existing = {key.lower() for key, _ in headers}
                    for key, value in ((b"cache-control", b"no-store"), (b"referrer-policy", b"no-referrer"),
                                       (b"x-content-type-options", b"nosniff")):
                        if key not in existing:
                            headers.append((key, value))
                await send(message)

            if path == "/api/bolton-connect" or path.startswith("/api/bolton-connect/"):
                with scoped_settings(self.modules.bolton_settings):
                    return await self.modules.bolton(scope, receive, private_send)
            if path == "/api/adjust" or path.startswith("/api/adjust/"):
                return await self.modules.adjust(scope, receive, private_send)
        return await self.app(scope, receive, send)


def install_integrations(application: FastAPI, modules: IntegratedModules) -> None:
    application.state.integration_modules = modules
    # Added after the host guard: dispatch is outside that guard, so the module
    # retains its own limits without spending the host's per-client budget.
    application.add_middleware(ModuleDispatcher, modules=modules)
    application.mount("/module-assets/bolton-connect", StaticFiles(
        directory=str(modules.bolton_settings.frontend_dir), html=True,
    ), name="bolton-connect-assets")
