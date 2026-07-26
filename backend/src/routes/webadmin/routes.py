"""
Authentication routes for administrator login and password management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.service.authentication.admin_auth_service import AdminAuthService
from src.service.authentication.auth import get_current_admin
from src.service.database import create_engine

router = APIRouter(prefix="/auth", tags=["auth"])


def get_admin_auth_service() -> AdminAuthService:
    """FastAPI dependency that provides an AdminAuthService instance."""
    return AdminAuthService(create_engine())


class LoginRequest(BaseModel):
    """Payload for the login endpoint."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """Response schema containing the access token."""

    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    """Payload for the change-password endpoint."""

    new_password: str


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(payload: LoginRequest, service: AdminAuthService = Depends(get_admin_auth_service)):
    """Authenticate an administrator and return a JWT access token.

    Parameters
    ----------
    payload : LoginRequest
        The e-mail and password supplied by the administrator.
    service : AdminAuthService
        Injected authentication service.

    Returns
    -------
    TokenResponse
        A bearer JWT token valid for 24 hours.

    Raises
    ------
    HTTPException
        HTTP 401 if the credentials are invalid.
    """
    token = service.login(payload.email, payload.password)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
        )
    return TokenResponse(access_token=token)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    current_admin: dict = Depends(get_current_admin),
    service: AdminAuthService = Depends(get_admin_auth_service),
):
    """Change the password of the currently authenticated administrator.

    Parameters
    ----------
    payload : ChangePasswordRequest
        The new plain-text password.
    current_admin : dict
        The authenticated admin dict injected by ``get_current_admin``.
    service : AdminAuthService
        Injected authentication service.

    Raises
    ------
    HTTPException
        HTTP 404 if the administrator record is not found.
    """
    ok = service.change_password(int(current_admin["id"]), payload.new_password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin não encontrado.")
