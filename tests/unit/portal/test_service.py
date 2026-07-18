import pytest
from datetime import date
from io import BytesIO
from unittest.mock import MagicMock, patch

from src.service.portal_management.service import PortalService
from src.routes.portal.schemas import OperationCreate, OperationType


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def portal_service(mock_engine):
    return PortalService(engine=mock_engine)


def _make_row(
    op_id=1,
    created=None,
    value=150.0,
    description="Desc",
    op_type=OperationType.procurement,
    previous=None,
    attachment_url=None,
):
    return (
        op_id,
        created or date.today(),
        value,
        description,
        op_type,
        previous,
        attachment_url,
    )


def test_create_operation_without_attachment(portal_service, mock_engine):
    payload = OperationCreate(
        value=150.0,
        description="Compra de suprimentos",
        operation_type=OperationType.procurement,
    )

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value.scalar.return_value = 1
    mock_engine.connect.return_value = mock_conn

    result = portal_service.create_operation(payload)

    assert result.id == 1
    assert result.value == 150.0
    assert result.description == "Compra de suprimentos"
    assert result.previous is None
    assert result.attachment_url is None


def test_create_operation_with_attachment(portal_service, mock_engine):
    payload = OperationCreate(
        value=500.0,
        description="Compra com nota fiscal",
        operation_type=OperationType.procurement,
    )
    file_obj = BytesIO(b"pdf-content")

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value.scalar.return_value = 2
    mock_engine.connect.return_value = mock_conn

    with patch(
        "src.service.portal_management.service.upload_fileobj_to_s3"
    ) as mock_upload:
        mock_upload.return_value = "http://s3/portal/2/nota.pdf"

        with patch("src.service.portal_management.service.run_query") as mock_run:
            mock_run.return_value = None  # INSERT attachment

            result = portal_service.create_operation(
                payload,
                file_obj=file_obj,
                filename="nota.pdf",
                content_type="application/pdf",
            )

    assert result.id == 2
    assert result.attachment_url == "http://s3/portal/2/nota.pdf"
    mock_upload.assert_called_once()


def test_update_operation_append_only_inherits_attachment(portal_service, mock_engine):
    payload = OperationCreate(
        value=200.0,
        description="Valor corrigido",
        operation_type=OperationType.procurement,
    )

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value.scalar.return_value = 3
    mock_engine.connect.return_value = mock_conn

    # _fetch_attachment_url chamará run_query
    with patch("src.service.portal_management.service.run_query") as mock_run:
        mock_run.return_value = [("http://s3/portal/1/nota.pdf",)]

        result = portal_service.update_operation(previous_id=1, payload=payload)

    assert result.id == 3
    assert result.previous == 1
    assert result.attachment_url == "http://s3/portal/1/nota.pdf"


def test_update_operation_with_new_attachment(portal_service, mock_engine):
    payload = OperationCreate(
        value=300.0,
        description="Documento atualizado",
        operation_type=OperationType.procurement,
    )
    file_obj = BytesIO(b"new-pdf")

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value.scalar.return_value = 4
    mock_engine.connect.return_value = mock_conn

    with patch(
        "src.service.portal_management.service.upload_fileobj_to_s3"
    ) as mock_upload:
        mock_upload.return_value = "http://s3/portal/4/new.pdf"

        with patch("src.service.portal_management.service.run_query") as mock_run:
            mock_run.return_value = None

            result = portal_service.update_operation(
                previous_id=1,
                payload=payload,
                file_obj=file_obj,
                filename="new.pdf",
                content_type="application/pdf",
            )

    assert result.id == 4
    assert result.previous == 1
    assert result.attachment_url == "http://s3/portal/4/new.pdf"


def test_get_operation_not_found(portal_service, mock_engine):
    with patch("src.service.portal_management.service.run_query") as mock_run:
        mock_run.return_value = []

        result = portal_service.get_operation(operation_id=99)

    assert result is None


def test_get_operation_history(portal_service, mock_engine):
    with patch("src.service.portal_management.service.run_query") as mock_run:
        mock_run.side_effect = [
            [_make_row(op_id=2, value=200.0, description="Corrigido", previous=1)],
            [_make_row(op_id=1, value=150.0, description="Original", previous=None)],
        ]

        result = portal_service.get_operation(operation_id=2)

    assert result.id == 2
    assert len(result.history) == 1
    assert result.history[0].id == 1


def test_list_operations_no_filter(portal_service, mock_engine):
    with patch("src.service.portal_management.service.run_query") as mock_run:
        mock_run.return_value = [
            _make_row(op_id=1),
            _make_row(op_id=2, previous=1),
        ]

        results = portal_service.list_operations()

    assert len(results) == 2


def test_list_operations_with_filter(portal_service, mock_engine):
    with patch("src.service.portal_management.service.run_query") as mock_run:
        mock_run.return_value = [
            _make_row(op_id=1, op_type=OperationType.procurement),
        ]

        results = portal_service.list_operations(
            operation_type=OperationType.procurement
        )

    assert len(results) == 1
    assert results[0].operation_type == OperationType.procurement


def test_list_operations_empty(portal_service, mock_engine):
    with patch("src.service.portal_management.service.run_query") as mock_run:
        mock_run.return_value = []

        results = portal_service.list_operations()

    assert results == []
