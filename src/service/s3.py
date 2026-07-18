import os
import boto3
from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client
from typing import BinaryIO, Optional
import logging

logger = logging.getLogger(__name__)


def get_s3_client() -> S3Client:
    """Initialize and return a configured boto3 client for Garage S3."""
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
        aws_access_key_id=os.getenv("GARAGE_DEFAULT_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("GARAGE_DEFAULT_SECRET_KEY"),
        region_name=os.getenv("AWS_REGION", "garage"),
    )


def upload_fileobj_to_s3(
    file_obj: BinaryIO,
    object_name: str,
    content_type: str = "application/octet-stream",
) -> Optional[str]:
    """Upload a file to the S3 bucket.

    Parameters
    ----------
    file_obj : BinaryIO
        The file or bytes to upload.
    object_name : str
        The object key in the bucket.
    content_type : str
        The mime-type of the file.

    Returns
    -------
    Optional[str]
        The public URL or object key on success, None on error.
    """
    bucket_name = os.getenv("GARAGE_DEFAULT_BUCKET")
    if not bucket_name:
        raise ValueError("GARAGE_DEFAULT_BUCKET env var is not set.")

    client = get_s3_client()

    try:
        client.upload_fileobj(
            file_obj,
            bucket_name,
            object_name,
            ExtraArgs={"ContentType": content_type},
        )

        endpoint = os.getenv("AWS_ENDPOINT_URL", "").rstrip("/")
        if endpoint:
            return f"{endpoint}/{bucket_name}/{object_name}"

        return object_name

    except ClientError as e:
        logger.error(f"Failed to upload to S3: {e}")
        return None


def generate_presigned_url(object_name: str, expiration: int = 3600) -> Optional[str]:
    """Generate a temporary URL to download a private file.

    Parameters
    ----------
    object_name : str
        The object key in the bucket.
    expiration : int
        Time in seconds until the URL expires.

    Returns
    -------
    Optional[str]
        The presigned URL on success, None on error.
    """
    bucket_name = os.getenv("GARAGE_DEFAULT_BUCKET")
    client = get_s3_client()

    try:
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_name},
            ExpiresIn=expiration,
        )
    except ClientError as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        return None
