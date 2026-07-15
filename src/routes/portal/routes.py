from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from src.routes.portal.schemas import (
    OperationCreate,
    OperationResponse,
    OperationHistoryResponse,
    OperationType,
)
from src.service.portal_management.service import PortalService
from src.service.database import create_engine

router = APIRouter(tags=["Portal da Transparência"])


def get_portal_service() -> PortalService:
    """Dependency injector for PortalService.

    Returns
    -------
    PortalService
        An instantiated PortalService with a valid database engine.
    """
    engine = create_engine()
    return PortalService(engine)


# TODO: forçar admin (falta o jwt aqui)
@router.post("/operations", response_model=OperationResponse, status_code=201)
def create_operation(
    payload: OperationCreate, service: PortalService = Depends(get_portal_service)
) -> OperationResponse:
    """Create a new operation endpoint.

    Parameters
    ----------
    payload : OperationCreate
        The JSON payload containing operation details.
    service : PortalService, optional
        The injected portal service dependency.

    Returns
    -------
    OperationResponse
        The created operation data.
    """
    return service.create_operation(payload)


# TODO: aqui tbm falta o jwt
@router.put("/operations/{operation_id}", response_model=OperationResponse)
def update_operation(
    operation_id: int,
    payload: OperationCreate,
    service: PortalService = Depends(get_portal_service),
) -> OperationResponse:
    """Update an existing operation using append-only logic.

    Parameters
    ----------
    operation_id : int
        The ID of the operation to update.
    payload : OperationCreate
        The JSON payload containing the updated operation details.
    service : PortalService, optional
        The injected portal service dependency.

    Returns
    -------
    OperationResponse
        The newly created operation version data.

    Raises
    ------
    HTTPException
        If the given operation_id is not found in the database.
    """
    existing = service.get_operation(operation_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Operation not found")

    return service.update_operation(operation_id, payload)


@router.get("/operations", response_model=List[OperationResponse])
def list_operations(
    operation_type: Optional[OperationType] = None,
    service: PortalService = Depends(get_portal_service),
) -> List[OperationResponse]:
    """List operations endpoints with optional filtering.

    Parameters
    ----------
    operation_type : Optional[OperationType], optional
        Query parameter to filter operations by type, by default None.
    service : PortalService, optional
        The injected portal service dependency.

    Returns
    -------
    List[OperationResponse]
        A list of retrieved operations.
    """
    return service.list_operations(operation_type)


@router.get("/operations/{operation_id}", response_model=OperationHistoryResponse)
def get_operation(
    operation_id: int, service: PortalService = Depends(get_portal_service)
) -> OperationHistoryResponse:
    """Retrieve an operation and its history.

    Parameters
    ----------
    operation_id : int
        The ID of the operation to retrieve.
    service : PortalService, optional
        The injected portal service dependency.

    Returns
    -------
    OperationHistoryResponse
        The operation and its modification history.

    Raises
    ------
    HTTPException
        If the given operation_id is not found in the database.
    """
    result = service.get_operation(operation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Operation not found")
    return result
