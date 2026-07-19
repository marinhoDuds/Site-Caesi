from unittest.mock import MagicMock, patch

from src.service.authentication import repository


def _fake_row(data: dict):
    """Build an object mimicking a SQLAlchemy Row, with a `_mapping` attribute."""
    row = MagicMock()
    row._mapping = data
    return row


class TestGetAdminByEmail:
    def test_found_returns_dict(self):
        engine = MagicMock()
        row = _fake_row({"id": 1, "email": "admin@caesi.com"})
        with patch(
            "src.service.authentication.repository.run_query", return_value=[row]
        ) as run_query:
            result = repository.get_admin_by_email(engine, "admin@caesi.com")

        run_query.assert_called_once()
        assert result == {"id": 1, "email": "admin@caesi.com"}

    def test_not_found_returns_none(self):
        engine = MagicMock()
        with patch("src.service.authentication.repository.run_query", return_value=[]):
            result = repository.get_admin_by_email(engine, "ghost@caesi.com")

        assert result is None


class TestGetAdminByGoogleId:
    def test_found_returns_dict(self):
        engine = MagicMock()
        row = _fake_row({"id": 1, "google_id": "google-sub-123"})
        with patch(
            "src.service.authentication.repository.run_query", return_value=[row]
        ):
            result = repository.get_admin_by_google_id(engine, "google-sub-123")

        assert result == {"id": 1, "google_id": "google-sub-123"}

    def test_not_found_returns_none(self):
        engine = MagicMock()
        with patch("src.service.authentication.repository.run_query", return_value=[]):
            result = repository.get_admin_by_google_id(engine, "unknown-sub")

        assert result is None


class TestGetAdminById:
    def test_found_returns_dict(self):
        engine = MagicMock()
        row = _fake_row({"id": 42, "email": "admin@caesi.com"})
        with patch(
            "src.service.authentication.repository.run_query", return_value=[row]
        ):
            result = repository.get_admin_by_id(engine, 42)

        assert result == {"id": 42, "email": "admin@caesi.com"}

    def test_not_found_returns_none(self):
        engine = MagicMock()
        with patch("src.service.authentication.repository.run_query", return_value=[]):
            result = repository.get_admin_by_id(engine, 999)

        assert result is None


class TestUpdatePassword:
    def test_calls_run_query_with_engine(self):
        engine = MagicMock()
        with patch("src.service.authentication.repository.run_query") as run_query:
            repository.update_password(engine, 1, "new-hash", "new-salt")

        run_query.assert_called_once()
        called_engine = run_query.call_args[0][0]
        assert called_engine is engine


class TestLinkGoogleAccount:
    def test_calls_run_query_with_engine(self):
        engine = MagicMock()
        with patch("src.service.authentication.repository.run_query") as run_query:
            repository.link_google_account(engine, 1, "google-sub-123")

        run_query.assert_called_once()
        called_engine = run_query.call_args[0][0]
        assert called_engine is engine
