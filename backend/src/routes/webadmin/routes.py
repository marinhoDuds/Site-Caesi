from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.service.authentication.admin_auth_service import AdminAuthService
from src.service.authentication.auth import (
    create_access_token,
    create_refresh_token,
    get_current_admin,
    verify_refresh_token,
)
from src.service.database import create_engine

router = APIRouter(prefix="/auth", tags=["auth"])


def get_admin_auth_service() -> AdminAuthService:
    """FastAPI dependency that provides an AdminAuthService instance."""
    return AdminAuthService(create_engine())


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    new_password: str


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(payload: LoginRequest, service: AdminAuthService = Depends(get_admin_auth_service)):
    """Authenticate an administrator and return access + refresh tokens."""
    clean_email = payload.email.strip().lower()
    if service.check_lockout(clean_email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login falhas. Conta temporariamente bloqueada.",
        )

    tokens = service.login(clean_email, payload.password)
    if tokens is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
        )

    access_token, refresh_token = tokens
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def refresh_token_route(payload: RefreshRequest):
    """Generate a new access token using a valid refresh token."""
    decoded = verify_refresh_token(payload.refresh_token)
    admin_id = decoded.get("sub")
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
        )
    new_access = create_access_token({"sub": admin_id})
    new_refresh = create_refresh_token({"sub": admin_id})
    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    current_admin: dict = Depends(get_current_admin),
    service: AdminAuthService = Depends(get_admin_auth_service),
):
    """Change the password of the currently authenticated administrator."""
    ok = service.change_password(int(current_admin["id"]), payload.new_password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin não encontrado.")
