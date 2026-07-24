import pytest
from unittest.mock import MagicMock, patch

from src.service.informations_management.service import InformationService


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def information_service(mock_engine):
    return InformationService(engine=mock_engine)


def _make_row(
    id=1,
    content="A sala do professor Dalton é a 210, localizada no bloco SPLab.",
    info_type="professors",
):
    return (id, content, info_type, None)


def test_list_informations(information_service, mock_engine):
    with patch("src.service.informations_management.service.run_query") as mock_run:
        mock_run.return_value = [
            _make_row(),
            _make_row(
                id=2,
                content="O Laboratório de programação é no bloco CP.",
                info_type="laboratories",
            ),
        ]

        result = information_service.list_informations()

        mock_run.assert_called_once()
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].information_type == "professors"
        assert (
            result[0].content
            == "A sala do professor Dalton é a 210, localizada no bloco SPLab."
        )
        assert result[1].id == 2
        assert result[1].information_type == "laboratories"
        assert result[1].content == "O Laboratório de programação é no bloco CP."


def test_list_informations_empty(information_service, mock_engine):
    with patch("src.service.informations_management.service.run_query") as mock_run:
        mock_run.return_value = []

        result = information_service.list_informations()

        mock_run.assert_called_once()
        assert result == []


def test_get_information_found(information_service, mock_engine):
    with patch("src.service.informations_management.service.run_query") as mock_run:
        mock_run.return_value = [
            _make_row(id=5, content="Entrada principal da UFCG.", info_type="map")
        ]

        result = information_service.get_information(id=5)

        mock_run.assert_called_once()
        assert result is not None
        assert result.id == 5
        assert result.information_type == "map"
        assert result.content == "Entrada principal da UFCG."


def test_get_information_not_found(information_service, mock_engine):
    with patch("src.service.informations_management.service.run_query") as mock_run:
        mock_run.return_value = []

        result = information_service.get_information(id=999)

        mock_run.assert_called_once()
        assert result is None


def test_search_information_by_type(information_service, mock_engine):
    with patch("src.service.informations_management.service.run_query") as mock_run:
        mock_run.return_value = [
            _make_row(id=10, content="Lab 1", info_type="laboratories"),
            _make_row(id=11, content="Lab 2", info_type="laboratories"),
        ]

        result = information_service.list_informations(info_type="laboratories")

        mock_run.assert_called_once()
        assert len(result) == 2
        assert all(info.information_type == "laboratories" for info in result)


def test_search_informations_by_keyword(information_service, mock_engine):
    with patch("src.service.informations_management.service.run_query") as mock_run:
        mock_run.return_value = [
            _make_row(id=7, content="Professor Jorge.", info_type="professors")
        ]

        result = information_service.list_informations(keyword="Jorge")

        mock_run.assert_called_once()
        assert len(result) == 1
        assert result[0].id == 7
        assert "Jorge" in result[0].content


def test_search_information_no_result(information_service, mock_engine):
    with patch("src.service.informations_management.service.run_query") as mock_run:
        mock_run.return_value = []

        result = information_service.list_informations(keyword="pesquisa inexistente")

        mock_run.assert_called_once()
        assert result == []
