import pytest
from pydantic import ValidationError

from src.service.authentication.models import (
    AdminOut,
    ChangePasswordRequest,
    GoogleLoginRequest,
    LoginRequest,
    TokenResponse,
)


class TestLoginRequest:
    def test_valid_payload(self):
        request = LoginRequest(email="admin@caesi.com", password="secret")
        assert request.email == "admin@caesi.com"
        assert request.password == "secret"

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="not-an-email", password="secret")


class TestGoogleLoginRequest:
    def test_valid_payload(self):
        request = GoogleLoginRequest(id_token="fake-google-token")
        assert request.id_token == "fake-google-token"


class TestChangePasswordRequest:
    def test_valid_payload(self):
        request = ChangePasswordRequest(
            current_password="old-password", new_password="new-password1"
        )
        assert request.new_password == "new-password1"

    def test_short_new_password_raises(self):
        with pytest.raises(ValidationError):
            ChangePasswordRequest(current_password="old-password", new_password="short")


class TestTokenResponse:
    def test_defaults_token_type_to_bearer(self):
        response = TokenResponse(access_token="fake-jwt", must_change_password=False)
        assert response.token_type == "bearer"


class TestAdminOut:
    def test_valid_payload(self):
        admin = AdminOut(id=1, name="Admin", email="admin@caesi.com")
        assert admin.id == 1
