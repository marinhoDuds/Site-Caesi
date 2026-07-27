"""HTTP endpoints for private S3 attachments."""
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from src.service.attachment_service import Attachment, AttachmentService
from src.service.authentication.auth import get_current_admin
from src.service.database import create_engine

router = APIRouter(prefix="/attachments", tags=["attachments"])
admin_router = APIRouter(prefix="/admin/attachments", tags=["admin-attachments"])

MAX_FILE_SIZE = 10 * 1024 * 1024


def get_attachment_service() -> AttachmentService:
    return AttachmentService(create_engine())


def to_response(attachment: Attachment) -> dict[str, str | int]:
    return {
        "id": attachment.id,
        "owner_id": attachment.owner_id,
        "filename": attachment.filename,
        "content_type": attachment.content_type,
        "url": f"/attachments/{attachment.id}",
    }


@router.post("/upload", status_code=status.HTTP_201_CREATED)
@admin_router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_attachment_generic(
    attachment: UploadFile = File(...),
    service: AttachmentService = Depends(get_attachment_service),
) -> dict[str, str | int]:
    if not attachment.filename:
        raise HTTPException(status_code=400, detail="Attachment filename is required")
    contents = await attachment.read(MAX_FILE_SIZE + 1)
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Attachments are limited to 10 MB")

    owner_id = service.create_owner("information")

    from io import BytesIO

    stored = service.upload(
        owner_id,
        BytesIO(contents),
        attachment.filename,
        attachment.content_type or "application/octet-stream",
    )
    return to_response(stored)


@admin_router.post("/{owner_id}", status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    owner_id: int,
    attachment: UploadFile = File(...),
    service: AttachmentService = Depends(get_attachment_service),
    _admin: dict = Depends(get_current_admin),
) -> dict[str, str | int]:
    if not attachment.filename:
        raise HTTPException(status_code=400, detail="Attachment filename is required")
    contents = await attachment.read(MAX_FILE_SIZE + 1)
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Attachments are limited to 10 MB")

    from io import BytesIO

    stored = service.upload(
        owner_id,
        BytesIO(contents),
        attachment.filename,
        attachment.content_type or "application/octet-stream",
    )
    return to_response(stored)


@router.get("/{attachment_id}")
def download_attachment(
    attachment_id: int,
    service: AttachmentService = Depends(get_attachment_service),
) -> StreamingResponse:
    attachment = service.get(attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    response = service.open(attachment)
    if not response:
        raise HTTPException(status_code=404, detail="Attachment data not found")

    body = response["Body"]
    if hasattr(body, "iter_chunks"):
        stream_gen = body.iter_chunks(chunk_size=64 * 1024)
    else:
        stream_gen = iter(lambda: body.read(64 * 1024), b"")

    return StreamingResponse(
        stream_gen,
        media_type=attachment.content_type,
        headers={"Content-Disposition": f'inline; filename="{attachment.filename}"'},
    )


@admin_router.put("/reassign/{owner_id}")
def reassign_attachment_owner(
    owner_id: int,
    attachment_ids: list[int],
    service: AttachmentService = Depends(get_attachment_service),
    _admin: dict = Depends(get_current_admin),
) -> dict[str, str]:
    service.reassign_owner(attachment_ids, owner_id)
    return {"status": "ok"}


@admin_router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: int,
    service: AttachmentService = Depends(get_attachment_service),
    _admin: dict = Depends(get_current_admin),
) -> None:
    if not service.delete(attachment_id):
        raise HTTPException(status_code=404, detail="Attachment not found")
