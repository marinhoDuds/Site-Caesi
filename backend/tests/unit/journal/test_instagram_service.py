import pytest
from unittest.mock import MagicMock
from src.service.instagram_management.service import InstagramService
from src.routes.journal.schemas import PostType, PostResponse
from datetime import date


@pytest.fixture
def mock_journal_service():
    service = MagicMock()
    return service


def test_infer_post_type(mock_journal_service):
    ig_service = InstagramService(mock_journal_service)
    assert (
        ig_service._infer_post_type("Confira o #evento semat") == PostType.evento.value
    )
    assert ig_service._infer_post_type("Nova #vaga de estágio") == PostType.vaga.value
    assert (
        ig_service._infer_post_type("Ótima #oportunidade de pesquisa")
        == PostType.oportunidade.value
    )
    assert (
        ig_service._infer_post_type("Apenas um #aviso normal") == PostType.aviso.value
    )


def test_extract_title(mock_journal_service):
    ig_service = InstagramService(mock_journal_service)
    caption = "📢 Novo Edital da Monitoria!\nConfira todos os detalhes..."
    assert ig_service._extract_title(caption) == "📢 Novo Edital da Monitoria!"

    caption_empty = "\n\n  \n"
    assert ig_service._extract_title(caption_empty) == "Publicação do Instagram"


def test_sync_posts_deduplication(mock_journal_service):
    ig_service = InstagramService(mock_journal_service)

    # Initial sync
    mock_journal_service.list_posts.return_value = []
    mock_journal_service.create_post.side_effect = lambda payload: PostResponse(
        id=1,
        title=payload.title,
        post_type=payload.post_type,
        caption=payload.caption,
        created_at=date.today(),
    )

    res1 = ig_service.sync_posts()
    assert res1["imported_count"] == 2
    assert res1["skipped_count"] == 0

    # Second sync where posts already exist in journal_service
    existing_posts = res1["posts"]
    mock_journal_service.list_posts.return_value = existing_posts

    res2 = ig_service.sync_posts()
    assert res2["imported_count"] == 0
    assert res2["skipped_count"] == 2


def test_fetch_instagram_posts_missing_credentials(mock_journal_service, monkeypatch):
    monkeypatch.setenv("INSTAGRAM_MOCK_MODE", "false")
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "")
    monkeypatch.setenv("INSTAGRAM_ACCOUNT_ID", "")

    ig_service = InstagramService(mock_journal_service)
    posts = ig_service.fetch_instagram_posts()
    assert posts == []


def test_fetch_instagram_posts_http_success(mock_journal_service, monkeypatch):
    import json
    from unittest.mock import patch, MagicMock

    monkeypatch.setenv("INSTAGRAM_MOCK_MODE", "false")
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "valid_token")
    monkeypatch.setenv("INSTAGRAM_ACCOUNT_ID", "123456")

    mock_response = MagicMock()
    mock_response.status = 200
    mock_payload = {
        "data": [
            {
                "id": "ig_999",
                "caption": "Post de teste #evento",
                "media_url": "https://example.com/ig_999.jpg",
                "timestamp": "2026-07-26T00:00:00Z",
            }
        ]
    }
    mock_response.read.return_value = json.dumps(mock_payload).encode("utf-8")
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
        ig_service = InstagramService(mock_journal_service)
        posts = ig_service.fetch_instagram_posts()
        assert len(posts) == 1
        assert posts[0]["id"] == "ig_999"
        mock_urlopen.assert_called_once()


def test_fetch_instagram_posts_http_error(mock_journal_service, monkeypatch):
    import urllib.error
    from unittest.mock import patch

    monkeypatch.setenv("INSTAGRAM_MOCK_MODE", "false")
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "valid_token")
    monkeypatch.setenv("INSTAGRAM_ACCOUNT_ID", "123456")

    error = urllib.error.HTTPError(
        "http://graph.facebook.com", 400, "Bad Request", {}, None
    )
    with patch("urllib.request.urlopen", side_effect=error):
        ig_service = InstagramService(mock_journal_service)
        posts = ig_service.fetch_instagram_posts()
        assert posts == []


def test_fetch_instagram_posts_url_error(mock_journal_service, monkeypatch):
    import urllib.error
    from unittest.mock import patch

    monkeypatch.setenv("INSTAGRAM_MOCK_MODE", "false")
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "valid_token")
    monkeypatch.setenv("INSTAGRAM_ACCOUNT_ID", "123456")

    error = urllib.error.URLError("Connection timed out")
    with patch("urllib.request.urlopen", side_effect=error):
        ig_service = InstagramService(mock_journal_service)
        posts = ig_service.fetch_instagram_posts()
        assert posts == []


def test_fetch_instagram_posts_json_error(mock_journal_service, monkeypatch):
    from unittest.mock import patch, MagicMock

    monkeypatch.setenv("INSTAGRAM_MOCK_MODE", "false")
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "valid_token")
    monkeypatch.setenv("INSTAGRAM_ACCOUNT_ID", "123456")

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = b"invalid json content {"
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response):
        ig_service = InstagramService(mock_journal_service)
        posts = ig_service.fetch_instagram_posts()
        assert posts == []
