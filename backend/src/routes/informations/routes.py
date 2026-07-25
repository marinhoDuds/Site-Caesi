from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from src.routes.informations.schemas import InformationResponse, InformationCreate, InformationUpdate
from sqlalchemy import Engine
from src.service.database import create_engine
from src.service.informations_management.service import InformationService
from src.service.authentication.auth import get_current_admin

# Public router
router = APIRouter(prefix="/informations", tags=["Informations"])

# Admin router
admin_router = APIRouter(prefix="/admin/informations", tags=["Admin Informations"])

def get_information_service() -> InformationService:
    engine = create_engine()
    return InformationService(engine)

@router.get("/type/{info_type}", response_model=List[InformationResponse])
def get_informations_by_type(info_type: str, service: InformationService = Depends(get_information_service)):
    """Fetch all informations of a given type (e.g., announcements, laboratories, professors, tamburetei)."""
    return service.get_informations_by_type(info_type)

@admin_router.post("/", response_model=InformationResponse, status_code=status.HTTP_201_CREATED)
def create_information(
    info: InformationCreate,
    service: InformationService = Depends(get_information_service),
    _admin: dict = Depends(get_current_admin)
):
    """Admin route to create new information."""
    return service.create_information(info.information_type, info.content)

@admin_router.put("/{info_id}", response_model=InformationResponse)
def update_information(
    info_id: int,
    info: InformationUpdate,
    service: InformationService = Depends(get_information_service),
    _admin: dict = Depends(get_current_admin)
):
    """Admin route to update an existing information."""
    updated = service.update_information(info_id, info.information_type, info.content)
    if not updated:
        raise HTTPException(status_code=404, detail="Information not found")
    return updated

@admin_router.delete("/{info_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_information(
    info_id: int,
    service: InformationService = Depends(get_information_service),
    _admin: dict = Depends(get_current_admin)
):
    """Admin route to delete an information."""
    existing = service.get_information_by_id(info_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Information not found")
    service.delete_information(info_id)
