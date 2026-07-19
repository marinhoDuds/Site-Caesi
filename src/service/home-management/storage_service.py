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

    def deletar_foto(self, foto_url: str) -> None:
        """Remove an admin's photo from the bucket.

        Parameters
        ----------
        foto_url : str
            The URL of the photo to remove.
        """