import pytest
from unittest.mock import MagicMock, patch

from src.service.ticket_management.service import TicketService
from src.routes.tickets.schemas import TicketUpdate, TicketType

@pytest.fixture
def mock_engine():
    return MagicMock();


@pytest.fixture
def ticket_service(mock_engine):
    return TicketService(engine=mock_engine)


def _make_ticket_row(
    ticket_id=1,
    public_id="PUB-001",
    protocol="TICKET-001",
    semester="25.1",
    content="Mensagem de teste",
    ticket_type=TicketType.infrastructure,
    author=None,
    email=None
):
    return (
        ticket_id,
        public_id,
        protocol,
        semester,
        content,
        ticket_type,
        author,
        email
    )


def test_list_all_tickets(ticket_service, mock_engine):
    with patch("src.service.ticket_management.service.run_query") as mock_run:
        mock_run.return_value = [
            _make_ticket_row(),
            _make_ticket_row(ticket_id=2, public_id="PUB-002", protocol="TICKET-002", author="Teste da silva", email="testeDaSilva@gmail.com")
        ]

        results = ticket_service.list_all_tickets()

        assert len(results) == 2

        assert results[0].id == 1
        assert results[0].public_id == "PUB-001"
        assert results[0].protocol == "TICKET-001"
        assert results[0].semester == "25.1"
        assert results[0].content == "Mensagem de teste"
        assert results[0].ticket_type == TicketType.infrastructure
        assert results[0].author == None
        assert results[0].email == None

        assert results[1].id == 2
        assert results[1].public_id == "PUB-002"
        assert results[1].protocol == "TICKET-002"
        assert results[1].semester == "25.1"
        assert results[1].content == "Mensagem de teste"
        assert results[1].ticket_type == TicketType.infrastructure
        assert results[1].author == "Teste da silva" 
        assert results[1].email == "testeDaSilva@gmail.com" 


def test_list_all_tickets_empty(ticket_service, mock_engine):
    with patch("src.service.ticket_management.service.run_query") as mock_run:
        mock_run.return_value = []

    results = ticket_service.list_all_tickets()

    assert len(results) == 0


def test_list_tickets_with_type_filter(ticket_service, mock_engine):
    with patch("src.service.ticket_management.service.run_query") as mock_run:
        mock_run.return_value = [
            _make_ticket_row()
        ]

        results = ticket_service.list_all_tickets(ticket_type=TicketType.infrastructure)

        assert len(results) == 1
        assert results[0].ticket_type == TicketType.infrastructure


def test_list_tickets_with_type_filter_empty(ticket_service, mock_engine):
    with patch("src.service.ticket_management.service.run_query") as mock_run:
        mock_run.return_value = []

        results = ticket_service.list_all_tickets(ticket_type=TicketType.infrastructure)

        assert len(results) == 0

    
def test_get_specific_ticket_found(ticket_service, mock_engine):
    with patch("src.service.ticket_management.service.run_query") as mock_run:
        mock_run.return_value = [
            _make_ticket_row(ticket_id=15, public_id="PUB-015", protocol="TICKET-015")
        ]

        result = ticket_service.get_ticket(ticket_id=15)

        assert result is not None
        assert result.id == 15
        assert result.public_id == "PUB-015"
        assert result.protocol == "TICKET-015"


def test_get_specific_ticket_not_found(ticket_service, mock_engine):
    with patch("src.service.ticket_management.service.run_query") as mock_run:
        mock_run.return_value = []

        result = ticket_service.get_ticket(ticket_id=999)

        assert result is None


#TODO: PROVAVELMENTE ESSE TESTE TERÁ QUE MUDAR, POIS NÃO HÁ NO BD UM CAMPO PARA "RESPOSTA" E "STATUS"
def test_update_ticket_without_email_notification(ticket_service, mock_engine):
    payload = TicketUpdate(
        content="Mensagem atualizada pelo ADM"
    )


    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_engine.connect.return_value = mock_conn

    with patch("src.service.ticket_management.service.run_query") as mock_run:

        mock_run.return_value = [
            _make_ticket_row()
        ]

        with patch("src.service.ticket_management.service.send_email_notification") as mock_email:
            
            result = ticket_service.update_ticket(ticket_id=1, payload=payload)

            mock_conn.commit.assert_called_once()

            mock_email.assert_not_called()


#TODO: PROVAVELMENTE ESSE TESTE TERÁ QUE MUDAR, POIS NÃO HÁ NO BD UM CAMPO PARA "RESPOSTA" E "STATUS"
def test_update_ticket_with_email_notification(ticket_service, mock_engine):
    payload = TicketUpdate(
        content="Status: Resolvido"
    )

    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: mock_conn
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_engine.connect.return_value = mock_conn

    with patch("src.service.ticket_management.service.run_query") as mock_run:

        mock_run.return_value = [
            _make_ticket_row(ticket_id=2, email="testeDaSilva@gmail.com")
        ]

        with patch("src.service.ticket_management.service.send_email_notification") as mock_email:

            result = ticket_service.update_ticket(ticket_id=2, payload=payload)

            mock_conn.commit.assert_called_once()

            mock_email.assert_called_once()