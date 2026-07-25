import pytest
from unittest.mock import patch, MagicMock
from pypika import Query, Table

import src.service.database as db_module


def test_create_engine_success(monkeypatch):
    monkeypatch.setenv("SQL_ALCHEMY_CONNECTION", "sqlite:///:memory:")

    with patch("src.service.database.sa_create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        engine = db_module.create_engine()
        assert engine is mock_engine
        mock_create_engine.assert_called_once_with("sqlite:///:memory:")


def test_create_engine_missing_env(monkeypatch):
    monkeypatch.delenv("SQL_ALCHEMY_CONNECTION", raising=False)
    with pytest.raises(ValueError, match="SQL_ALCHEMY_CONNECTION is not set"):
        db_module.create_engine()


def test_run_query_returns_rows():
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    mock_result = MagicMock()
    mock_result.returns_rows = True
    mock_result.all.return_value = [("row1",), ("row2",)]
    mock_conn.execute.return_value = mock_result

    table = Table("test_table")
    query = Query.from_(table).select("*")

    result = db_module.run_query(mock_engine, query)

    assert result == [("row1",), ("row2",)]
    mock_conn.commit.assert_called_once()
    mock_result.all.assert_called_once()


def test_run_query_returns_rowcount():
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    mock_result = MagicMock()
    mock_result.returns_rows = False
    mock_result.rowcount = 1
    mock_conn.execute.return_value = mock_result

    table = Table("test_table")
    query = Query.into(table).insert(1)

    result = db_module.run_query(mock_engine, query)

    assert result == 1
    mock_conn.commit.assert_called_once()
    mock_result.all.assert_not_called()
