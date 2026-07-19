from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.routes.home import admin_routes, caesi_routes, chapa_routes
from src.routes.home.dependencies import get_admin_service, get_caesi_service
from src.service.authentication.auth import get_current_admin
from src.service.home_management.models import Admin


def fake_admin(**overrides) -> Admin:
    """Build an Admin with sensible test defaults, overridable per test."""
    defaults = dict(
        id=1,
        nome="Fulano",
        email="fulano@example.com",
        senha_hash="hash-nao-deve-vazar",
        salt="salt-nao-deve-vazar",
        foto_url="http://s3.local/admins/1.jpg",
        descricao="desc",
        periodo="2026.1",
        chapa_id=1,
        linkedin_url="",
        git_url="",
        lattes_url="",
    )
    defaults.update(overrides)
    return Admin(**defaults)


@pytest.fixture
def mock_admin_service():
    return MagicMock()


@pytest.fixture
def mock_caesi_service():
    return MagicMock()


@pytest.fixture
def client(mock_admin_service, mock_caesi_service):
    app = FastAPI()
    app.include_router(admin_routes.router)
    app.include_router(caesi_routes.router)
    app.include_router(chapa_routes.router)

    app.dependency_overrides[get_admin_service] = lambda: mock_admin_service
    app.dependency_overrides[get_caesi_service] = lambda: mock_caesi_service
    app.dependency_overrides[get_current_admin] = lambda: {"id": "1"}

    return TestClient(app)
