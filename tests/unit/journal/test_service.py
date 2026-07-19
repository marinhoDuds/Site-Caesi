import pytest
from datetime import date
from io import BytesIO
from unittest.mock import MagicMock, patch

from src.service.journal.service import JournalService
from src.routes.journal.schemas import (
    PublicationCreate,
    PublicationType,
)


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def journal_service(mock_engine):
    return JournalService(engine=mock_engine)


def _make_row(
    publication_id=1,
    publication_date=None,
    title="Nova publicação",
    message="Mensagem de teste",
    publication_type=PublicationType.news,
    previous=None,
    attachment_url=None,
):
    return (
        publication_id,
        publication_date or date.today(),
        date.today(),  # last_edit
        title,
        message,
        publication_type,
        previous,
        attachment_url,
    )


def test_create_publication_without_attachment(
    journal_service,
    mock_engine,
):
    payload = PublicationCreate(
        title="Semana Acadêmica",
        message="Inscrições abertas.",
        publication_type=PublicationType.news,
    )

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value.scalar.return_value = 1
    mock_engine.connect.return_value = mock_conn

    result = journal_service.create_publication(payload)

    assert result.id == 1
    assert result.title == "Semana Acadêmica"
    assert result.message == "Inscrições abertas."
    assert result.previous is None
    assert result.attachment_url is None


def test_create_publication_with_attachment(
    journal_service,
    mock_engine,
):
    payload = PublicationCreate(
        title="Edital",
        message="Confira o edital.",
        publication_type=PublicationType.notice,
    )

    file_obj = BytesIO(b"pdf-content")

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value.scalar.return_value = 2
    mock_engine.connect.return_value = mock_conn

    with patch(
        "src.service.journal.service.upload_fileobj_to_s3"
    ) as mock_upload:

        mock_upload.return_value = (
            "http://s3/journal/2/edital.pdf"
        )

        with patch(
            "src.service.journal.service.run_query"
        ) as mock_run:

            mock_run.return_value = None

            result = journal_service.create_publication(
                payload,
                file_obj=file_obj,
                filename="edital.pdf",
                content_type="application/pdf",
            )

    assert result.id == 2
    assert (
        result.attachment_url
        == "http://s3/journal/2/edital.pdf"
    )

    mock_upload.assert_called_once()


def test_update_publication_keep_attachment(
    journal_service,
    mock_engine,
):
    payload = PublicationCreate(
        title="Evento atualizado",
        message="Nova data.",
        publication_type=PublicationType.event,
    )

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value.scalar.return_value = 3
    mock_engine.connect.return_value = mock_conn

    with patch(
        "src.service.journal.service.run_query"
    ) as mock_run:

        mock_run.return_value = [
            ("http://s3/journal/1/evento.pdf",)
        ]

        result = journal_service.update_publication(
            previous_id=1,
            payload=payload,
        )

    assert result.id == 3
    assert result.previous == 1

    assert (
        result.attachment_url
        == "http://s3/journal/1/evento.pdf"
    )


def test_update_publication_with_new_attachment(
    journal_service,
    mock_engine,
):
    payload = PublicationCreate(
        title="Evento atualizado",
        message="Arquivo atualizado.",
        publication_type=PublicationType.event,
    )

    file_obj = BytesIO(b"new-pdf")

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value.scalar.return_value = 4
    mock_engine.connect.return_value = mock_conn

    with patch(
        "src.service.journal.service.upload_fileobj_to_s3"
    ) as mock_upload:

        mock_upload.return_value = (
            "http://s3/journal/4/new.pdf"
        )

        with patch(
            "src.service.journal.service.run_query"
        ) as mock_run:

            mock_run.return_value = None

            result = journal_service.update_publication(
                previous_id=1,
                payload=payload,
                file_obj=file_obj,
                filename="new.pdf",
                content_type="application/pdf",
            )

    assert result.id == 4
    assert result.previous == 1

    assert (
        result.attachment_url
        == "http://s3/journal/4/new.pdf"
    )


def test_get_publication_not_found(
    journal_service,
    mock_engine,
):
    with patch(
        "src.service.journal.service.run_query"
    ) as mock_run:

        mock_run.return_value = []

        result = journal_service.get_publication(
            publication_id=99
        )

    assert result is None


def test_get_publication_history(
    journal_service,
    mock_engine,
):
    with patch(
        "src.service.journal.service.run_query"
    ) as mock_run:

        mock_run.side_effect = [
            [
                _make_row(
                    publication_id=2,
                    title="Versão 2",
                    previous=1,
                )
            ],
            [
                _make_row(
                    publication_id=1,
                    title="Versão 1",
                )
            ],
        ]

        result = journal_service.get_publication(
            publication_id=2
        )

    assert result.id == 2
    assert len(result.history) == 1
    assert result.history[0].id == 1


def test_list_publications_no_filter(
    journal_service,
    mock_engine,
):
    with patch(
        "src.service.journal.service.run_query"
    ) as mock_run:

        mock_run.return_value = [
            _make_row(publication_id=1),
            _make_row(
                publication_id=2,
                previous=1,
            ),
        ]

        results = journal_service.list_publications()

    assert len(results) == 2


def test_list_publications_with_filter(
    journal_service,
    mock_engine,
):
    with patch(
        "src.service.journal.service.run_query"
    ) as mock_run:

        mock_run.return_value = [
            _make_row(
                publication_type=PublicationType.news
            )
        ]

        results = journal_service.list_publications(
            publication_type=PublicationType.news
        )

    assert len(results) == 1
    assert (
        results[0].publication_type
        == PublicationType.news
    )


def test_list_publications_empty(
    journal_service,
    mock_engine,
):
    with patch(
        "src.service.journal.service.run_query"
    ) as mock_run:

        mock_run.return_value = []

        results = journal_service.list_publications()

    assert results == []


def test_search_publications(
    journal_service,
    mock_engine,
):
    with patch(
        "src.service.journal.service.run_query"
    ) as mock_run:

        mock_run.return_value = [
            _make_row(title="Semana Acadêmica")
        ]

        results = journal_service.search_publications(
            "Semana"
        )

    assert len(results) == 1
    assert results[0].title == "Semana Acadêmica"


def test_delete_publication(
    journal_service,
    mock_engine,
):
    with patch(
        "src.service.journal.service.run_query"
    ) as mock_run:

        mock_run.return_value = [(1,)]

        result = journal_service.delete_publication(
            publication_id=1
        )

    assert result is True


def test_delete_publication_not_found(
    journal_service,
    mock_engine,
):
    with patch(
        "src.service.journal.service.run_query"
    ) as mock_run:

        mock_run.return_value = []

        result = journal_service.delete_publication(
            publication_id=99
        )

    assert result is False