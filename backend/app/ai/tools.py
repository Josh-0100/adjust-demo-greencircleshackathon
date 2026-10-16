from dataclasses import dataclass
from typing import Callable

from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.ai.retrieval import RetrievalResult, retrieve
from app.core.settings import BOROUGHS
from app.schemas.api import StrictModel
from app.services.audit import audit


class ApprovedRetrievalInput(StrictModel):
    message: str = Field(min_length=8, max_length=3000)
    borough: str
    module_ids: list[str] = Field(min_length=1, max_length=12)
    limit: int = Field(default=3, ge=1, le=3)

    @field_validator("borough")
    @classmethod
    def valid_borough(cls, value):
        if value not in BOROUGHS:
            raise ValueError("Unknown borough.")
        return value

    @field_validator("module_ids")
    @classmethod
    def valid_modules(cls, value):
        from app.modules.registry import MODULES
        if any(item not in MODULES for item in value):
            raise ValueError("Unknown module resource mapping.")
        return value


@dataclass
class ToolSpec:
    name: str
    arguments: type[BaseModel]
    handler: Callable
    description: str


class ToolRegistry:
    """Typed allowlist for bounded read-only workflow tools.

    Core orchestration invokes tools explicitly. Future model tool suggestions
    must pass this same validation and permission boundary before execution.
    There are deliberately no approval, eligibility, arbitrary URL-fetch or write tools.
    """
    def __init__(self):
        self.tools: dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec):
        if tool.name in self.tools:
            raise ValueError("A tool cannot silently replace another tool.")
        self.tools[tool.name] = tool

    def invoke(self, name: str, arguments: dict, db: Session) -> RetrievalResult:
        if name not in self.tools:
            raise ValueError("Tool is not in the approved registry.")
        spec = self.tools[name]
        validated = spec.arguments.model_validate(arguments)
        result = spec.handler(validated, db)
        audit(db, "tool.invoked", "system", f"tool:{name}", f"Validated read-only retrieval completed with {len(result.resources)} approved sources.")
        return result


def retrieve_approved_resources(arguments: ApprovedRetrievalInput, db: Session):
    return retrieve(db, arguments.message, arguments.borough, arguments.module_ids, arguments.limit)


TOOLS = ToolRegistry()
TOOLS.register(ToolSpec("retrieve_approved_resources", ApprovedRetrievalInput, retrieve_approved_resources,
                        "Retrieve only administrator-approved bounded passages for a known borough and module."))

