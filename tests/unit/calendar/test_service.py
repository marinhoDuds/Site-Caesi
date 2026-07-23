import pytest
from datetime import date
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from src.service.calendar_management.service import CalendarService
from src.routes.calendar.schemas import EventCreate, EventUpdate 


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def calendar_service(mock_engine):
    return CalendarService(engine=mock_engine)


def _make_row(
    id=1,
    title="Semana Acadêmica",
    scheduled_to=None,
    description="Evento de teste",
):
    return (
        id,
        title,
        scheduled_to or date.today(),
        description,
    )


def test_list_events(calendar_service, mock_engine):
    with patch("src.service.calendar_management.service.run_query") as mock_run:
        mock_run.return_value = [
            _make_row(),
            _make_row(
                id=2,
                title="Workshop Python",
            ),
        ]

        result = calendar_service.list_events()

    assert len(result) == 2
    assert result[0].id == 1
    assert result[0].title == "Semana Acadêmica"
    assert result[1].id == 2
    assert result[1].title == "Workshop Python"


def test_list_events_empty(calendar_service, mock_engine):
    with patch("src.service.calendar_management.service.run_query") as mock_run:
        mock_run.return_value = []

        result = calendar_service.list_events()

    assert result == []


def test_get_event(calendar_service, mock_engine):
    with patch("src.service.calendar_management.service.run_query") as mock_run:
        mock_run.return_value = [
            _make_row(
                id=5,
                title="Palestra IA",
            )
        ]

        result = calendar_service.get_event(event_id=5)

    assert result.id == 5
    assert result.title == "Palestra IA"
    assert result.description == "Evento de teste"


def test_get_event_not_found(calendar_service, mock_engine):
    with patch("src.service.calendar_management.service.run_query") as mock_run:
        mock_run.return_value = []

        result = calendar_service.get_event(event_id=99)

    assert result is None


def test_creat_event_sucess(calendar_service, mock_engine):
    payload = EventCreate(
        title="Palestra de inteligência artificial",
        scheduled_to=date(2026, 8, 15),
        description="Palestra com professor convidado no auditório."
    )

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value.scalar.return_value = 1
    mock_engine.connect.return_value = mock_conn

    with patch("src.service.calendar_management.service.run_query") as mock_run:
        result = calendar_service.create_event(payload)

        mock_run.assert_called_onde()
        mock_conn.commit.assert_called_once()
        assert result.id == 1
        assert result.title == "Palestra de inteligência artificial"
        assert result.scheduled_to == date(15, 8, 2026)
        assert result.description == "Palestra com professor convidado no auditório."


def test_update_existing_event(calendar_service, mock_engine):
    payload = EventUpdate(
        title="Palestra de IA (Nova Data)",
        scheduled_to=date(2026, 8, 16)
    )

    with patch.object(calendar_service, "get_event") as mock_get:
        mock_get.return_value = MagicMock(
            id=10,
            title="Palestra de Inteligência Artificial",
            scheduled_to=date(2026, 8, 15),
            description="Palestra com professor convidado no auditório."
        )

        with patch("src.service.calendar_management.service.run_query") as mock_run:
            result = calendar_service.update_event(event_id=10, payload=payload)

            mock_run.assert_called_once()
            assert result.id == 10
            assert result.title == "Palestra de IA (Nova Data)"
            assert result.scheduled_to == date(2026, 8, 16)
            assert result.description == "Palestra com professor convidado no auditório"


def test_update_non_existent_event(calendar_service, mock_engine):
    payload = EventUpdate(
        title="Evento não existe"
    )

    with patch.object(calendar_service, "get_event") as mock_get:
        mock_get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            calendar_service.update_event(event_id=999, payload=payload)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Evento não encontrado"