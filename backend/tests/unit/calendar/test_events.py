import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from src.main import app
from src.service.event_management.service import EventService
from src.routes.events.routes import get_event_service
from src.service.authentication.auth import get_current_admin


@pytest.fixture
def service():
    return EventService(engine="mock_engine")


def test_create_and_list_events(service, monkeypatch):
    mock_db = []

    def mock_run_query(engine, sql):
        sql_str = str(sql)
        if "INSERT" in sql_str:
            mock_db.append(
                {
                    "id": 1,
                    "title": "Evento Teste",
                    "scheduled_to": "2026-08-01",
                    "description": "Descricao",
                    "formulario_id": 42,
                }
            )
            return 1
        elif "SELECT" in sql_str:
            return mock_db

    monkeypatch.setattr(
        "src.service.event_management.service.run_query", mock_run_query
    )

    created = service.create_event(
        "Evento Teste", "2026-08-01", "Descricao", formulario_id=42
    )
    assert created["id"] == 1
    assert created["title"] == "Evento Teste"
    assert created["formulario_id"] == 42

    events = service.list_events()
    assert len(events) == 1
    assert events[0]["formulario_id"] == 42


def test_get_update_delete_event(service, monkeypatch):
    mock_db = [
        {
            "id": 1,
            "title": "Evento Inicial",
            "scheduled_to": "2026-08-01",
            "description": "Desc",
            "formulario_id": None,
        }
    ]

    def mock_run_query(engine, sql):
        sql_str = str(sql)
        if "UPDATE" in sql_str:
            mock_db[0]["title"] = "Evento Atualizado"
            mock_db[0]["formulario_id"] = 99
            return None
        elif "DELETE" in sql_str:
            mock_db.clear()
            return None
        return mock_db

    monkeypatch.setattr(
        "src.service.event_management.service.run_query", mock_run_query
    )

    fetched = service.get_event_by_id(1)
    assert fetched["title"] == "Evento Inicial"

    updated = service.update_event(
        1, "Evento Atualizado", "2026-08-01", "Desc", formulario_id=99
    )
    assert updated["title"] == "Evento Atualizado"
    assert updated["formulario_id"] == 99

    deleted = service.delete_event(1)
    assert deleted is True


def test_event_routes(monkeypatch):
    mock_service = MagicMock()
    app.dependency_overrides[get_event_service] = lambda: mock_service
    app.dependency_overrides[get_current_admin] = lambda: {"sub": "admin"}

    try:
        mock_service.list_events.return_value = [
            {
                "id": 1,
                "title": "Evento 1",
                "scheduled_to": "2026-08-01",
                "description": "",
                "formulario_id": 10,
            }
        ]
        client = TestClient(app)
        res = client.get("/events/")
        assert res.status_code == 200
        assert res.json()[0]["formulario_id"] == 10

        mock_service.create_event.return_value = {
            "id": 2,
            "title": "Novo Evento",
            "scheduled_to": "2026-08-05",
            "description": "Nova desc",
            "formulario_id": 20,
        }
        res_post = client.post(
            "/admin/events/",
            json={
                "title": "Novo Evento",
                "scheduled_to": "2026-08-05",
                "description": "Nova desc",
                "formulario_id": 20,
            },
        )
        assert res_post.status_code == 201
        assert res_post.json()["formulario_id"] == 20

        mock_service.get_event_by_id.return_value = {"id": 2}
        mock_service.update_event.return_value = {
            "id": 2,
            "title": "Evento Alt",
            "scheduled_to": "2026-08-05",
            "description": "Nova desc",
            "formulario_id": 20,
        }
        res_put = client.put(
            "/admin/events/2",
            json={
                "title": "Evento Alt",
                "scheduled_to": "2026-08-05",
                "description": "Nova desc",
                "formulario_id": 20,
            },
        )
        assert res_put.status_code == 200
        assert res_put.json()["title"] == "Evento Alt"

        res_del = client.delete("/admin/events/2")
        assert res_del.status_code == 204

        # Test 404 routes
        mock_service.get_event_by_id.return_value = None
        res_put_404 = client.put(
            "/admin/events/999",
            json={
                "title": "Evento Alt",
                "scheduled_to": "2026-08-05",
                "description": "Nova desc",
            },
        )
        assert res_put_404.status_code == 404

        res_del_404 = client.delete("/admin/events/999")
        assert res_del_404.status_code == 404
    finally:
        app.dependency_overrides.clear()
