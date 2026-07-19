import io
import logging
import os

from botocore.exceptions import ClientError

from ..s3 import get_s3_client, upload_fileobj_to_s3

logger = logging.getLogger(__name__)


class StorageService:
    """Handle upload and removal of admin photos in the bucket."""

    def upload_foto(self, admin_id: int, foto_bytes: bytes) -> str:
        """Upload an admin's photo to the bucket.

        Parameters
        ----------
        admin_id : int
            The unique identifier of the admin, used to name the file.
        foto_bytes : bytes
            The raw bytes of the photo to upload.

        Returns
        -------
        str
            The public URL of the uploaded photo.
        """
        object_name = f"admins/{admin_id}.jpg"
        foto_url = upload_fileobj_to_s3(
            io.BytesIO(foto_bytes), object_name, content_type="image/jpeg"
        )

        if foto_url is None:
            raise ValueError(f"Failed to upload photo for admin {admin_id}.")

        return foto_url

    def deletar_foto(self, foto_url: str) -> None:
        """Remove an admin's photo from the bucket.

        Parameters
        ----------
        foto_url : str
            The URL of the photo to remove.
        """
        bucket_name = os.getenv("GARAGE_DEFAULT_BUCKET")
        if not bucket_name:
            raise ValueError("GARAGE_DEFAULT_BUCKET env var is not set.")

        object_name = foto_url.rsplit(f"/{bucket_name}/", 1)[-1]
        client = get_s3_client()

        try:
            client.delete_object(Bucket=bucket_name, Key=object_name)
        except ClientError as e:
            logger.error(f"Failed to delete photo from S3: {e}")
            raise ValueError(f"Failed to delete photo '{foto_url}'.") from e
