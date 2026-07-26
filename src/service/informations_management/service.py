from typing import BinaryIO, Optional, Any
from pypika import Table, Query
from sqlalchemy import Engine, text

from src.service.database import run_query
from src.service.s3 import upload_fileobj_to_s3
from src.routes.informations.schemas import (
    InformationCreate,
    InformationUpdate,
    InformationResponse,
)


information_table = Table("information")
attachment_owner_table = Table("attachment_owner")
attachment_table = Table("attachment")


class InformationService:
    """Service to handle business logic for the informations management.

    This service manages the creation, updating, retrieval, and listing of
    informations (like announcements, laboratories, professors, etc).
    Attachments (e.g., map links) are stored in S3 and referenced via
    the attachment table

    Attributes
    ----------
    engine : Engine
        The SQLAlchemy engine used to connect to the database.
    """

    def __init__(self, engine: Engine) -> None:
        """Initialize a new InformationService.

        Parameters
        ----------
        engine : Engine
            The SQLAlchemy database engine instance.
        """
        self.engine = engine

    def _map_row_to_response(self, row: Any) -> InformationResponse:
        """Map a raw database row to an InformationResponse model.

        Parameters
        ----------
        row : Any
            The database row - a tuple of
            (id, content, information_type, attachment_url)

        Returns
        -------
        InformationResponse
            The mapped pydantic response model.
        """
        info_id, content, info_type, attachment_url = row
        return InformationResponse(
            id=info_id,
            content=content,
            information_type=info_type,
            attachment_url=attachment_url,
        )

    def _insert_attachment_owner(self) -> int:
        """Insert a new attachment_owner record of type 'information'.

        Returns
        -------
        int
            The auto-generated ID of the new attachment_owner row.
        """
        with self.engine.connect() as conn:
            conn.execute(
                text("INSERT INTO attachment_owner (owner_type) VALUES (:t)"),
                {"t": "information"},
            )
            owner_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            conn.commit()
        return int(owner_id or 0)

    def _insert_attachment(self, owner_id: int, midia_url: str) -> None:
        """Insert an attachment record linking the owner to a media URL.

        Parameters
        ----------
        owner_id : int
            The ID of the attachment owner (the information ID).
        midia_url : str
            The S3 URL of the uploaded media/document.
        """
        query = (
            Query.into(attachment_table)
            .columns("owner_id", "midia_url")
            .insert(owner_id, midia_url)
        )
        run_query(self.engine, query)

    def _fetch_attachment_url(self, owner_id: int) -> Optional[str]:
        """Retrieve the attachment URL for a given information id.

        Parameters
        ----------
        owner_id : int
            The ID of the attachment owner.

        Returns
        -------
        Optional[str]
            The URL of the attachment, or None if no attachment exists.
        """
        query = (
            Query.from_(attachment_table)
            .select("midia_url")
            .where(attachment_table.owner_id == owner_id)
            .limit(1)
        )
        result = run_query(self.engine, query)
        if result:
            return result[0][0]
        return None

    def _upload_file(
        self, info_id: int, file_obj: BinaryIO, filename: str, content_type: str
    ) -> Optional[str]:
        """Upload a file to S3 and persist the URL in the attachment table.

        Parameters
        ----------
        info_id : int
            The ID of the information that will own the file.
        file_obj : BinaryIO
            The file-like object to be uploaded.
        filename : str
            The original name of the file.
        content_type : str
            The MIME type of the file.

        Returns
        -------
        Optional[str]
            The generated S3 URL if successful, otherwise None.
        """
        object_name = f"information/{info_id}/{filename}"
        url = upload_fileobj_to_s3(file_obj, object_name, content_type)
        if url:
            self._insert_attachment(info_id, url)
        return url

    def get_information(self, id: int) -> Optional[InformationResponse]:
        """Fetch a specific information by its ID.

        Parameters
        ----------
        info_id : int
            The ID of the information to retrieve.

        Returns
        -------
        Optional[InformationResponse]
            The information data, or None if not found.
        """
        query = (
            Query.from_(information_table)
            .left_join(attachment_table)
            .on(attachment_table.owner_id == information_table.id)
            .select(
                information_table.id,
                information_table.content,
                information_table.information_type,
                attachment_table.midia_url,
            )
            .where(information_table.id == id)
        )
        result = run_query(self.engine, query)

        if not result:
            return None

        return self._map_row_to_response(result[0])

    def list_informations(
        self,
        info_type: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> list[InformationResponse]:
        """List informations, optionally filtered by type and/or keyword.
 
        Parameters
        ----------
        info_type : Optional[str]
            If provided, only informations of this exact type are returned.
        keyword : Optional[str]
            If provided, only informations whose content contains this
            keyword (case-insensitive substring match) are returned.
 
        Returns
        -------
        list[InformationResponse]
            The matching informations. Empty list if none match.
        """
        query = (
            Query.from_(information_table)
            .left_join(attachment_table)
            .on(attachment_table.owner_id == information_table.id)
            .select(
                information_table.id,
                information_table.content,
                information_table.information_type,
                attachment_table.midia_url,
            )
        )
 
        if info_type is not None:
            value = info_type.value if hasattr(info_type, "value") else info_type
            query = query.where(information_table.information_type == value)
 
        if keyword is not None:
            query = query.where(information_table.content.like(f"%{keyword}%"))
 
        result = run_query(self.engine, query)
 
        return [self._map_row_to_response(row) for row in result]
    
    def create_information(
        self,
        payload: InformationCreate,
        file_obj: Optional[BinaryIO] = None,
        filename: Optional[str] = None,
        content_type: str = "application/octet-stream",
    ) -> InformationResponse:
        """Create a new information record, optionally with a map/attachment.

        Parameters
        ----------
        payload : InformationCreate
            The data submitted by the administrator.
        file_obj : Optional[BinaryIO]
            The file to upload (e.g., a map image).
        filename : Optional[str]
            Original filename for the uploaded file.
        content_type : str
            MIME type of the file.

        Returns
        -------
        InformationResponse
            The newly created information data.
        """
        owner_id = self._insert_attachment_owner()

        with self.engine.connect() as conn:
            conn.execute(
                text(
                    "INSERT INTO information (id, content, information_type) "
                    "VALUES (:id, :cnt, :it)"
                ),
                {
                    "id": owner_id,
                    "cnt": payload.content,
                    "it": payload.information_type.value,
                },
            )
            conn.commit()

        attachment_url: Optional[str] = None
        if file_obj and filename:
            attachment_url = self._upload_file(
                owner_id, file_obj, filename, content_type
            )

        return InformationResponse(
            id=owner_id,
            content=payload.content,
            information_type=payload.information_type,
            attachment_url=attachment_url,
        )

    def update_information(
        self,
        info_id: int,
        payload: InformationUpdate,
        file_obj: Optional[BinaryIO] = None,
        filename: Optional[str] = None,
        content_type: str = "application/octet-stream",
    ) -> Optional[InformationResponse]:
        """Update an existing information record in the database.

        If a new file is provided, it will be uploaded to S3 and linked
        to the information, bypassing or adding to the existing attachments.

        Parameters
        ----------
        info_id : int
            The unique identifier of the information to update.
        payload : InformationUpdate
            The partial data to update (content and/or information_type).
        file_obj : Optional[BinaryIO], optional
            A new document file to upload, by default None.
        filename : Optional[str], optional
            Original filename for the new uploaded file, by default None.
        content_type : str, optional
            MIME type of the file, by default "application/octet-stream".

        Returns
        -------
        Optional[informationResponse]
            The updated information date, or None if the record was not found.

        Raises
        ------
        Exception
            If the database execution fails during the update process.
        """
        existing = self.get_information(info_id)
        if not existing:
            return None

        update_data = payload.model_dump(exclude_unset=True)

        if update_data:
            query = Query.update(information_table).where(
                information_table.id == info_id
            )

            if "content" in update_data:
                query = query.set(information_table.content, update_data["content"])
            if "information_type" in update_data:
                val = update_data["information_type"]
                query = query.set(
                    information_table.information_type,
                    val.value if hasattr(val, "value") else val,
                )

            run_query(self.engine, query)

        if file_obj and filename:
            self._upload_file(info_id, file_obj, filename, content_type)

        return self.get_information(info_id)

    def delete_information(self, info_id: int) -> bool:
        """Delete an information record and all its dependencies.

        Removes the record hierarchically: first deleting any associated
        attachments, then the main information record, and finally the
        polymorphic attachment_owner record.

        Parameters
        ----------
        info_id : int
            The unique identifier of the information to be deleted.

        Returns
        -------
        bool
            True if the deletion was successful, False if the record
            did not exist in the database.

        Raises
        ------
        Exception
            If the database execution fails during the cascading deletion.
        """
        existing = self.get_information(info_id)
        if not existing:
            return False

        try:
            del_attach = (
                Query.from_(attachment_table)
                .where(attachment_table.owner_id == info_id)
                .delete()
            )
            run_query(self.engine, del_attach)

            del_info = (
                Query.from_(information_table)
                .where(information_table.id == info_id)
                .delete()
            )
            run_query(self.engine, del_info)

            del_owner = (
                Query.from_(attachment_owner_table)
                .where(attachment_owner_table.id == info_id)
                .delete()
            )
            run_query(self.engine, del_owner)

            return True
        except Exception as e:
            raise Exception(f"Failed to delete information: {str(e)}")
