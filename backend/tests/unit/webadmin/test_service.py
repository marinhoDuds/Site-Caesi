from unittest.mock import MagicMock, patch

from src.service.authentication.admin_auth_service import AdminAuthService


def test_ensure_default_admin_seeds_when_empty():
    engine = MagicMock()
    conn_mock = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn_mock
    engine.dialect.name = "mysql"
    conn_mock.execute.side_effect = [
        MagicMock(scalar=lambda: 0),
        MagicMock(),
        MagicMock(scalar=lambda: 1),
        MagicMock(),
    ]
    service = AdminAuthService(engine)
    with patch(
        "src.service.authentication.admin_auth_service.hash_password",
        return_value="hash",
    ):
        service._ensure_default_admin()
    assert conn_mock.commit.called


def test_login_returns_token_on_valid_credentials():
    engine = MagicMock()
    conn_mock = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn_mock
    service = AdminAuthService(engine)
    service.reset_failed_attempts("caesi@ccc.ufcg.edu.br")

    conn_mock.execute.side_effect = [
        MagicMock(scalar=lambda: 1),
        MagicMock(fetchone=lambda: (42, "$2b$12$fakehash")),
    ]

    with (
        patch(
            "src.service.authentication.admin_auth_service.verify_password",
            return_value=True,
        ),
        patch(
            "src.service.authentication.admin_auth_service.create_access_token",
            return_value="access.xyz",
        ),
        patch(
            "src.service.authentication.admin_auth_service.create_refresh_token",
            return_value="refresh.xyz",
        ),
    ):
        tokens = service.login("caesi@ccc.ufcg.edu.br", "caesi2025")

    assert tokens == ("access.xyz", "refresh.xyz")


def test_login_returns_none_on_wrong_password():
    engine = MagicMock()
    conn_mock = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn_mock
    service = AdminAuthService(engine)

    conn_mock.execute.side_effect = [
        MagicMock(scalar=lambda: 1),
        MagicMock(fetchone=lambda: (42, "$2b$12$fakehash")),
    ]

    with patch(
        "src.service.authentication.admin_auth_service.verify_password",
        return_value=False,
    ):
        token = service.login("caesi@ccc.ufcg.edu.br", "wrongpass")

    assert token is None


def test_login_returns_none_when_user_not_found():
    engine = MagicMock()
    conn_mock = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn_mock
    service = AdminAuthService(engine)

    conn_mock.execute.side_effect = [
        MagicMock(scalar=lambda: 1),
        MagicMock(fetchone=lambda: None),
    ]

    token = service.login("unknown@email.com", "anypass")
    assert token is None


def test_change_password_returns_true_when_updated():
    engine = MagicMock()
    conn_mock = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn_mock
    service = AdminAuthService(engine)

    conn_mock.execute.return_value.rowcount = 1

    with patch(
        "src.service.authentication.admin_auth_service.hash_password",
        return_value="$2b$hashed",
    ):
        result = service.change_password(1, "novasenha")

    assert result is True


def test_change_password_returns_false_when_not_found():
    engine = MagicMock()
    conn_mock = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn_mock
    service = AdminAuthService(engine)

    conn_mock.execute.return_value.rowcount = 0

    with patch(
        "src.service.authentication.admin_auth_service.hash_password",
        return_value="$2b$hashed",
    ):
        result = service.change_password(999, "novasenha")

    assert result is False
