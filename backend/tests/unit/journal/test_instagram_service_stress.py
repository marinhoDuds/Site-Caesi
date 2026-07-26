import pytest
from unittest.mock import MagicMock
from src.service.instagram_management.service import InstagramService
from src.routes.journal.schemas import PostType, PostResponse
from datetime import date


@pytest.fixture
def mock_journal_service():
    service = MagicMock()
    return service


def test_hashtag_parsing_case_and_variations(mock_journal_service):
    ig_service = InstagramService(mock_journal_service)

    # Uppercase hashtags
    assert ig_service._infer_post_type("Confira o #EVENTO semat") == PostType.evento.value
    assert ig_service._infer_post_type("Nova #VAGA de estágio") == PostType.vaga.value
    assert ig_service._infer_post_type("Ótima #OPORTUNIDADE de pesquisa") == PostType.oportunidade.value

    # Multiple hashtags (evaluates #evento first, then #vaga, then #oportunidade)
    assert ig_service._infer_post_type("Post com #vaga e #evento") == PostType.evento.value

    # Substrings or plural hashtags (#vagas, #oportunidades)
    # Note: "#vagas" contains "#vaga" so it matches vaga. "#oportunidades" contains "#oportunidade" so it matches oportunidade.
    assert ig_service._infer_post_type("Temos #vagas abertas") == PostType.vaga.value
    assert ig_service._infer_post_type("Muitas #oportunidades de TCC") == PostType.oportunidade.value

    # Accented or non-ASCII characters in hashtag
    # "#oportunidâde" does NOT match "#oportunidade" exact string
    assert ig_service._infer_post_type("Nova #oportunidâde") == PostType.aviso.value


def test_extract_title_corner_cases(mock_journal_service):
    ig_service = InstagramService(mock_journal_service)

    # Non-ASCII hashtag removal: re.sub(r"#\w+", "", title) in Python 3 matches unicode letters
    caption_non_ascii_tag = "Abertas as #inscrições para monitoria\nMais detalhes..."
    title = ig_service._extract_title(caption_non_ascii_tag)
    # #inscrições is stripped, leaving double space in "Abertas as  para monitoria"
    assert title == "Abertas as  para monitoria"

    # First line with emoji and hashtag
    caption_emoji = "🚀 Inscreva-se no #evento de Computação!\nLink na bio."
    assert ig_service._extract_title(caption_emoji) == "🚀 Inscreva-se no  de Computação!"

    # Very long title > 255 chars
    long_title_caption = ("A" * 300) + "\nSegunda linha"
    extracted = ig_service._extract_title(long_title_caption)
    assert len(extracted) == 255


def test_deduplication_whitespace_and_same_batch(mock_journal_service):
    ig_service = InstagramService(mock_journal_service)

    # Existing post in DB with exact caption
    existing_post = MagicMock()
    existing_post.caption = "Legenda idêntica"
    mock_journal_service.list_posts.return_value = [existing_post]

    # Mock fetch returns post with trailing whitespace
    ig_service.fetch_instagram_posts = MagicMock(return_value=[
        {"id": "1", "caption": "Legenda idêntica \n"},
        {"id": "2", "caption": "Legenda idêntica \n"},
    ])

    mock_journal_service.create_post.side_effect = lambda p: PostResponse(
        id=10, title=p.title, post_type=p.post_type, caption=p.caption, created_at=date.today()
    )

    res = ig_service.sync_posts()
    # "Legenda idêntica \n" is NOT equal to "Legenda idêntica" (without strip), so it imports it!
    # And second item in same batch has same caption as first, so second is skipped.
    assert res["imported_count"] == 1
    assert res["skipped_count"] == 1


def test_mock_vs_live_mode(mock_journal_service, monkeypatch):
    # Test Mock Mode (default: INSTAGRAM_MOCK_MODE=true)
    monkeypatch.setenv("INSTAGRAM_MOCK_MODE", "true")
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "")
    ig_service_mock = InstagramService(mock_journal_service)
    posts_mock = ig_service_mock.fetch_instagram_posts()
    assert len(posts_mock) == 2

    # Test Live Mode (INSTAGRAM_MOCK_MODE=false with ACCESS_TOKEN)
    monkeypatch.setenv("INSTAGRAM_MOCK_MODE", "false")
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "fake_live_token")
    ig_service_live = InstagramService(mock_journal_service)
    posts_live = ig_service_live.fetch_instagram_posts()
    # Live mode Graph API call is unhandled / returns empty list []
    assert posts_live == []
