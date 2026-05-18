"""Admin mode — password verification endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.config import get_admin_password

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class VerifyRequest(BaseModel):
    password: str


@router.post("/verify")
async def verify(request: VerifyRequest):
    valid = request.password == get_admin_password()
    return {"valid": valid}
