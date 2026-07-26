from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from typing import Optional

from src.routes.informations.schemas import (
    InformationCreate,
    InformationUpdate,
    InformationResponse,
    InformationTypeEnum,
)
from src.service.informations_management.service import InformationService
from src.service.database import create_engine
from src.service.authentication.auth import get_current_admin


router = APIRouter(tags=["Gerenciamento de Informações"])


def get_information_service() -> InformationService:
    """Dependency injector for InformationService.

    Returns
    -------
    InformationService
        An instantiated InformationService with a valid database engine.
    """
    engine = create_engine()
    return InformationService(engine)


@router.post("/informations", response_model=InformationResponse, status_code=201)
async def create_information(
    content: str = Form(...),
    information_type: InformationTypeEnum = Form(...),
    attachment: Optional[UploadFile] = File(None),
    service: InformationService = Depends(get_information_service),
    admin: dict = Depends(get_current_admin),
) -> InformationResponse:
    """Create a new information endpoint for administrators.

    Accepts a multipart/form-data request with the information fields and an
    optional document file (e.g., a PDF for announcements).
    Map locations should be passed within the 'content' field as text.

    Parameters
    ----------
    content : str
        The main text content, description, or map location.
    information_type : InformationTypeEnum
        The category of the information.
    attachment: Optional[UploadFile]
        The document file to upload to S3, if any.
    service : InformationService, optional
        The injected information service dependency.
    admin : dict
        The authenticated administrator payload.

    Returns
    -------
    InformationResponse
        The created information data.
    """
    payload = InformationCreate(content=content, information_type=information_type)

    file_obj = None
    filename = None
    content_type = "application/octet-stream"

    if attachment:
        file_obj = attachment.file
        filename = attachment.filename
        content_type = attachment.content_type or content_type

    return service.create_information(
        payload, file_obj=file_obj, filename=filename, content_type=content_type
    )


@router.patch("/informations/{info_id}", response_model=InformationResponse)
async def update_information(
    info_id: int,
    content: Optional[str] = Form(None),
    information_type: Optional[InformationTypeEnum] = Form(None),
    attachment: Optional[UploadFile] = File(None),
    service: InformationService = Depends(get_information_service),
    admin: dict = Depends(get_current_admin),
) -> InformationResponse:
    """Update an existing information record.

    Allows partial updates. If a new attachment is provided, it replaces
    the existing S3 object reference.

    Parameters
    ----------
    info_id : int
        The ID of the information to update.
    content : Optional[str]
        The updated text content or map location.
    information_type : Optional[InformationTypeEnum]
        The updated category of the information.
    attachment : Optional[UploadFile]
        A new document file to upload and replace the existing one, if any.
    service : InformationService, optional
        The injected information admin service dependency.
    admin : dict
        The authenticated administrator payload.

    Returns
    -------
    InformationResponse
        The updated information data.

    Raises
    ------
    HTTPException
        If the given info_id is not found in the database.
    """
    payload = InformationUpdate(content=content, information_type=information_type)

    file_obj = None
    filename = None
    content_type = "application/octet-stream"

    if attachment:
        file_obj = attachment.file
        filename = attachment.filename
        content_type = attachment.content_type or content_type

    result = service.update_information(
        info_id,
        payload,
        file_obj=file_obj,
        filename=filename,
        content_type=content_type,
    )

    if not result:
        raise HTTPException(status_code=404, detail="Information not found")

    return result


@router.delete("/informations/{info_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_information(
    info_id: int,
    service: InformationService = Depends(get_information_service),
    admin: dict = Depends(get_current_admin),
) -> None:
    """Delete an existing information and its attachments.

    Parameters
    ----------
    info_id : int
        The ID of the information to delete.
    service : InformationService, optional
        The injected information admin service dependency.
    admin : dict
        The authenticated administrator payload.

    Raises
    ------
    HTTPException
        If the given info_id is not found in the database.
    """
    deleted = service.delete_information(info_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Information not found")

@router.get("/informations/list", response_model=list[InformationResponse])
async def list_informations(
    service: InformationService = Depends(get_information_service)
) -> list[InformationResponse]:
    """List all informations persisted.

    Parameters
    ----------
    service : InformationService, optional
        The injected information service dependency.
    
    Returns
    -------
    list[InformationResponse]
        The matching informations. Empty list if none match.
    """
    return service.list_informations()

@router.get("/informations/type/{info_type}", response_model=list[InformationResponse])
async def search_information_by_type(
    info_type: InformationTypeEnum,
    service: InformationService = Depends(get_information_service)
) -> list[InformationResponse]:
    """List informations that match the given type.

    Parameters
    ----------
    info_type : InformationTypeEnum
        Only informations of this exact type are returned.
    service : InformationService, optional
        The injected information service dependency.
    
    Returns
    -------
    list[InformationResponse]
        The matching informations. Empty list if none match.
    """
    return service.list_informations(info_type=info_type)

@router.get("/informations/search", response_model=list[InformationResponse])
async def search_information_by_keyword(
    keyword: str,
    service: InformationService = Depends(get_information_service)
) -> list[InformationResponse]:
    """List informations whose content contains the given keyword.

    Parameters
    ----------
    keyword : str
        Only informations whose content contains this keyword
        (case-insensitive substring match) are returned.
    service : InformationService, optional
        The injected information service dependency.
    
    Returns
    -------
    list[InformationResponse]
        The matching informations. Empty list if none match.
    """
    return service.list_informations(keyword=keyword)

@router.get("/informations/{info_id}", response_model=InformationResponse)
async def get_information(
    info_id: int,
    service: InformationService = Depends(get_information_service),
) -> InformationResponse:
    """Fetch a specific information by its ID.
    
    Parameters
    ----------
    info_id : int
        The ID of the information to retrieve.
    service : InformationService, optional
        The injected information service dependency.
    
    Returns
    -------
    InformationResponse
        The information data, or None if not found.
    
    Raises
    ------
    HTTPException
        If the given info_id is not found in the database.
    """
    result = service.get_information(info_id)

    if not result:
        raise HTTPException(status_code=404, detail="Information not found")

    return result
