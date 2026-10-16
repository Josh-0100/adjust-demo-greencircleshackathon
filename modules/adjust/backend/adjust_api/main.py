import os
from datetime import date

from fastapi import APIRouter, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .engine import analyse, make_plan
from .knowledge import KnowledgeLibrary
from .models import AnalyseRequest, AnalyseResponse, Plan, PlanRequest
from .referrals import referrals

router = APIRouter(prefix="/adjust", tags=["ADJUST"])


@router.get("/health")
def health():
    library = KnowledgeLibrary()
    return {"status": "ok", "module": "adjust", "provider": "local-rules", "data_persisted": False,
            "ai_configured": bool(os.environ.get("ADJUST_AI_BASE_URL") and os.environ.get("ADJUST_AI_MODEL")),
            "knowledge_entries": len(library.validated()), "professional_review": "pending"}


@router.post("/analyse", response_model=AnalyseResponse)
def analyse_route(request: AnalyseRequest):
    return analyse(request)


@router.get("/knowledge")
def knowledge(q: str = Query(default="", max_length=120)):
    entries = KnowledgeLibrary().validated()
    if q:
        entries = [e for e in entries if q.casefold() in f"{e.topic} {e.summary} {e.publisher}".casefold()]
    return {"entries": entries, "editorial_review_only": True, "professional_review": "pending"}


@router.get("/support")
def support():
    return {"referrals": referrals(date.today())}


@router.post("/plan", response_model=Plan)
def plan_route(request: PlanRequest):
    return make_plan(request)


@router.get("/scenarios")
def scenarios():
    return {"scenarios": [
        {"id": "warehouse", "label": "Lifting and back pain", "role": "Warehouse picker", "description": "One of our warehouse pickers reports back pain and struggles with repeated lifting and picking. We want to understand which changes to the work might help.", "constraints": "Small team; limited space for new equipment.", "expected": "Source-supported handling options"},
        {"id": "office", "label": "Anxiety and office work", "role": "Office administrator", "description": "An office employee reports anxiety and struggles with computer work, competing deadlines and spontaneous phone calls in a noisy office. They would like clearer priorities.", "constraints": "No dedicated HR team; customer cover is needed.", "expected": "Workload, environment and communication options"},
        {"id": "multiple", "label": "Several barriers at work", "role": "Retail worker", "description": "A retail worker reports fatigue when standing for long periods, difficulty concentrating on written instructions and stress during busy customer calls. They would like to discuss changes.", "constraints": "Small shop with limited floor space.", "expected": "Options spanning several workplace barriers"},
        {"id": "vague", "label": "Not sure where to start", "role": "", "description": "An employee is finding work difficult and we are not sure how to help.", "constraints": "", "expected": "Clarification before recommendations"},
        {"id": "evidence-gap", "label": "Specialist evidence needed", "role": "Underwater technician", "description": "An underwater technician reports difficulty with pressure equalisation during saturation diving. We need specialist guidance about the diving task.", "constraints": "Specialist offshore equipment.", "expected": "No unsupported task-specific recommendations"},
    ]}


class PrivacyHeaders:
    """Bound bodies even when Content-Length is absent; keep payloads out of errors."""
    def __init__(self, app, max_bytes=16000):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        total = 0
        messages = []
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            total += len(message.get("body", b""))
            if total > self.max_bytes:
                response = JSONResponse({"detail": "This request is too large. Keep the situation concise."}, 413)
                return await response(scope, receive, send)
            messages.append(message)
            if not message.get("more_body", False):
                break
        async def replay():
            return messages.pop(0) if messages else await receive()
        async def protected_send(message):
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).extend([(b"cache-control", b"no-store"),
                    (b"referrer-policy", b"no-referrer"), (b"x-content-type-options", b"nosniff")])
            await send(message)
        await self.app(scope, replay, protected_send)


def create_app():
    app = FastAPI(title="ADJUST · Workplace adjustments", version="0.1.0",
                  description="Independent, stateless local prototype. General guidance with human review; no production authentication.")
    app.include_router(router, prefix="/api")
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3001", "http://127.0.0.1:3001"],
                       allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
    app.add_middleware(PrivacyHeaders)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": [
            {"loc": list(item["loc"]), "msg": item["msg"], "type": item["type"]}
            for item in error.errors()]})

    @app.exception_handler(Exception)
    async def internal_error(request: Request, error: Exception):
        return JSONResponse(status_code=503, content={"detail": "ADJUST could not complete this request. Please retry. No plan has been saved."}, headers={"Cache-Control": "no-store"})

    return app


app = create_app()
