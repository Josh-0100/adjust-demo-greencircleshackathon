import secrets
from typing import Annotated

from fastapi import Header, HTTPException, Request


def actor_role(request: Request, x_demo_role: Annotated[str | None, Header()] = None,
               authorization: Annotated[str | None, Header()] = None) -> str:
    settings = request.app.state.settings
    if settings.demo_mode:
        role = x_demo_role or "resident"
        if role not in {"resident", "staff", "admin"}:
            raise HTTPException(status_code=401, detail="Unknown demo role.")
        return role
    if not authorization:
        return "resident"
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="A bearer token is required.")
    if secrets.compare_digest(token, settings.admin_api_token):
        return "admin"
    if secrets.compare_digest(token, settings.staff_api_token):
        return "staff"
    raise HTTPException(status_code=401, detail="Invalid credentials.")


def require_role(required: str):
    from fastapi import Depends

    def dependency(role: str = Depends(actor_role)):
        allowed = {"admin"} if required == "admin" else {"staff", "admin"}
        if role not in allowed:
            raise HTTPException(status_code=403, detail=f"{required.capitalize()} access is required.")
        return role
    return dependency


staff_role = require_role("staff")
admin_role = require_role("admin")

