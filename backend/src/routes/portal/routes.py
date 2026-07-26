from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from typing import List, Optional

from src.routes.portal.schemas import (
    OperationCreate,
    OperationResponse,
    OperationHistoryResponse,
    OperationType,
)
from src.service.portal_management.service import PortalService
from src.service.database import create_engine
from src.service.authentication.auth import get_current_admin

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


@router.post("/operations", response_model=OperationResponse, status_code=201)
async def create_operation(
    value: float = Form(...),
    description: str = Form(...),
    operation_type: OperationType = Form(...),
    attachment: Optional[UploadFile] = File(None),
    service: PortalService = Depends(get_portal_service),
    admin: dict = Depends(get_current_admin),
) -> OperationResponse:
    """Create a new operation endpoint.

    Accepts a multipart/form-data request with the operation fields and an
    optional comprobatory document file.

    Parameters
    ----------
    value : float
        Monetary value of the operation.
    description : str
        Description or object of the operation.
    operation_type : OperationType
        Category of the operation.
    attachment : Optional[UploadFile]
        The comprobatory document file to upload to S3, if any.
    service : PortalService, optional
        The injected portal service dependency.
    admin : dict
        The authenticated administrator payload.

    Returns
    -------
    OperationResponse
        The created operation data.
    """
    payload = OperationCreate(
        value=value,
        description=description,
        operation_type=operation_type,
    )

    file_obj = None
    filename = None
    content_type = "application/octet-stream"

    if attachment:
        file_obj = attachment.file
        filename = attachment.filename
        content_type = attachment.content_type or "application/octet-stream"

    return service.create_operation(
        payload,
        file_obj=file_obj,
        filename=filename,
        content_type=content_type,
    )


@router.put("/operations/{operation_id}", response_model=OperationResponse)
async def update_operation(
    operation_id: int,
    value: float = Form(...),
    description: str = Form(...),
    operation_type: OperationType = Form(...),
    attachment: Optional[UploadFile] = File(None),
    service: PortalService = Depends(get_portal_service),
    admin: dict = Depends(get_current_admin),
) -> OperationResponse:
    """Update an existing operation using append-only logic.

    If an attachment is provided it replaces the previous one (a new S3 object
    is created). If omitted, the previous operation's attachment URL is
    inherited.

    Parameters
    ----------
    operation_id : int
        The ID of the operation to update.
    value : float
        Monetary value of the updated operation.
    description : str
        Description or object of the updated operation.
    operation_type : OperationType
        Category of the updated operation.
    attachment : Optional[UploadFile]
        Replacement comprobatory document, if any.
    service : PortalService, optional
        The injected portal service dependency.
    admin : dict
        The authenticated administrator payload.

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

    payload = OperationCreate(
        value=value,
        description=description,
        operation_type=operation_type,
    )

    file_obj = None
    filename = None
    content_type = "application/octet-stream"

    if attachment:
        file_obj = attachment.file
        filename = attachment.filename
        content_type = attachment.content_type or "application/octet-stream"

    return service.update_operation(
        operation_id,
        payload,
        file_obj=file_obj,
        filename=filename,
        content_type=content_type,
    )


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


@router.delete("/operations/{operation_id}", status_code=204)
def delete_operation(
    operation_id: int,
    service: PortalService = Depends(get_portal_service),
    admin: dict = Depends(get_current_admin),
) -> None:
    """Delete an operation.

    Parameters
    ----------
    operation_id : int
        The ID of the operation to delete.
    service : PortalService, optional
        The injected portal service dependency.
    admin : dict
        The authenticated administrator payload.

    Raises
    ------
    HTTPException
        If the given operation_id is not found in the database.
    """
    deleted = service.delete_operation(operation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Operation not found")

