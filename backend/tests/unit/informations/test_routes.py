import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.routes.informations.routes import get_information_service
from src.service.authentication.auth import get_current_admin

client = TestClient(app)

class MockInformationService:
    def get_informations_by_type(self, info_type):
        return [{"id": 1, "information_type": info_type, "content": '{"test":"data"}'}]
        
    def create_information(self, info_type, content):
        return {"id": 1, "information_type": info_type, "content": content}
        
    def update_information(self, info_id, info_type, content):
        if info_id == 999:
            return None
        return {"id": info_id, "information_type": info_type, "content": content}
        
    def get_information_by_id(self, info_id):
        if info_id == 999:
            return None
        return {"id": info_id, "information_type": "test", "content": "{}"}
        
    def delete_information(self, info_id):
        return True

def override_get_service():
    return MockInformationService()

def override_get_admin():
    return {"sub": "admin"}

app.dependency_overrides[get_information_service] = override_get_service
app.dependency_overrides[get_current_admin] = override_get_admin

def test_get_informations_by_type():
    response = client.get("/informations/type/professors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["information_type"] == "professors"

def test_create_information():
    response = client.post("/admin/informations/", json={
        "information_type": "laboratories",
        "content": '{"name": "LSD"}'
    })
    assert response.status_code == 201
    assert response.json()["information_type"] == "laboratories"

def test_update_information():
    response = client.put("/admin/informations/1", json={
        "information_type": "laboratories",
        "content": '{"name": "LSD2"}'
    })
    assert response.status_code == 200
    assert response.json()["content"] == '{"name": "LSD2"}'

def test_update_information_not_found():
    response = client.put("/admin/informations/999", json={
        "information_type": "laboratories",
        "content": '{"name": "LSD2"}'
    })
    assert response.status_code == 404

def test_delete_information():
    response = client.delete("/admin/informations/1")
    assert response.status_code == 204

def test_delete_information_not_found():
    response = client.delete("/admin/informations/999")
    assert response.status_code == 404
