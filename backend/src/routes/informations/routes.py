"""
Routes for managing generic information records (announcements, labs, professors, etc.).
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from src.routes.informations.schemas import (
    InformationCreate,
    InformationResponse,
    InformationUpdate,
)
from src.service.authentication.auth import get_current_admin
from src.service.database import create_engine
from src.service.informations_management.service import InformationService

router = APIRouter(prefix="/informations", tags=["Informations"])
admin_router = APIRouter(prefix="/admin/informations", tags=["Admin Informations"])


def get_information_service() -> InformationService:
    """Dependency factory for InformationService.

    Returns
    -------
    InformationService
        Initialized InformationService instance.
    """
    engine = create_engine()
    return InformationService(engine)


@router.get("/type/{info_type}", response_model=List[InformationResponse])
def get_informations_by_type(
    info_type: str,
    service: InformationService = Depends(get_information_service),
):
    """Fetch all information records of a given type.

    Parameters
    ----------
    info_type : str
        The type category (e.g., announcements, laboratories, professors, tamburetei).
    service : InformationService
        Injected information service dependency.

    Returns
    -------
    List[InformationResponse]
        List of information objects belonging to the specified type.
    """
    return service.get_informations_by_type(info_type)


@admin_router.post(
    "/",
    response_model=InformationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_information(
    info: InformationCreate,
    service: InformationService = Depends(get_information_service),
    _admin: dict = Depends(get_current_admin),
):
    """Admin route to create new information entry.

    Parameters
    ----------
    info : InformationCreate
        Request payload with information_type and content.
    service : InformationService
        Injected information service dependency.
    _admin : dict
        Authenticated admin claims.

    Returns
    -------
    InformationResponse
        Created information record details.
    """
    return service.create_information(info.information_type, info.content)


@admin_router.put("/{info_id}", response_model=InformationResponse)
def update_information(
    info_id: int,
    info: InformationUpdate,
    service: InformationService = Depends(get_information_service),
    _admin: dict = Depends(get_current_admin),
):
    """Admin route to update an existing information entry.

    Parameters
    ----------
    info_id : int
        ID of the information record to update.
    info : InformationUpdate
        Request payload with updated fields.
    service : InformationService
        Injected information service dependency.
    _admin : dict
        Authenticated admin claims.

    Returns
    -------
    InformationResponse
        Updated information record.
    """
    updated = service.update_information(info_id, info.information_type, info.content)
    if not updated:
        raise HTTPException(status_code=404, detail="Information not found")
    return updated


@admin_router.delete("/{info_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_information(
    info_id: int,
    service: InformationService = Depends(get_information_service),
    _admin: dict = Depends(get_current_admin),
):
    """Admin route to delete an information entry.

    Parameters
    ----------
    info_id : int
        ID of the information record to delete.
    service : InformationService
        Injected information service dependency.
    _admin : dict
        Authenticated admin claims.
    """
    existing = service.get_information_by_id(info_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Information not found")
    service.delete_information(info_id)

