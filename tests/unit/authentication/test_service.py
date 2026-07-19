from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.service.authentication import service
from src.service.crypto import generate_salt, hash_password


def _make_admin(**overrides) -> dict:
    salt = generate_salt()
    admin = {
        "id": 1,
        "name": "Admin",
        "email": "admin@caesi.com",
        "password": hash_password("correct-password", salt),
        "salt": salt,
        "google_id": None,
        "must_change_password": False,
    }
    admin.update(overrides)
    return admin


class TestAuthenticateWithPassword:
    def test_success_returns_token(self):
        engine = MagicMock()
        admin = _make_admin()
        with patch(
            "src.service.authentication.service.repository.get_admin_by_email",
            return_value=admin,
        ), patch(
            "src.service.authentication.service.create_access_token",
            return_value="fake-jwt",
        ):
            result = service.authenticate_with_password(
                engine, "admin@caesi.com", "correct-password"
            )

        assert result == {
            "access_token": "fake-jwt",
            "token_type": "bearer",
            "must_change_password": False,
        }

    def test_first_login_flags_must_change_password(self):
        engine = MagicMock()
        admin = _make_admin(must_change_password=True)
        with patch(
            "src.service.authentication.service.repository.get_admin_by_email",
            return_value=admin,
        ), patch(
            "src.service.authentication.service.create_access_token",
            return_value="fake-jwt",
        ):
            result = service.authenticate_with_password(
                engine, "admin@caesi.com", "correct-password"
            )

        assert result["must_change_password"] is True

    def test_wrong_password_raises_401(self):
        engine = MagicMock()
        admin = _make_admin()
        with patch(
            "src.service.authentication.service.repository.get_admin_by_email",
            return_value=admin,
        ):
            with pytest.raises(HTTPException) as exc_info:
                service.authenticate_with_password(engine, "admin@caesi.com", "wrong")

        assert exc_info.value.status_code == 401

    def test_unknown_email_raises_401(self):
        engine = MagicMock()
        with patch(
            "src.service.authentication.service.repository.get_admin_by_email",
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                service.authenticate_with_password(
                    engine, "ghost@caesi.com", "whatever"
                )

        assert exc_info.value.status_code == 401


class TestAuthenticateWithGoogle:
    def test_unregistered_google_account_raises_403(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
        engine = MagicMock()
        fake_payload = {
            "email": "outsider@gmail.com",
            "email_verified": True,
            "sub": "google-sub-123",
        }
        with patch(
            "src.service.authentication.service.google_id_token.verify_oauth2_token",
            return_value=fake_payload,
        ), patch(
            "src.service.authentication.service.repository.get_admin_by_google_id",
            return_value=None,
        ), patch(
            "src.service.authentication.service.repository.get_admin_by_email",
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                service.authenticate_with_google(engine, "fake-google-token")

        assert exc_info.value.status_code == 403

    def test_known_admin_links_google_account(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
        engine = MagicMock()
        admin = _make_admin(google_id=None)
        fake_payload = {
            "email": admin["email"],
            "email_verified": True,
            "sub": "google-sub-123",
        }
        with patch(
            "src.service.authentication.service.google_id_token.verify_oauth2_token",
            return_value=fake_payload,
        ), patch(
            "src.service.authentication.service.repository.get_admin_by_google_id",
            return_value=None,
        ), patch(
            "src.service.authentication.service.repository.get_admin_by_email",
            return_value=admin,
        ) as get_by_email, patch(
            "src.service.authentication.service.repository.link_google_account"
        ) as link_google, patch(
            "src.service.authentication.service.create_access_token",
            return_value="fake-jwt",
        ):
            result = service.authenticate_with_google(engine, "fake-google-token")

        get_by_email.assert_called_once()
        link_google.assert_called_once_with(engine, admin["id"], "google-sub-123")
        assert result["access_token"] == "fake-jwt"


class TestAuthenticateWithGoogleEdgeCases:
    def test_missing_client_id_raises_value_error(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
        engine = MagicMock()

        with pytest.raises(ValueError):
            service.authenticate_with_google(engine, "fake-google-token")

    def test_invalid_google_token_raises_401(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
        engine = MagicMock()

        with patch(
            "src.service.authentication.service.google_id_token.verify_oauth2_token",
            side_effect=ValueError("bad token"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                service.authenticate_with_google(engine, "fake-google-token")

        assert exc_info.value.status_code == 401

    def test_unverified_email_raises_401(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
        engine = MagicMock()
        fake_payload = {
            "email": "someone@gmail.com",
            "email_verified": False,
            "sub": "google-sub-123",
        }

        with patch(
            "src.service.authentication.service.google_id_token.verify_oauth2_token",
            return_value=fake_payload,
        ):
            with pytest.raises(HTTPException) as exc_info:
                service.authenticate_with_google(engine, "fake-google-token")

        assert exc_info.value.status_code == 401


class TestChangePassword:
    def test_unknown_admin_raises_404(self):
        engine = MagicMock()
        with patch(
            "src.service.authentication.service.repository.get_admin_by_id",
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                service.change_password(engine, 999, "whatever", "new-password1")

        assert exc_info.value.status_code == 404

    def test_wrong_current_password_raises_401(self):
        engine = MagicMock()
        admin = _make_admin()
        with patch(
            "src.service.authentication.service.repository.get_admin_by_id",
            return_value=admin,
        ):
            with pytest.raises(HTTPException) as exc_info:
                service.change_password(engine, admin["id"], "wrong", "new-password1")

        assert exc_info.value.status_code == 401

    def test_success_updates_password_and_clears_flag(self):
        engine = MagicMock()
        admin = _make_admin(must_change_password=True)
        with patch(
            "src.service.authentication.service.repository.get_admin_by_id",
            return_value=admin,
        ), patch(
            "src.service.authentication.service.repository.update_password"
        ) as update_password:
            service.change_password(
                engine, admin["id"], "correct-password", "new-password1"
            )

        update_password.assert_called_once()
        called_engine, called_id, _hash, _salt = update_password.call_args[0]
        assert called_engine is engine
        assert called_id == admin["id"]