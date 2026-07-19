from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from src.service.home_management.storage_service import StorageService

MODULE = "src.service.home_management.storage_service"


class TestUploadFoto:
    def test_retorna_url_publica_no_sucesso(self):
        service = StorageService()

        with patch(
            f"{MODULE}.upload_fileobj_to_s3",
            return_value="http://s3.local/bucket/admins/1.jpg",
        ) as mock_upload:
            url = service.upload_foto(1, b"fake-image-bytes")

        assert url == "http://s3.local/bucket/admins/1.jpg"
        mock_upload.assert_called_once()

    def test_usa_o_admin_id_para_nomear_o_objeto(self):
        service = StorageService()

        with patch(
            f"{MODULE}.upload_fileobj_to_s3", return_value="http://s3.local/x"
        ) as mock_upload:
            service.upload_foto(42, b"fake-image-bytes")

        _, object_name = mock_upload.call_args.args[:2]
        assert "42" in object_name

    def test_levanta_erro_quando_upload_falha(self):
        service = StorageService()

        with patch(f"{MODULE}.upload_fileobj_to_s3", return_value=None):
            with pytest.raises(ValueError):
                service.upload_foto(1, b"fake-image-bytes")


class TestDeletarFoto:
    def test_chama_delete_object_com_bucket_e_key_corretos(self, monkeypatch):
        monkeypatch.setenv("GARAGE_DEFAULT_BUCKET", "meu-bucket")
        mock_client = MagicMock()
        service = StorageService()

        with patch(f"{MODULE}.get_s3_client", return_value=mock_client):
            service.deletar_foto("http://s3.local/meu-bucket/admins/1.jpg")

        mock_client.delete_object.assert_called_once_with(
            Bucket="meu-bucket", Key="admins/1.jpg"
        )

    def test_levanta_erro_quando_bucket_nao_configurado(self, monkeypatch):
        monkeypatch.delenv("GARAGE_DEFAULT_BUCKET", raising=False)
        service = StorageService()

        with pytest.raises(ValueError):
            service.deletar_foto("http://s3.local/meu-bucket/admins/1.jpg")

    def test_levanta_erro_quando_s3_falha(self, monkeypatch):
        monkeypatch.setenv("GARAGE_DEFAULT_BUCKET", "meu-bucket")
        mock_client = MagicMock()
        mock_client.delete_object.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "boom"}}, "DeleteObject"
        )
        service = StorageService()

        with patch(f"{MODULE}.get_s3_client", return_value=mock_client):
            with pytest.raises(ValueError):
                service.deletar_foto("http://s3.local/meu-bucket/admins/1.jpg")
