import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import date
from unittest.mock import MagicMock

from src.routes.portal.routes import router, get_portal_service
from src.routes.portal.schemas import OperationResponse, OperationHistoryResponse, OperationType

app = FastAPI()
app.include_router(router, prefix="/portal")

mock_service = MagicMock()

def override_get_portal_service():
    return mock_service

app.dependency_overrides[get_portal_service] = override_get_portal_service

client = TestClient(app)

def test_create_operation_route():
    # Arrange
    mock_service.create_operation.return_value = OperationResponse(
        id=1,
        created_at=date.today(),
        value=500.0,
        description="Test",
        operation_type=OperationType.procurement,
        previous=None
    )
    
    # Act
    response = client.post("/portal/operations", json={
        "value": 500.0,
        "description": "Test",
        "operation_type": "procurement"
    })
    
    # Assert
    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["value"] == 500.0

def test_list_operations_route():
    # Arrange
    mock_service.list_operations.return_value = [
        OperationResponse(
            id=1,
            created_at=date.today(),
            value=500.0,
            description="Test",
            operation_type=OperationType.procurement,
            previous=None
        )
    ]
    
    # Act
    response = client.get("/portal/operations")
    
    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_get_operation_route():
    # Arrange
    mock_service.get_operation.return_value = OperationHistoryResponse(
        id=1,
        created_at=date.today(),
        value=500.0,
        description="Test",
        operation_type=OperationType.procurement,
        previous=None,
        history=[]
    )
    
    # Act
    response = client.get("/portal/operations/1")
    
    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == 1

def test_get_operation_not_found():
    # Arrange
    mock_service.get_operation.return_value = None
    
    # Act
    response = client.get("/portal/operations/999")
    
    # Assert
    assert response.status_code == 404

def test_update_operation_route():
    # Arrange
    mock_service.get_operation.return_value = OperationHistoryResponse(
        id=1,
        created_at=date.today(),
        value=500.0,
        description="Test",
        operation_type=OperationType.procurement,
        previous=None,
        history=[]
    )
    mock_service.update_operation.return_value = OperationResponse(
        id=2,
        created_at=date.today(),
        value=600.0,
        description="Test Updated",
        operation_type=OperationType.procurement,
        previous=1
    )
    
    # Act
    response = client.put("/portal/operations/1", json={
        "value": 600.0,
        "description": "Test Updated",
        "operation_type": "procurement"
    })
    
    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == 2
    assert response.json()["previous"] == 1
