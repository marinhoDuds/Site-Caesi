import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import Engine
from datetime import date

from src.service.journal_management.service import JournalService
from src.routes.journal.schemas import PostCreate, PostUpdate, PostType

@pytest.fixture
def mock_engine():
    engine = MagicMock(spec=Engine)
    engine.dialect = MagicMock()
    engine.dialect.name = "mysql"
    conn = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn
    
    
    conn.execute.return_value.scalar.return_value = 1
    return engine

def test_create_post(mock_engine):
    service = JournalService(mock_engine)
    payload = PostCreate(
        title="Test Post",
        post_type=PostType.aviso,
        caption="This is a test post caption.",
    )
    
    post = service.create_post(payload)
    
    assert post.id == 1
    assert post.title == "Test Post"
    assert post.post_type == "aviso"
    assert post.caption == "This is a test post caption."
    assert post.created_at == date.today()

def test_create_post_mysql(mock_engine):
    mock_engine.dialect.name = "mysql"
    service = JournalService(mock_engine)
    payload = PostCreate(
        title="Test Post",
        post_type=PostType.aviso,
        caption="This is a test post caption.",
    )
    post = service.create_post(payload)
    assert post.id == 1

def test_get_post(mock_engine):
    service = JournalService(mock_engine)
    with patch("src.service.journal_management.service.run_query") as mock_run_query:
        
        mock_run_query.return_value = [(1, "Title", "aviso", date(2024, 1, 1), None, "Caption")]
        
        post = service.get_post(1)
        
        assert post is not None
        assert post.id == 1
        assert post.title == "Title"
        assert post.created_at == date(2024, 1, 1)

def test_get_post_not_found(mock_engine):
    service = JournalService(mock_engine)
    with patch("src.service.journal_management.service.run_query") as mock_run_query:
        mock_run_query.return_value = []
        post = service.get_post(999)
        assert post is None

def test_list_posts(mock_engine):
    service = JournalService(mock_engine)
    with patch("src.service.journal_management.service.run_query") as mock_run_query:
        mock_run_query.return_value = [
            (1, "Title 1", "aviso", date(2024, 1, 1), None, "Caption 1"),
            (2, "Title 2", "evento", date(2024, 1, 2), None, "Caption 2")
        ]
        
        posts = service.list_posts()
        assert len(posts) == 2
        assert posts[0].id == 1
        assert posts[1].id == 2

def test_list_posts_with_filter(mock_engine):
    service = JournalService(mock_engine)
    with patch("src.service.journal_management.service.run_query") as mock_run_query:
        mock_run_query.return_value = [
            (2, "Title 2", "evento", date(2024, 1, 2), None, "Caption 2")
        ]
        
        posts = service.list_posts(post_type="evento")
        assert len(posts) == 1
        assert posts[0].post_type == "evento"

def test_update_post(mock_engine):
    service = JournalService(mock_engine)
    with patch.object(service, 'get_post') as mock_get_post:
        
        mock_get_post.side_effect = [
            MagicMock(id=1, title="Old"),
            MagicMock(id=1, title="New Title")
        ]
        
        payload = PostUpdate(title="New Title")
        updated = service.update_post(1, payload)
        
        assert updated is not None
        assert updated.title == "New Title"

def test_update_post_not_found(mock_engine):
    service = JournalService(mock_engine)
    with patch.object(service, 'get_post', return_value=None):
        payload = PostUpdate(title="New")
        assert service.update_post(1, payload) is None

def test_update_post_no_fields(mock_engine):
    service = JournalService(mock_engine)
    existing_mock = MagicMock(id=1, title="Old")
    with patch.object(service, 'get_post', return_value=existing_mock):
        payload = PostUpdate()  
        updated = service.update_post(1, payload)
        assert updated == existing_mock

def test_delete_post(mock_engine):
    service = JournalService(mock_engine)
    with patch.object(service, 'get_post') as mock_get_post:
        mock_get_post.return_value = MagicMock(id=1)
        
        success = service.delete_post(1)
        assert success is True

def test_delete_post_not_found(mock_engine):
    service = JournalService(mock_engine)
    with patch.object(service, 'get_post', return_value=None):
        success = service.delete_post(1)
        assert success is False
