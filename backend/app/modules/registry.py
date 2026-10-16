from app.modules.base import CivicModule
from app.modules.community import Community
from app.modules.custom import CustomChallenge
from app.modules.employment import Employment
from app.modules.learning import Learning
from app.modules.service_navigator import ServiceNavigator
from app.modules.triage import Triage

MODULES: dict[str, CivicModule] = {module.id: module for module in [ServiceNavigator(), Employment(), Community(), Triage(), Learning(), CustomChallenge()]}


def get_module(module_id: str) -> CivicModule:
    return MODULES[module_id]


def register_module(module: CivicModule):
    """Register during application construction; never overwrite a live module silently."""
    if module.id in MODULES:
        raise ValueError(f"Module already registered: {module.id}")
    MODULES[module.id] = module
