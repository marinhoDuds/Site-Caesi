from unittest.mock import MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.routes.informations.routes import router, get_information_service
from src.service.authentication.auth import get_current_admin
from src.routes.informations.schemas import InformationResponse, InformationTypeEnum

app = FastAPI()
app.include_router(router, prefix="/admin")

mock_service = MagicMock()


def override_get_service():
    return mock_service


def override_get_current_admin():
    return {"id": 1, "name": "Admin Caesi", "role": "admin"}


app.dependency_overrides[get_information_service] = override_get_service
app.dependency_overrides[get_current_admin] = override_get_current_admin

client = TestClient(app)


def _make_info(
    info_id=1,
    content="Aviso geral para a comunidade.",
    info_type=InformationTypeEnum.announcements,
    attachment_url=None,
) -> InformationResponse:
    return InformationResponse(
        id=info_id,
        content=content,
        information_type=info_type,
        attachment_url=attachment_url,
    )


def test_create_information_route_without_file():
    mock_service.create_information.return_value = _make_info(
        content="Novo Laboratório de Redes",
        info_type=InformationTypeEnum.laboratories
    )

    response = client.post(
        "/admin/informations",
        data={
            "content": "Novo Laboratório de Redes",
            "information_type": "laboratories"
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["content"] == "Novo Laboratório de Redes"
    assert response.json()["information_type"] == "laboratories"
    assert response.json()["attachment_url"] is None


def test_create_information_route_with_file():
    mock_service.create_information.return_value = _make_info(
        attachment_url="http://s3/information/1/mapa.pdf"
    )

    response = client.post(
        "/admin/informations",
        data={
            "content": "Aviso geral para a comunidade.",
            "information_type": "announcements"
        },
        files={"attachment": ("mapa.pdf", b"pdf-bytes", "application/pdf")},
    )

    assert response.status_code == 201
    assert response.json()["attachment_url"] == "http://s3/information/1/mapa.pdf"
    mock_service.create_information.assert_called()


def test_update_information_route():
    mock_service.update_information.return_value = _make_info(
        info_id=5,
        content="Conteúdo Editado",
        info_type=InformationTypeEnum.map
    )

    response = client.patch(
        "/admin/informations/5",
        data={
            "content": "Conteúdo Editado",
            "information_type": "map"
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == 5
    assert response.json()["content"] == "Conteúdo Editado"
    assert response.json()["attachment_url"] is None


def test_update_information_route_with_new_file():
    mock_service.update_information.return_value = _make_info(
        info_id=5,
        content="Aviso com novo anexo",
        attachment_url="http://s3/information/5/novo_anexo.pdf"
    )

    response = client.patch(
        "/admin/informations/5",
        data={
            "content": "Aviso com novo anexo",
            "information_type": "announcements"
        },
        files={"attachment": ("novo_anexo.pdf", b"new-pdf-bytes", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["attachment_url"] == "http://s3/information/5/novo_anexo.pdf"


def test_update_information_not_found():
    mock_service.update_information.return_value = None

    response = client.patch(
        "/admin/informations/999",
        data={
            "content": "Tentando atualizar fantasma",
            "information_type": "professors"
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Information not found"


def test_delete_information_route():
    mock_service.delete_information.return_value = True

    response = client.delete("/admin/informations/10")

    assert response.status_code == 204
    assert not response.content 


def test_delete_information_not_found():
    mock_service.delete_information.return_value = False

    response = client.delete("/admin/informations/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Information not found"