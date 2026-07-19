import os

from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy import Engine

from src.service.authentication.auth import create_access_token
from src.service.authentication import repository
from src.service.crypto import generate_salt, hash_password, verify_password

INVALID_CREDENTIALS_MESSAGE = "Invalid credentials"


def authenticate_with_password(engine: Engine, email: str, password: str) -> dict:
    """Authenticate an administrator with email and password.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine.
    email : str
        Administrator's email.
    password : str
        Plain-text password provided by the administrator.

    Returns
    -------
    dict
        A dict with `access_token`, `token_type` and `must_change_password`,
        matching `TokenResponse`.

    Raises
    ------
    HTTPException
        401 if the email/password combination is invalid.
    """
    admin = repository.get_admin_by_email(engine, email)
    if not admin or not admin.get("password"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, INVALID_CREDENTIALS_MESSAGE)

    if not verify_password(password, admin["password"], admin["salt"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, INVALID_CREDENTIALS_MESSAGE)

    return _issue_token(admin)


def authenticate_with_google(engine: Engine, google_token: str) -> dict:
    """Authenticate an administrator using a Google ID token.

    Only accounts that already exist as administrators can log in this
    way; a matching Google account does not create a new administrator.
    On first successful login with Google, the account is linked by
    storing the Google "sub" claim for future logins.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine.
    google_token : str
        The ID token returned by Google Sign-In on the frontend.

    Returns
    -------
    dict
        A dict with `access_token`, `token_type` and `must_change_password`,
        matching `TokenResponse`.

    Raises
    ------
    HTTPException
        401 if the Google token is invalid or the email is not verified.
        403 if the Google account does not belong to a registered administrator.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise ValueError("GOOGLE_CLIENT_ID is not set. Configure it in your .env file.")

    try:
        payload = google_id_token.verify_oauth2_token(
            google_token, google_requests.Request(), client_id
        )
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Google token")

    email = payload.get("email")
    google_id = payload.get("sub")
    if not email or not payload.get("email_verified"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Google account is not verified")

    admin = repository.get_admin_by_google_id(engine, google_id)
    if not admin:
        admin = repository.get_admin_by_email(engine, email)
        if not admin:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "This Google account is not registered as an administrator",
            )
        repository.link_google_account(engine, admin["id"], google_id)
        admin["google_id"] = google_id

    return _issue_token(admin)


def change_password(
    engine: Engine, admin_id: int, current_password: str, new_password: str
) -> None:
    """Change an administrator's password.

    Also clears the `must_change_password` flag, so this same function
    handles both the mandatory first-login change and later voluntary
    password changes.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine.
    admin_id : int
        The administrator's ID.
    current_password : str
        The administrator's current password, required for confirmation.
    new_password : str
        The new password to set.

    Raises
    ------
    HTTPException
        404 if the administrator does not exist.
        401 if `current_password` does not match the stored password.
    """
    admin = repository.get_admin_by_id(engine, admin_id)
    if not admin:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Administrator not found")

    if admin.get("password") and not verify_password(
        current_password, admin["password"], admin["salt"]
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Current password is incorrect")

    salt = generate_salt()
    password_hash = hash_password(new_password, salt)
    repository.update_password(engine, admin_id, password_hash, salt)


def _issue_token(admin: dict) -> dict:
    """Build a `TokenResponse`-shaped dict for an authenticated administrator."""
    must_change = bool(admin.get("must_change_password"))
    token = create_access_token(
        {"sub": str(admin["id"]), "must_change_password": must_change}
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "must_change_password": must_change,
    }