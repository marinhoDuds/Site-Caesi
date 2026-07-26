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

def _set_engine_connect(mock_engine, scalar_return=None):
    """Wire mock_engine.connect() to a context-managed connection mock.
 
    The returned connection mock's `execute(...).scalar()` chain always
    resolves to `scalar_return`, which is what `_insert_attachment_owner`
    reads back as the new LAST_INSERT_ID.
    """
    mock_conn = MagicMock()
    mock_conn.execute.return_value.scalar.return_value = scalar_return
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    return mock_conn
 
def test_create_information_without_file(information_service, mock_engine):
    mock_conn = _set_engine_connect(mock_engine, scalar_return=42)
 
    payload = InformationCreate(
        content="Aviso geral para a comunidade.",
        information_type=InformationTypeEnum.announcements,
    )
 
    result = information_service.create_information(payload)
 
    assert result.id == 42
    assert result.content == "Aviso geral para a comunidade."
    assert result.information_type == InformationTypeEnum.announcements
    assert result.attachment_url is None
    assert mock_conn.execute.call_count == 3
    mock_conn.commit.assert_called()
 
 
def test_create_information_with_file(information_service, mock_engine):
    _set_engine_connect(mock_engine, scalar_return=7)
 
    with patch(
        "src.service.informations_management.service.upload_fileobj_to_s3"
    ) as mock_upload, patch(
        "src.service.informations_management.service.run_query"
    ) as mock_run:
        mock_upload.return_value = "http://s3/information/7/mapa.pdf"
 
        payload = InformationCreate(
            content="Entrada principal da UFCG.",
            information_type=InformationTypeEnum.map,
        )
 
        result = information_service.create_information(
            payload,
            file_obj=io.BytesIO(b"pdf-bytes"),
            filename="mapa.pdf",
            content_type="application/pdf",
        )
 
        assert result.id == 7
        assert result.attachment_url == "http://s3/information/7/mapa.pdf"
        mock_upload.assert_called_once()
        assert mock_upload.call_args[0][1] == "information/7/mapa.pdf"
        assert mock_upload.call_args[0][2] == "application/pdf"
        mock_run.assert_called_once()
 
 
def test_create_information_file_upload_fails(information_service, mock_engine):
    _set_engine_connect(mock_engine, scalar_return=9)
 
    with patch(
        "src.service.informations_management.service.upload_fileobj_to_s3"
    ) as mock_upload, patch("src.service.informations_management.service.run_query"):
        mock_upload.return_value = None
 
        payload = InformationCreate(
            content="Sem anexo", information_type=InformationTypeEnum.tamburetei
        )
 
        result = information_service.create_information(
            payload,
            file_obj=io.BytesIO(b"data"),
            filename="foo.txt",
            content_type="text/plain",
        )
 
        assert result.attachment_url is None
 
def test_update_information_not_found(information_service, mock_engine):
    with patch("src.service.informations_management.service.run_query") as mock_run:
        mock_run.return_value = []
 
        result = information_service.update_information(
            999, InformationUpdate(content="Tentando atualizar fantasma")
        )
 
        assert result is None
        mock_run.assert_called_once()
 
 
def test_update_information_content_and_type(information_service, mock_engine):
    row_before = _make_row(id=5, content="Old content", info_type="map")
    row_after = _make_row(
        id=5, content="Conteudo editado", info_type="laboratories"
    )
 
    with patch("src.service.informations_management.service.run_query") as mock_run:
        mock_run.side_effect = [[row_before], 1, [row_after]]
 
        payload = InformationUpdate(
            content="Conteudo editado",
            information_type=InformationTypeEnum.laboratories,
        )
        result = information_service.update_information(5, payload)
 
        assert result is not None
        assert result.content == "Conteudo editado"
        assert result.information_type == "laboratories"
        assert mock_run.call_count == 3

def test_update_information_no_fields_no_file(information_service, mock_engine):
    row = _make_row(id=5, content="Unchanged", info_type="professors")
 
    with patch("src.service.informations_management.service.run_query") as mock_run:
        mock_run.side_effect = [[row], [row]]
 
        result = information_service.update_information(5, InformationUpdate())
 
        assert result is not None
        assert result.content == "Unchanged"
        assert mock_run.call_count == 2
 
 
def test_update_information_with_file(information_service, mock_engine):
    row_before = _make_row(id=5, content="Aviso", info_type="announcements")
    row_after = _make_row(id=5, content="Aviso", info_type="announcements")
 
    with patch(
        "src.service.informations_management.service.upload_fileobj_to_s3"
    ) as mock_upload, patch(
        "src.service.informations_management.service.run_query"
    ) as mock_run:
        mock_upload.return_value = "http://s3/information/5/novo_anexo.pdf"
        mock_run.side_effect = [[row_before], None, [row_after]]
 
        result = information_service.update_information(
            5,
            InformationUpdate(),
            file_obj=io.BytesIO(b"new-pdf-bytes"),
            filename="novo_anexo.pdf",
            content_type="application/pdf",
        )
 
        assert result is not None
        mock_upload.assert_called_once()
        assert mock_upload.call_args[0][1] == "information/5/novo_anexo.pdf"
        assert mock_run.call_count == 3
 
def test_delete_information_not_found(information_service, mock_engine):
    with patch("src.service.informations_management.service.run_query") as mock_run:
        mock_run.return_value = []
 
        result = information_service.delete_information(999)
 
        assert result is False
        mock_run.assert_called_once()
 
 
def test_delete_information_success(information_service, mock_engine):
    row = _make_row(id=10, content="Entrada principal", info_type="map")
 
    with patch("src.service.informations_management.service.run_query") as mock_run:
        mock_run.side_effect = [[row], 1, 1, 1]
 
        result = information_service.delete_information(10)
 
        assert result is True
        assert mock_run.call_count == 4
 
 
def test_delete_information_raises_on_failure(information_service, mock_engine):
    row = _make_row(id=10, content="Entrada principal", info_type="map")
 
    with patch("src.service.informations_management.service.run_query") as mock_run:
        mock_run.side_effect = [[row], Exception("connection lost")]
 
        with pytest.raises(Exception, match="Failed to delete information"):
            information_service.delete_information(10)
