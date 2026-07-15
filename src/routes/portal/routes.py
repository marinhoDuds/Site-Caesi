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
    engine = create_engine()
    return PortalService(engine)


# TODO: forçar admin (falta o jwt aqui)
@router.post("/operations", response_model=OperationResponse, status_code=201)
def create_operation(
    payload: OperationCreate, service: PortalService = Depends(get_portal_service)
):
    return service.create_operation(payload)


# TODO: aqui tbm falta o jwt
@router.put("/operations/{operation_id}", response_model=OperationResponse)
def update_operation(
    operation_id: int,
    payload: OperationCreate,
    service: PortalService = Depends(get_portal_service),
):
    existing = service.get_operation(operation_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Operation not found")

    return service.update_operation(operation_id, payload)


@router.get("/operations", response_model=List[OperationResponse])
def list_operations(
    operation_type: Optional[OperationType] = None,
    service: PortalService = Depends(get_portal_service),
):
    return service.list_operations(operation_type)


@router.get("/operations/{operation_id}", response_model=OperationHistoryResponse)
def get_operation(
    operation_id: int, service: PortalService = Depends(get_portal_service)
):
    result = service.get_operation(operation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Operation not found")
    return result
