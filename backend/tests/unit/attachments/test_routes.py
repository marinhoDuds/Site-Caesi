from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from io import BytesIO

from src.routes.attachments import router, admin_router, get_attachment_service
from src.service.authentication.auth import get_current_admin
from src.service.attachment_service import Attachment

app = FastAPI()
app.include_router(router)
app.include_router(admin_router)

mock_service = MagicMock()

def override_service():
    return mock_service

def override_admin():
    return {"id": "1"}

app.dependency_overrides[get_attachment_service] = override_service
app.dependency_overrides[get_current_admin] = override_admin

client = TestClient(app)


def test_upload_attachment_with_owner():
    mock_service.upload.return_value = Attachment(1, 10, "key", "test.txt", "text/plain")
    res = client.post(
        "/admin/attachments/10",
        files={"attachment": ("test.txt", b"hello world", "text/plain")}
    )
    assert res.status_code == 201
    assert res.json()["id"] == 1


def test_upload_attachment_generic():
    mock_service.create_owner.return_value = 20
    mock_service.upload.return_value = Attachment(2, 20, "key2", "test.txt", "text/plain")
    res = client.post(
        "/admin/attachments/upload",
        files={"attachment": ("test.txt", b"hello world", "text/plain")}
    )
    assert res.status_code == 201
    assert res.json()["id"] == 2


def test_download_attachment_success():
    mock_service.get.return_value = Attachment(1, 10, "key", "test.txt", "text/plain")
    mock_service.open.return_value = {"Body": BytesIO(b"file content")}

    res = client.get("/attachments/1")
    assert res.status_code == 200
    assert res.content == b"file content"


def test_download_attachment_not_found():
    mock_service.get.return_value = None
    res = client.get("/attachments/999")
    assert res.status_code == 404


def test_delete_attachment_success():
    mock_service.delete.return_value = True
    res = client.delete("/admin/attachments/1")
    assert res.status_code == 204


def test_delete_attachment_not_found():
    mock_service.delete.return_value = False
    res = client.delete("/admin/attachments/999")
    assert res.status_code == 404
