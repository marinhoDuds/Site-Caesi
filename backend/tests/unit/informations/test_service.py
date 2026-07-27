from unittest.mock import MagicMock
from sqlalchemy import Engine
import pytest
from src.service.informations_management.service import InformationService


@pytest.fixture
def service():
    engine = MagicMock(spec=Engine)
    conn = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn
    conn.execute.return_value.scalar.return_value = 1
    return InformationService(engine=engine)


def test_create_and_get_information(service, monkeypatch):
    mock_db = []

    def mock_run_query(engine, sql):
        sql_str = str(sql)
        if "INSERT" in sql_str:
            mock_db.append(
                {
                    "id": 1,
                    "information_type": "announcements",
                    "content": '{"title": "test"}',
                }
            )
            return 1
        elif "SELECT" in sql_str:
            return mock_db

    monkeypatch.setattr(
        "src.service.informations_management.service.run_query", mock_run_query
    )

    result = service.create_information("announcements", '{"title": "test"}')
    assert result["id"] == 1
    assert result["information_type"] == "announcements"


def test_get_latest_information_empty(service, monkeypatch):
    monkeypatch.setattr(
        "src.service.informations_management.service.run_query", lambda e, q: []
    )
    assert service.get_latest_information() is None


def test_get_information_by_id_empty(service, monkeypatch):
    monkeypatch.setattr(
        "src.service.informations_management.service.run_query", lambda e, q: []
    )
    assert service.get_information_by_id(999) is None


def test_get_informations_by_type(service, monkeypatch):
    mock_db = [
        {"id": 1, "information_type": "laboratories", "content": '{"name": "Lab 1"}'}
    ]

    def mock_run_query(engine, sql):
        return mock_db

    monkeypatch.setattr(
        "src.service.informations_management.service.run_query", mock_run_query
    )

    result = service.get_informations_by_type("laboratories")
    assert len(result) == 1
    assert result[0]["information_type"] == "laboratories"


def test_update_information(service, monkeypatch):
    mock_db = [
        {"id": 1, "information_type": "professors", "content": '{"name": "Prof A"}'}
    ]

    def mock_run_query(engine, sql):
        sql_str = str(sql)
        if "UPDATE" in sql_str:
            mock_db[0]["content"] = '{"name": "Prof B"}'
            return None
        return mock_db

    monkeypatch.setattr(
        "src.service.informations_management.service.run_query", mock_run_query
    )

    result = service.update_information(1, "professors", '{"name": "Prof B"}')
    assert result["content"] == '{"name": "Prof B"}'


def test_delete_information(service, monkeypatch):
    def mock_run_query(engine, sql):
        return None

    monkeypatch.setattr(
        "src.service.informations_management.service.run_query", mock_run_query
    )

    result = service.delete_information(1)
    assert result is True
