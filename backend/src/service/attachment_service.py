"""Private S3-backed attachment persistence."""
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Optional
from uuid import uuid4

from sqlalchemy import Engine, text

from src.service.s3 import delete_file_from_s3, get_file_from_s3, upload_fileobj_to_s3


@dataclass(frozen=True)
class Attachment:
    id: int
    owner_id: int
    object_key: str
    filename: str
    content_type: str


class AttachmentService:
    """Stores attachment bytes in S3 and metadata in the relational database."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def reassign_owner(self, attachment_ids: list[int], new_owner_id: int) -> None:
        """Reassign attachment records to a new owner ID."""
        if not attachment_ids:
            return
        params = {"owner_id": new_owner_id}
        placeholders = []
        for i, aid in enumerate(attachment_ids):
            key = f"id_{i}"
            placeholders.append(f":{key}")
            params[key] = aid

        with self.engine.connect() as connection:
            connection.execute(
                text(f"UPDATE attachment SET owner_id = :owner_id WHERE id IN ({','.join(placeholders)})"),
                params,
            )
            connection.commit()

    def create_owner(self, owner_type: str = "information") -> int:
        """Create a record in attachment_owner table and return its generated ID."""
        with self.engine.connect() as connection:
            connection.execute(
                text("INSERT INTO attachment_owner (owner_type) VALUES (:t)"),
                {"t": owner_type},
            )
            owner_id = connection.execute(text("SELECT LAST_INSERT_ID()")).scalar_one()
            connection.commit()
        return int(owner_id or 0)

    def upload(
        self,
        owner_id: int,
        file_obj: BinaryIO,
        filename: str,
        content_type: str,
    ) -> Attachment:
        """Upload a file and associate it with an existing attachment owner."""
        safe_name = Path(filename).name or "file"
        object_key = f"attachments/{owner_id}/{uuid4().hex}-{safe_name}"
        if not upload_fileobj_to_s3(file_obj, object_key, content_type):
            raise RuntimeError("Unable to upload attachment to object storage.")

        try:
            with self.engine.connect() as connection:
                connection.execute(
                    text(
                        "INSERT INTO attachment "
                        "(owner_id, object_key, filename, content_type) "
                        "VALUES (:owner_id, :object_key, :filename, :content_type)"
                    ),
                    {
                        "owner_id": owner_id,
                        "object_key": object_key,
                        "filename": safe_name,
                        "content_type": content_type,
                    },
                )
                attachment_id = connection.execute(text("SELECT LAST_INSERT_ID()")).scalar_one()
                connection.commit()
        except Exception:
            delete_file_from_s3(object_key)
            raise

        return Attachment(int(attachment_id), owner_id, object_key, safe_name, content_type)

    def get(self, attachment_id: int) -> Optional[Attachment]:
        with self.engine.connect() as connection:
            row = connection.execute(
                text(
                    "SELECT id, owner_id, object_key, filename, content_type "
                    "FROM attachment WHERE id = :id"
                ),
                {"id": attachment_id},
            ).first()
        return Attachment(*row) if row else None

    def list_for_owner(self, owner_id: int) -> list[Attachment]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT id, owner_id, object_key, filename, content_type "
                    "FROM attachment WHERE owner_id = :owner_id ORDER BY id"
                ),
                {"owner_id": owner_id},
            ).all()
        return [Attachment(*row) for row in rows]

    def delete(self, attachment_id: int) -> bool:
        attachment = self.get(attachment_id)
        if not attachment:
            return False
        if not delete_file_from_s3(attachment.object_key):
            return False
        with self.engine.connect() as connection:
            connection.execute(text("DELETE FROM attachment WHERE id = :id"), {"id": attachment_id})
            connection.commit()
        return True

    def delete_for_owner(self, owner_id: int) -> None:
        """Remove every object and metadata record associated with an owner."""
        for attachment in self.list_for_owner(owner_id):
            if not self.delete(attachment.id):
                raise RuntimeError(f"Unable to delete attachment {attachment.id}")

    def open(self, attachment: Attachment) -> Optional[dict]:
        """Get the private object stream for an already-authorized attachment."""
        return get_file_from_s3(attachment.object_key)
