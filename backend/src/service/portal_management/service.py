from datetime import date
from typing import BinaryIO, List, Optional, Any
from pypika import Table, Query
from sqlalchemy import Engine, text

from src.service.database import run_query
from src.service.attachment_service import AttachmentService
from src.service.s3 import upload_fileobj_to_s3
from src.routes.portal.schemas import (
    OperationCreate,
    OperationType,
    OperationResponse,
    OperationHistoryResponse,
)

operation_table = Table("operation")
attachment_owner_table = Table("attachment_owner")
attachment_table = Table("attachment")


class PortalService:
    """Service to handle business logic for the transparency portal operations.

    This service manages the creation, updating, retrieval, and listing of
    operations (artifacts). Updates are append-only to preserve history.
    Attachments are stored in S3 and referenced via the attachment table.

    Attributes
    ----------
    engine : Engine
        The SQLAlchemy engine used to connect to the database.
    """

    def __init__(self, engine: Engine) -> None:
        """Initialize a new PortalService.

        Parameters
        ----------
        engine : Engine
            The SQLAlchemy database engine instance.
        """
        self.engine = engine

    def _map_row_to_response(self, row: Any) -> OperationResponse:
        """Map a raw database row to an OperationResponse model.

        Parameters
        ----------
        row : Any
            The database row — a tuple of
            (id, created_at, value, description, operation_type, previous, attachment_id).

        Returns
        -------
        OperationResponse
            The mapped pydantic response model.
        """
        op_id, created_at, value, description, op_type, previous, attachment_id = row
        return OperationResponse(
            id=op_id,
            created_at=created_at,
            value=value,
            description=description,
            operation_type=op_type,
            previous=previous,
            attachment_url=f"/attachments/{attachment_id}" if attachment_id else None,
        )

    def _insert_attachment_owner(self) -> int:
        """Insert a new attachment_owner record of type 'operation'.

        Returns
        -------
        int
            The auto-generated ID of the new attachment_owner row.
        """
        with self.engine.connect() as conn:
            conn.execute(
                text("INSERT INTO attachment_owner (owner_type) VALUES (:t)"),
                {"t": "operation"},
            )
            owner_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            conn.commit()
        return int(owner_id or 0)

    def _insert_attachment(
        self, owner_id: int, object_key: str, filename: str, content_type: str
    ) -> int:
        """Insert an attachment record linking the owner to a media URL.

        Parameters
        ----------
        owner_id : int
            The attachment_owner id (same as the operation id).
        object_key : str
            The private S3 object key.
        """
        with self.engine.connect() as conn:
            conn.execute(
                text(
                    "INSERT INTO attachment (owner_id, object_key, filename, content_type) "
                    "VALUES (:owner_id, :object_key, :filename, :content_type)"
                ),
                {
                    "owner_id": owner_id,
                    "object_key": object_key,
                    "filename": filename,
                    "content_type": content_type,
                },
            )
            attachment_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            conn.commit()
        return int(attachment_id or 0)

    def _fetch_attachment_url(self, operation_id: int) -> Optional[str]:
        """Retrieve the attachment URL for a given operation id.

        Parameters
        ----------
        operation_id : int
            The operation (and attachment_owner) id.

        Returns
        -------
        Optional[str]
            The application download path of the first attachment found, or None.
        """
        query = (
            Query.from_(attachment_table)
            .select("id")
            .where(attachment_table.owner_id == operation_id)
            .limit(1)
        )
        result = run_query(self.engine, query)
        if result:
            return f"/attachments/{result[0][0]}"
        return None

    def _upload_file(
        self,
        operation_id: int,
        file_obj: BinaryIO,
        filename: str,
        content_type: str,
    ) -> Optional[str]:
        """Upload a file to S3 and persist the URL in the attachment table.

        Parameters
        ----------
        operation_id : int
            The operation id used to build the S3 object key.
        file_obj : BinaryIO
            The file-like object to upload.
        filename : str
            Original filename, used to build the object key.
        content_type : str
            MIME type of the file.

        Returns
        -------
        Optional[str]
            The S3 URL on success, None if upload failed.
        """
        object_name = f"portal/{operation_id}/{filename}"
        object_key = upload_fileobj_to_s3(file_obj, object_name, content_type)
        if object_key:
            attachment_id = self._insert_attachment(
                operation_id, object_key, filename, content_type
            )
            return f"/attachments/{attachment_id}"
        return None

    def create_operation(
        self,
        payload: OperationCreate,
        file_obj: Optional[BinaryIO] = None,
        filename: Optional[str] = None,
        content_type: str = "application/octet-stream",
    ) -> OperationResponse:
        """Create a new transparency operation, optionally with an attachment.

        The operation id reuses the attachment_owner id so that foreign key
        constraints are satisfied without an extra join.

        Parameters
        ----------
        payload : OperationCreate
            The data to create the operation.
        file_obj : Optional[BinaryIO]
            The file to upload as a comprobatory document.
        filename : Optional[str]
            Original filename for the uploaded file.
        content_type : str
            MIME type of the file.

        Returns
        -------
        OperationResponse
            The newly created operation data.

        Raises
        ------
        Exception
            If the created operation cannot be fetched from the database.
        """
        current_date = date.today()

        owner_id = self._insert_attachment_owner()

        with self.engine.connect() as conn:
            conn.execute(
                text(
                    "INSERT INTO operation "
                    "(id, created_at, value, description, operation_type, previous) "
                    "VALUES (:id, :ca, :v, :d, :ot, :prev)"
                ),
                {
                    "id": owner_id,
                    "ca": current_date,
                    "v": payload.value,
                    "d": payload.description,
                    "ot": payload.operation_type.value,
                    "prev": None,
                },
            )
            conn.commit()

        attachment_url: Optional[str] = None
        if file_obj and filename:
            attachment_url = self._upload_file(
                owner_id, file_obj, filename, content_type
            )

        return OperationResponse(
            id=owner_id,
            created_at=current_date,
            value=payload.value,
            description=payload.description,
            operation_type=payload.operation_type,
            previous=None,
            attachment_url=attachment_url,
        )

    def update_operation(
        self,
        previous_id: int,
        payload: OperationCreate,
        file_obj: Optional[BinaryIO] = None,
        filename: Optional[str] = None,
        content_type: str = "application/octet-stream",
    ) -> OperationResponse:
        """Update an operation using an append-only strategy.

        Creates a new attachment_owner + operation record pointing to the old
        one via the 'previous' field.  Optionally replaces the attachment.

        Parameters
        ----------
        previous_id : int
            The ID of the operation being updated.
        payload : OperationCreate
            The new data for the operation.
        file_obj : Optional[BinaryIO]
            The replacement file, if any.
        filename : Optional[str]
            Original filename for the replacement file.
        content_type : str
            MIME type of the file.

        Returns
        -------
        OperationResponse
            The newly created operation version data.
        """
        current_date = date.today()

        owner_id = self._insert_attachment_owner()

        with self.engine.connect() as conn:
            conn.execute(
                text(
                    "INSERT INTO operation "
                    "(id, created_at, value, description, operation_type, previous) "
                    "VALUES (:id, :ca, :v, :d, :ot, :prev)"
                ),
                {
                    "id": owner_id,
                    "ca": current_date,
                    "v": payload.value,
                    "d": payload.description,
                    "ot": payload.operation_type.value,
                    "prev": previous_id,
                },
            )
            conn.commit()

        attachment_url: Optional[str] = None
        if file_obj and filename:
            attachment_url = self._upload_file(
                owner_id, file_obj, filename, content_type
            )
        else:
            attachment_url = self._fetch_attachment_url(previous_id)

        return OperationResponse(
            id=owner_id,
            created_at=current_date,
            value=payload.value,
            description=payload.description,
            operation_type=payload.operation_type,
            previous=previous_id,
            attachment_url=attachment_url,
        )

    def get_operation(self, operation_id: int) -> Optional[OperationHistoryResponse]:
        """Fetch a specific operation and its full modification history.

        Parameters
        ----------
        operation_id : int
            The ID of the operation to retrieve.

        Returns
        -------
        Optional[OperationHistoryResponse]
            The operation data including its historical versions, or None if not found.
        """
        query = (
            Query.from_(operation_table)
            .left_join(attachment_table)
            .on(attachment_table.owner_id == operation_table.id)
            .select(
                operation_table.id,
                operation_table.created_at,
                operation_table.value,
                operation_table.description,
                operation_table.operation_type,
                operation_table.previous,
                attachment_table.id,
            )
            .where(operation_table.id == operation_id)
        )
        result = run_query(self.engine, query)

        if not result:
            return None

        base_resp = self._map_row_to_response(result[0])
        current = OperationHistoryResponse(**base_resp.model_dump(), history=[])

        history = []
        prev_id = current.previous
        while prev_id is not None:
            prev_query = (
                Query.from_(operation_table)
                .left_join(attachment_table)
                .on(attachment_table.owner_id == operation_table.id)
                .select(
                    operation_table.id,
                    operation_table.created_at,
                    operation_table.value,
                    operation_table.description,
                    operation_table.operation_type,
                    operation_table.previous,
                    attachment_table.id,
                )
                .where(operation_table.id == prev_id)
            )
            prev_result = run_query(self.engine, prev_query)
            if prev_result:
                p_resp = self._map_row_to_response(prev_result[0])
                history.append(p_resp)
                prev_id = p_resp.previous
            else:
                prev_id = None

        current.history = history
        return current

    def list_operations(
        self, operation_type: Optional[OperationType] = None
    ) -> List[OperationResponse]:
        """List transparency operations, optionally filtered by type.

        Only the latest version of each operation chain is returned —
        i.e. rows where another operation does NOT reference them as previous.

        Parameters
        ----------
        operation_type : Optional[OperationType], optional
            The operation type to filter by, by default None.

        Returns
        -------
        List[OperationResponse]
            A list of the most recent version of operations.
        """
        query = (
            Query.from_(operation_table)
            .left_join(attachment_table)
            .on(attachment_table.owner_id == operation_table.id)
            .select(
                operation_table.id,
                operation_table.created_at,
                operation_table.value,
                operation_table.description,
                operation_table.operation_type,
                operation_table.previous,
                attachment_table.id,
            )
        )
        if operation_type:
            query = query.where(operation_table.operation_type == operation_type.value)

        result = run_query(self.engine, query)

        ops = []
        if result:
            for row in result:
                ops.append(self._map_row_to_response(row))
        return ops

    def delete_operation(self, operation_id: int) -> bool:
        """Delete an operation by ID.

        Parameters
        ----------
        operation_id : int
            The ID of the operation to delete.

        Returns
        -------
        bool
            True if deleted successfully, False if not found.
        """
        existing = self.get_operation(operation_id)
        if not existing:
            return False

        with self.engine.connect() as conn:
            AttachmentService(self.engine).delete_for_owner(operation_id)
            conn.execute(text("DELETE FROM operation WHERE id = :id"), {"id": operation_id})
            conn.execute(text("DELETE FROM attachment_owner WHERE id = :id"), {"id": operation_id})
            conn.commit()
        return True
