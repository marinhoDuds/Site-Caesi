from fastapi import APIRouter, Depends, status
from sqlalchemy import Engine

from src.service.auth import get_current_admin
from src.service.authentication import service
from src.service.authentication.models import (
    ChangePasswordRequest,
    GoogleLoginRequest,
    LoginRequest,
    TokenResponse,
)
from src.service.database import create_engine

router = APIRouter(prefix="/webadmin/auth", tags=["webadmin-authentication"])


def get_db_engine() -> Engine:
    """Provide a database engine for request handlers."""
    return create_engine()


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest, engine: Engine = Depends(get_db_engine)
) -> TokenResponse:
    """Authenticate an administrator with email and password."""
    return service.authenticate_with_password(engine, payload.email, payload.password)


@router.post("/login/google", response_model=TokenResponse)
def login_with_google(
    payload: GoogleLoginRequest, engine: Engine = Depends(get_db_engine)
) -> TokenResponse:
    """Authenticate an administrator using a Google ID token."""
    return service.authenticate_with_google(engine, payload.id_token)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    admin: dict = Depends(get_current_admin),
    engine: Engine = Depends(get_db_engine),
) -> None:
    """Change the authenticated administrator's password.

    Uses `get_current_admin` (not `get_active_admin`) on purpose, so an
    administrator with a pending mandatory password change can still
    reach this endpoint to set a new one.
    """
    service.change_password(
        engine, int(admin["id"]), payload.current_password, payload.new_password
    )