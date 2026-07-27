import pytest
from io import BytesIO
from unittest.mock import MagicMock, patch

from src.service.s3 import upload_fileobj_to_s3, generate_presigned_url


class TestUploadFileobjToS3:
    def test_upload_returns_object_key_when_endpoint_set(self, monkeypatch):
        monkeypatch.setenv("GARAGE_DEFAULT_BUCKET", "test-bucket")
        monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:3900")

        mock_client = MagicMock()

        with patch("src.service.s3.get_s3_client", return_value=mock_client):
            result = upload_fileobj_to_s3(
                BytesIO(b"data"),
                "portal/1/file.pdf",
                "application/pdf",
            )

        assert result == "portal/1/file.pdf"
        mock_client.upload_fileobj.assert_called_once()

    def test_upload_returns_object_name_when_no_endpoint(self, monkeypatch):
        monkeypatch.setenv("GARAGE_DEFAULT_BUCKET", "test-bucket")
        monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)

        mock_client = MagicMock()

        with patch("src.service.s3.get_s3_client", return_value=mock_client):
            result = upload_fileobj_to_s3(BytesIO(b"data"), "portal/1/file.pdf")

        assert result == "portal/1/file.pdf"

    def test_upload_returns_none_on_client_error(self, monkeypatch):
        from botocore.exceptions import ClientError

        monkeypatch.setenv("GARAGE_DEFAULT_BUCKET", "test-bucket")
        monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:3900")

        mock_client = MagicMock()
        mock_client.upload_fileobj.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "Internal Error"}}, "upload_fileobj"
        )

        with patch("src.service.s3.get_s3_client", return_value=mock_client):
            result = upload_fileobj_to_s3(BytesIO(b"data"), "portal/1/file.pdf")

        assert result is None

    def test_upload_raises_when_bucket_not_set(self, monkeypatch):
        monkeypatch.delenv("GARAGE_DEFAULT_BUCKET", raising=False)

        with pytest.raises(ValueError, match="GARAGE_DEFAULT_BUCKET"):
            upload_fileobj_to_s3(BytesIO(b"data"), "some/key")

    def test_upload_strips_trailing_slash_from_endpoint(self, monkeypatch):
        monkeypatch.setenv("GARAGE_DEFAULT_BUCKET", "bucket")
        monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:3900/")

        mock_client = MagicMock()

        with patch("src.service.s3.get_s3_client", return_value=mock_client):
            result = upload_fileobj_to_s3(BytesIO(b"x"), "key.txt")

        assert "//" not in result.replace("http://", "")


class TestGeneratePresignedUrl:
    def test_returns_presigned_url_on_success(self, monkeypatch):
        monkeypatch.setenv("GARAGE_DEFAULT_BUCKET", "test-bucket")

        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = (
            "http://localhost:3900/test-bucket/key.pdf?token=abc"
        )

        with patch("src.service.s3.get_s3_client", return_value=mock_client):
            result = generate_presigned_url("key.pdf", expiration=3600)

        assert result == "http://localhost:3900/test-bucket/key.pdf?token=abc"
        mock_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "key.pdf"},
            ExpiresIn=3600,
        )

    def test_returns_none_on_client_error(self, monkeypatch):
        from botocore.exceptions import ClientError

        monkeypatch.setenv("GARAGE_DEFAULT_BUCKET", "test-bucket")

        mock_client = MagicMock()
        mock_client.generate_presigned_url.side_effect = ClientError(
            {"Error": {"Code": "403", "Message": "Forbidden"}},
            "generate_presigned_url",
        )

        with patch("src.service.s3.get_s3_client", return_value=mock_client):
            result = generate_presigned_url("key.pdf")

        assert result is None

    def test_raises_when_bucket_not_set(self, monkeypatch):
        monkeypatch.delenv("GARAGE_DEFAULT_BUCKET", raising=False)

        with pytest.raises(ValueError, match="GARAGE_DEFAULT_BUCKET"):
            generate_presigned_url("key.pdf")
