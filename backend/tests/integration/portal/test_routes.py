from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import date
from unittest.mock import MagicMock

from src.routes.portal.routes import router, get_portal_service
from src.routes.portal.schemas import (
    OperationResponse,
    OperationHistoryResponse,
    OperationType,
)
from src.service.authentication.auth import get_current_admin

app = FastAPI()
app.include_router(router, prefix="/portal")

mock_service = MagicMock()


def override_get_portal_service():
    return mock_service


def override_get_current_admin():
    return {"id": 1}


app.dependency_overrides[get_portal_service] = override_get_portal_service
app.dependency_overrides[get_current_admin] = override_get_current_admin

client = TestClient(app)


def _make_op(
    op_id=1,
    value=500.0,
    description="Test",
    op_type=OperationType.procurement,
    previous=None,
    attachment_url=None,
) -> OperationResponse:
    return OperationResponse(
        id=op_id,
        created_at=date.today(),
        value=value,
        description=description,
        operation_type=op_type,
        previous=previous,
        attachment_url=attachment_url,
    )


def test_create_operation_route_without_file():
    mock_service.create_operation.return_value = _make_op()

    response = client.post(
        "/portal/operations",
        data={"value": "500.0", "description": "Test", "operation_type": "procurement"},
    )

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["attachment_url"] is None


def test_create_operation_route_with_file():
    mock_service.create_operation.return_value = _make_op(
        attachment_url="http://s3/portal/1/nota.pdf"
    )

    response = client.post(
        "/portal/operations",
        data={"value": "500.0", "description": "Test", "operation_type": "procurement"},
        files={"attachment": ("nota.pdf", b"pdf-bytes", "application/pdf")},
    )

    assert response.status_code == 201
    assert response.json()["attachment_url"] == "http://s3/portal/1/nota.pdf"
    mock_service.create_operation.assert_called()


def test_update_operation_route():
    mock_service.get_operation.return_value = OperationHistoryResponse(
        **_make_op().model_dump(), history=[]
    )
    mock_service.update_operation.return_value = _make_op(
        op_id=2, value=600.0, description="Test Updated", previous=1
    )

    response = client.put(
        "/portal/operations/1",
        data={
            "value": "600.0",
            "description": "Test Updated",
            "operation_type": "procurement",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == 2
    assert response.json()["previous"] == 1


def test_update_operation_route_with_new_file():
    mock_service.get_operation.return_value = OperationHistoryResponse(
        **_make_op().model_dump(), history=[]
    )
    mock_service.update_operation.return_value = _make_op(
        op_id=2,
        value=600.0,
        description="Test Updated",
        previous=1,
        attachment_url="http://s3/portal/2/new.pdf",
    )

    response = client.put(
        "/portal/operations/1",
        data={
            "value": "600.0",
            "description": "Test Updated",
            "operation_type": "procurement",
        },
        files={"attachment": ("new.pdf", b"new-pdf-bytes", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["attachment_url"] == "http://s3/portal/2/new.pdf"


def test_update_operation_not_found():
    mock_service.get_operation.return_value = None

    response = client.put(
        "/portal/operations/999",
        data={
            "value": "100.0",
            "description": "x",
            "operation_type": "other",
        },
    )

    assert response.status_code == 404


def test_list_operations_route():
    mock_service.list_operations.return_value = [_make_op()]

    response = client.get("/portal/operations")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_operations_route_with_filter():
    mock_service.list_operations.return_value = [_make_op()]

    response = client.get("/portal/operations?operation_type=procurement")

    assert response.status_code == 200
    mock_service.list_operations.assert_called_with(OperationType.procurement)


def test_get_operation_route():
    mock_service.get_operation.return_value = OperationHistoryResponse(
        **_make_op().model_dump(), history=[]
    )

    response = client.get("/portal/operations/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["history"] == []


def test_get_operation_not_found():
    mock_service.get_operation.return_value = None

    response = client.get("/portal/operations/999")

    assert response.status_code == 404
