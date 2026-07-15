import pytest
from datetime import date
from unittest.mock import MagicMock, patch

from src.service.portal_management.service import PortalService
from src.routes.portal.schemas import OperationCreate, OperationType

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def portal_service(mock_engine):
    return PortalService(engine=mock_engine)

def test_create_operation(portal_service, mock_engine):
    # Arrange
    payload = OperationCreate(
        value=150.0,
        description="Compra de suprimentos",
        operation_type=OperationType.procurement
    )

    with patch("src.service.portal_management.service.run_query") as mock_run_query:
        mock_run_query.side_effect = [
            1,
            [(1, date.today(), 150.0, "Compra de suprimentos", OperationType.procurement, None)]
        ]

        # Act
        result = portal_service.create_operation(payload)

        # Assert
        assert result.id == 1
        assert result.value == payload.value
        assert result.description == payload.description
        assert mock_run_query.called

def test_update_operation_append_only(portal_service, mock_engine):
    # Arrange
    payload = OperationCreate(
        value=200.0,
        description="Compra de suprimentos (valor corrigido)",
        operation_type=OperationType.procurement
    )

    with patch("src.service.portal_management.service.run_query") as mock_run_query:
        mock_run_query.side_effect = [
            1,
            [(2, date.today(), 200.0, "Compra de suprimentos (valor corrigido)", OperationType.procurement, 1)]
        ]

        # Act
        result = portal_service.update_operation(previous_id=1, payload=payload)

        # Assert
        assert result.id == 2
        assert result.previous == 1
        assert mock_run_query.called

def test_get_operation_history(portal_service, mock_engine):
    # Arrange
    with patch("src.service.portal_management.service.run_query") as mock_run_query:
        mock_run_query.side_effect = [
            [(2, date.today(), 200.0, "Corrigido", OperationType.procurement, 1)],
            [(1, date.today(), 150.0, "Original", OperationType.procurement, None)]
        ]

        # Act
        result = portal_service.get_operation(operation_id=2)

        # Assert
        assert result.id == 2
        assert len(result.history) == 1
        assert result.history[0].id == 1

def test_list_operations(portal_service, mock_engine):
    # Arrange
    with patch("src.service.portal_management.service.run_query") as mock_run_query:
        mock_run_query.return_value = [
            (1, date.today(), 150.0, "Original", OperationType.procurement, None)
        ]

        # Act
        results = portal_service.list_operations(operation_type=OperationType.procurement)

        # Assert
        assert len(results) == 1
        assert results[0].id == 1
