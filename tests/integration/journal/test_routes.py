from datetime import date
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.routes.journal.routes import router, get_journal_service
from src.routes.journal.schemas import (
    PublicationResponse,
    PublicationHistoryResponse,
    PublicationType,
)
from src.service.authentication.auth import get_current_admin


app = FastAPI()
app.include_router(router, prefix="/journal")

mock_service = MagicMock()


def override_get_journal_service():
    return mock_service


def override_get_current_admin():
    return {"id": 1}


app.dependency_overrides[get_journal_service] = override_get_journal_service
app.dependency_overrides[get_current_admin] = override_get_current_admin

client = TestClient(app)


def _make_publication(
    publication_id=1,
    title="Nova publicação",
    message="Mensagem de teste",
    publication_type=PublicationType.news,
    previous=None,
    attachment_url=None,
):
    return PublicationResponse(
        id=publication_id,
        title=title,
        message=message,
        publication_type=publication_type,
        publication_date=date.today(),
        last_edit=date.today(),
        previous=previous,
        attachment_url=attachment_url,
    )


def test_create_publication_route_without_attachment():
    mock_service.create_publication.return_value = _make_publication()

    response = client.post(
        "/journal/publications",
        data={
            "title": "Nova publicação",
            "message": "Mensagem de teste",
            "publication_type": "news",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["attachment_url"] is None


def test_create_publication_route_with_attachment():
    mock_service.create_publication.return_value = _make_publication(
        attachment_url="http://s3/journal/1/documento.pdf"
    )

    response = client.post(
        "/journal/publications",
        data={
            "title": "Nova publicação",
            "message": "Mensagem de teste",
            "publication_type": "news",
        },
        files={
            "attachment": (
                "documento.pdf",
                b"pdf-content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201
    assert (
        response.json()["attachment_url"]
        == "http://s3/journal/1/documento.pdf"
    )

    mock_service.create_publication.assert_called()


def test_update_publication_route():
    mock_service.get_publication.return_value = PublicationHistoryResponse(
        **_make_publication().model_dump(),
        history=[],
    )

    mock_service.update_publication.return_value = _make_publication(
        publication_id=2,
        title="Título atualizado",
        message="Mensagem atualizada",
        previous=1,
    )

    response = client.put(
        "/journal/publications/1",
        data={
            "title": "Título atualizado",
            "message": "Mensagem atualizada",
            "publication_type": "news",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == 2
    assert response.json()["previous"] == 1


def test_update_publication_route_with_new_attachment():
    mock_service.get_publication.return_value = PublicationHistoryResponse(
        **_make_publication().model_dump(),
        history=[],
    )

    mock_service.update_publication.return_value = _make_publication(
        publication_id=2,
        title="Título atualizado",
        message="Mensagem atualizada",
        previous=1,
        attachment_url="http://s3/journal/2/new.pdf",
    )

    response = client.put(
        "/journal/publications/1",
        data={
            "title": "Título atualizado",
            "message": "Mensagem atualizada",
            "publication_type": "news",
        },
        files={
            "attachment": (
                "new.pdf",
                b"new-content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["attachment_url"]
        == "http://s3/journal/2/new.pdf"
    )


def test_update_publication_not_found():
    mock_service.get_publication.return_value = None

    response = client.put(
        "/journal/publications/999",
        data={
            "title": "Teste",
            "message": "Mensagem",
            "publication_type": "news",
        },
    )

    assert response.status_code == 404


def test_list_publications_route():
    mock_service.list_publications.return_value = [
        _make_publication(),
    ]

    response = client.get("/journal/publications")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_publications_route_with_filter():
    mock_service.list_publications.return_value = [
        _make_publication()
    ]

    response = client.get(
        "/journal/publications?publication_type=news"
    )

    assert response.status_code == 200

    mock_service.list_publications.assert_called_with(
        PublicationType.news
    )


def test_get_publication_route():
    mock_service.get_publication.return_value = (
        PublicationHistoryResponse(
            **_make_publication().model_dump(),
            history=[],
        )
    )

    response = client.get("/journal/publications/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["history"] == []


def test_get_publication_not_found():
    mock_service.get_publication.return_value = None

    response = client.get("/journal/publications/999")

    assert response.status_code == 404


def test_delete_publication_route():
    mock_service.delete_publication.return_value = True

    response = client.delete("/journal/publications/1")

    assert response.status_code == 204

    mock_service.delete_publication.assert_called_once_with(1)


def test_delete_publication_not_found():
    mock_service.delete_publication.return_value = False

    response = client.delete("/journal/publications/999")

    assert response.status_code == 404


def test_search_publications_route():
    mock_service.search_publications.return_value = [
        _make_publication(title="Semana Acadêmica")
    ]

    response = client.get(
        "/journal/publications/search?query=Semana"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1

    mock_service.search_publications.assert_called_with("Semana")


def test_sort_publications_by_title():
    mock_service.list_publications.return_value = [
        _make_publication(title="A"),
        _make_publication(publication_id=2, title="B"),
    ]

    response = client.get(
        "/journal/publications?sort_by=title"
    )

    assert response.status_code == 200

    mock_service.list_publications.assert_called_with(
        sort_by="title"
    )


def test_sort_publications_by_date():
    mock_service.list_publications.return_value = [
        _make_publication()
    ]

    response = client.get(
        "/journal/publications?sort_by=publication_date"
    )

    assert response.status_code == 200

    mock_service.list_publications.assert_called_with(
        sort_by="publication_date"
    )