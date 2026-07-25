import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from src.main import app
from src.routes.journal.routes import get_journal_service
from src.service.authentication.auth import get_current_admin

client = TestClient(app)

@pytest.fixture
def mock_journal_service():
    service = MagicMock()
    app.dependency_overrides[get_journal_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_journal_service, None)

@pytest.fixture
def override_admin_auth():
    app.dependency_overrides[get_current_admin] = lambda: {"user": "admin"}
    yield
    app.dependency_overrides.pop(get_current_admin, None)

def test_list_posts(mock_journal_service):
    mock_journal_service.list_posts.return_value = [
        {
            "id": 1,
            "title": "Test",
            "post_type": "aviso",
            "caption": "Cap",
            "created_at": "2024-01-01"
        }
    ]
    response = client.get("/journal/")
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_get_post(mock_journal_service):
    mock_journal_service.get_post.return_value = {
        "id": 1,
        "title": "Test",
        "post_type": "aviso",
        "caption": "Cap",
        "created_at": "2024-01-01"
    }
    response = client.get("/journal/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

def test_get_post_not_found(mock_journal_service):
    mock_journal_service.get_post.return_value = None
    response = client.get("/journal/999")
    assert response.status_code == 404

def test_create_post_admin(mock_journal_service, override_admin_auth):
    mock_journal_service.create_post.return_value = {
        "id": 1,
        "title": "Test",
        "post_type": "aviso",
        "caption": "Cap",
        "created_at": "2024-01-01"
    }
    payload = {
        "title": "Test",
        "post_type": "aviso",
        "caption": "CapCapCapCap"
    }
    response = client.post("/admin/journal/", json=payload)
    assert response.status_code == 201
    assert response.json()["id"] == 1

def test_update_post_admin(mock_journal_service, override_admin_auth):
    mock_journal_service.update_post.return_value = {
        "id": 1,
        "title": "Updated",
        "post_type": "aviso",
        "caption": "Cap",
        "created_at": "2024-01-01"
    }
    payload = {"title": "Updated"}
    response = client.patch("/admin/journal/1", json=payload)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"

def test_update_post_admin_not_found(mock_journal_service, override_admin_auth):
    mock_journal_service.update_post.return_value = None
    response = client.patch("/admin/journal/999", json={"title": "Updated"})
    assert response.status_code == 404

def test_delete_post_admin(mock_journal_service, override_admin_auth):
    mock_journal_service.delete_post.return_value = True
    response = client.delete("/admin/journal/1")
    assert response.status_code == 204

def test_delete_post_admin_not_found(mock_journal_service, override_admin_auth):
    mock_journal_service.delete_post.return_value = False
    response = client.delete("/admin/journal/999")
    assert response.status_code == 404
