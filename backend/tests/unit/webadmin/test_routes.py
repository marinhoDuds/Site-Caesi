from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from src.routes.webadmin.routes import router, get_admin_auth_service
from src.service.authentication.auth import get_current_admin

app = FastAPI()
app.include_router(router)

mock_service = MagicMock()


def override_service():
    return mock_service


def override_admin():
    return {"id": "1"}


app.dependency_overrides[get_admin_auth_service] = override_service
app.dependency_overrides[get_current_admin] = override_admin

client = TestClient(app)


def test_login_success():
    mock_service.check_lockout.return_value = False
    mock_service.login.return_value = ("jwt.access.here", "jwt.refresh.here")

    resp = client.post(
        "/auth/login", json={"email": "caesi@ccc.ufcg.edu.br", "password": "caesi2025"}
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"] == "jwt.access.here"
    assert body["refresh_token"] == "jwt.refresh.here"
    assert body["token_type"] == "bearer"


def test_login_invalid_credentials():
    mock_service.check_lockout.return_value = False
    mock_service.login.return_value = None

    resp = client.post(
        "/auth/login", json={"email": "wrong@email.com", "password": "wrongpass"}
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Credenciais inválidas."


def test_login_locked_out():
    mock_service.check_lockout.return_value = True

    resp = client.post(
        "/auth/login", json={"email": "locked@email.com", "password": "pass"}
    )

    assert resp.status_code == 429
    assert "bloqueada" in resp.json()["detail"]


def test_refresh_token_success():
    from src.service.authentication.auth import create_refresh_token

    token = create_refresh_token({"sub": "1"})

    resp = client.post("/auth/refresh", json={"refresh_token": token})

    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert "refresh_token" in resp.json()


def test_change_password_success():
    mock_service.change_password.return_value = True

    resp = client.post("/auth/change-password", json={"new_password": "novaSenha123"})

    assert resp.status_code == 204
    mock_service.change_password.assert_called_once_with(1, "novaSenha123")


def test_change_password_admin_not_found():
    mock_service.change_password.return_value = False

    resp = client.post("/auth/change-password", json={"new_password": "qualquerSenha"})

    assert resp.status_code == 404
