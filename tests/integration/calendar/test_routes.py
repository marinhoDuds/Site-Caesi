from datetime import date
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.routes.calendar.routes import router, get_calendar_service


app = FastAPI()
app.include_router(router, prefix="/calendar")

mock_service = MagicMock()


def override_get_calendar_service():
    return mock_service


app.dependency_overrides[get_calendar_service] = override_get_calendar_service

client = TestClient(app)


def _make_event(
    event_id=1,
    name="Semana Acadêmica",
    description="Evento de teste",
):
    return {
        "id": event_id,
        "name": name,
        "date": date.today(),
        "description": description,
    }


def test_list_events_route():
    mock_service.list_events.return_value = [
        _make_event(),
        _make_event(
            event_id=2,
            name="Workshop Python",
        ),
    ]

    response = client.get("/calendar/events")

    assert response.status_code == 200
    assert len(response.json()) == 2

    assert response.json()[0]["id"] == 1
    assert response.json()[1]["id"] == 2


def test_list_events_empty():
    mock_service.list_events.return_value = []

    response = client.get("/calendar/events")

    assert response.status_code == 200
    assert response.json() == []


def test_get_event_route():
    mock_service.get_event.return_value = _make_event(
        event_id=5,
        name="Palestra IA",
    )

    response = client.get("/calendar/events/5")

    assert response.status_code == 200
    assert response.json()["id"] == 5
    assert response.json()["name"] == "Palestra IA"


def test_get_event_not_found():
    mock_service.get_event.return_value = None

    response = client.get("/calendar/events/999")

    assert response.status_code == 404