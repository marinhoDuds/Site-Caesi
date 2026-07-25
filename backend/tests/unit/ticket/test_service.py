import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import Engine
from src.service.ticket_management.service import TicketService
from src.routes.ticket.schemas import TicketCreate, TicketUpdate, TicketType, TicketResponse


@pytest.fixture
def mock_engine():
    engine = MagicMock(spec=Engine)
    engine.dialect = MagicMock()
    engine.dialect.name = "sqlite"
    conn = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn
    
    conn.execute.return_value.scalar.return_value = 1
    return engine


def test_create_ticket(mock_engine):
    service = TicketService(mock_engine)
    payload = TicketCreate(
        semester="2024",
        content="Test issue",
        ticket_type=TicketType.infrastructure,
        author="John",
        email="john@example.com"
    )
    
    ticket = service.create_ticket(payload)
    assert ticket.id == 1
    assert ticket.semester == "2024"
    assert ticket.ticket_type == TicketType.infrastructure
    assert ticket.author == "John"
    assert ticket.email == "john@example.com"
    assert len(ticket.protocol) == 10
    assert len(ticket.public_id) == 16


def test_create_ticket_mysql(mock_engine):
    # Change dialect to mysql
    mock_engine.dialect.name = "mysql"
    service = TicketService(mock_engine)
    payload = TicketCreate(
        semester="2024",
        content="Test issue",
        ticket_type=TicketType.infrastructure,
        author="John",
        email="john@example.com"
    )
    
    ticket = service.create_ticket(payload)
    assert ticket.id == 1


def test_get_ticket_by_protocol(mock_engine):
    service = TicketService(mock_engine)
    with patch("src.service.ticket_management.service.run_query") as mock_run_query:
        mock_run_query.return_value = [
            (1, "pub123", "PROT123", "2024", "Content", "infrastructure", "Test Author", "test@test.com")
        ]
        ticket = service.get_ticket_by_protocol("PROT123")
        assert ticket is not None
        assert ticket.protocol == "PROT123"

        # Not found
        mock_run_query.return_value = []
        ticket_not_found = service.get_ticket_by_protocol("UNKNOWN")
        assert ticket_not_found is None


def test_list_tickets(mock_engine):
    service = TicketService(mock_engine)
    with patch("src.service.ticket_management.service.run_query") as mock_run_query:
        mock_run_query.return_value = [
            (1, "pub123", "PROT123", "2024", "Content", "infrastructure", "Test Author", "test@test.com")
        ]
        tickets = service.list_tickets()
        assert len(tickets) == 1
        assert tickets[0].protocol == "PROT123"

        # List with filter
        tickets_filtered = service.list_tickets(ticket_type=TicketType.infrastructure)
        assert len(tickets_filtered) == 1

def test_update_ticket(mock_engine):
    service = TicketService(mock_engine)
    payload = TicketUpdate(content="New content", semester="2025", ticket_type=TicketType.classmates)
    
    with patch("src.service.ticket_management.service.TicketService.get_ticket_by_protocol") as mock_get:
        mock_get.return_value = TicketResponse(
            id=1, public_id="pub123", protocol="PROT123", semester="2025", 
            content="New content", ticket_type=TicketType.classmates,
            author="John", email="john@example.com"
        )
        ticket = service.update_ticket("PROT123", payload)
        assert ticket is not None
        assert ticket.content == "New content"
        
        # update non-existent
        mock_get.return_value = None
        assert service.update_ticket("UNKNOWN", payload) is None
        
        # update with no changes (empty updates dict)
        mock_get.return_value = TicketResponse(
            id=1, public_id="pub123", protocol="PROT123", semester="2025", 
            content="New content", ticket_type=TicketType.classmates,
            author="John", email="john@example.com"
        )
        empty_payload = TicketUpdate(content=None, semester=None, ticket_type=None)
        ticket_no_change = service.update_ticket("PROT123", empty_payload)
        assert ticket_no_change is not None
