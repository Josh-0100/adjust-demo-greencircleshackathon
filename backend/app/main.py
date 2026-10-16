from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import router
from app.core.middleware import RequestGuard
from app.core.settings import Settings, get_settings
from app.database.bootstrap import bootstrap
from app.database.session import session_factory
from app.integrations import create_integrated_modules, install_integrations
from app.modules.registry import MODULES


def create_app(settings: Settings | None = None, *, bolton_settings: dict | None = None) -> FastAPI:
    settings = settings or get_settings()
    integrated_modules = create_integrated_modules(settings, bolton_settings)

    @asynccontextmanager
    async def lifespan(application):
        engine = bootstrap(settings)
        application.state.engine = engine
        application.state.session_factory = session_factory(engine)
        try:
            async with integrated_modules.lifespan():
                yield
        finally:
            engine.dispose()

    application = FastAPI(title="Adjust AI", version="0.1.0", lifespan=lifespan,
                          description="Grounded civic workflows with explicit synthetic demo mode and human review. Prototype role boundaries require hardening before a council pilot.")
    application.state.settings = settings
    application.add_middleware(RequestGuard, limit=settings.request_limit_per_minute, body_limit=settings.request_max_body_bytes)
    install_integrations(application, integrated_modules)
    application.add_middleware(CORSMiddleware, allow_origins=[value.strip() for value in settings.cors_origins.split(",") if value.strip()],
                               allow_credentials=False, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                               allow_headers=["Content-Type", "Authorization", "X-Demo-Role"])
    application.include_router(router, prefix="/api")
    for module in MODULES.values():
        if module.router is not None:
            application.include_router(module.router, prefix="/api")

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        # Error payloads omit resident text and supplied credentials.
        detail = [{"loc": list(item["loc"]), "msg": item["msg"], "type": item["type"]} for item in error.errors()]
        return JSONResponse(status_code=422, content={"detail": detail})

    @application.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, error: SQLAlchemyError):
        return JSONResponse(status_code=503, content={"detail": "The data store is temporarily unavailable. Please retry or contact the prototype administrator."})

    return application


app = create_app()
