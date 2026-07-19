import pytest
from datetime import date
from unittest.mock import MagicMock, patch

from src.service.calendar.service import CalendarService


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def calendar_service(mock_engine):
    return CalendarService(engine=mock_engine)


def _make_row(
    event_id=1,
    name="Semana Acadêmica",
    event_date=None,
    description="Evento de teste",
):
    return (
        event_id,
        name,
        event_date or date.today(),
        description,
    )


def test_list_events(calendar_service, mock_engine):
    with patch("src.service.calendar.service.run_query") as mock_run:
        mock_run.return_value = [
            _make_row(),
            _make_row(
                event_id=2,
                name="Workshop Python",
            ),
        ]

        result = calendar_service.list_events()

    assert len(result) == 2
    assert result[0].id == 1
    assert result[0].name == "Semana Acadêmica"
    assert result[1].id == 2
    assert result[1].name == "Workshop Python"


def test_list_events_empty(calendar_service, mock_engine):
    with patch("src.service.calendar.service.run_query") as mock_run:
        mock_run.return_value = []

        result = calendar_service.list_events()

    assert result == []


def test_get_event(calendar_service, mock_engine):
    with patch("src.service.calendar.service.run_query") as mock_run:
        mock_run.return_value = [
            _make_row(
                event_id=5,
                name="Palestra IA",
            )
        ]

        result = calendar_service.get_event(event_id=5)

    assert result.id == 5
    assert result.name == "Palestra IA"
    assert result.description == "Evento de teste"


def test_get_event_not_found(calendar_service, mock_engine):
    with patch("src.service.calendar.service.run_query") as mock_run:
        mock_run.return_value = []

        result = calendar_service.get_event(event_id=99)

    assert result is None