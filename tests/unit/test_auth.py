import pytest
import jwt
from datetime import timedelta
from fastapi import HTTPException

from src.service.authentication.auth import (
    create_access_token,
    verify_token,
    get_current_admin,
    SECRET_KEY,
    ALGORITHM,
)


def test_create_access_token():
    data = {"sub": "123"}
    token = create_access_token(data)
    assert isinstance(token, str)
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "123"
    assert "exp" in decoded


def test_create_access_token_with_delta():
    data = {"sub": "123"}
    delta = timedelta(minutes=5)
    token = create_access_token(data, expires_delta=delta)
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "123"


def test_verify_token_valid():
    token = create_access_token({"sub": "admin1"})
    payload = verify_token(token)
    assert payload["sub"] == "admin1"


def test_verify_token_expired():
    token = create_access_token({"sub": "admin1"}, expires_delta=timedelta(seconds=-1))
    with pytest.raises(HTTPException) as exc:
        verify_token(token)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Token has expired"


def test_verify_token_invalid():
    with pytest.raises(HTTPException) as exc:
        verify_token("invalid.token.here")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Could not validate credentials"


def test_get_current_admin_valid():
    token = create_access_token({"sub": "admin1"})
    admin = get_current_admin(token)
    assert admin["id"] == "admin1"


def test_get_current_admin_missing_sub():
    token = create_access_token({"other": "value"})
    with pytest.raises(HTTPException) as exc:
        get_current_admin(token)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Could not validate credentials"
