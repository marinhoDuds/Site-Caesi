from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from src.routes.ticket.routes import router, admin_router, get_ticket_service
from src.routes.ticket.schemas import TicketResponse, TicketType
from src.service.authentication.auth import get_current_admin

app = FastAPI()
app.include_router(router)
app.include_router(admin_router)

mock_service = MagicMock()

def override_get_ticket_service():
    return mock_service

def override_get_current_admin():
    return {"id": 1}

app.dependency_overrides[get_ticket_service] = override_get_ticket_service
app.dependency_overrides[get_current_admin] = override_get_current_admin

client = TestClient(app)

def _make_ticket(
    op_id=1,
    public_id="pub123",
    protocol="PROT123",
    password="PASS12",
    semester="2024",
    content="Test",
    ticket_type=TicketType.infrastructure,
    author="John",
    email="test@test.com",
    status="pendente",
    admin_notes=None,
    updated_at=None
) -> TicketResponse:
    return TicketResponse(
        id=op_id,
        public_id=public_id,
        protocol=protocol,
        password=password,
        semester=semester,
        content=content,
        ticket_type=ticket_type,
        author=author,
        email=email,
        status=status,
        admin_notes=admin_notes,
        updated_at=updated_at
    )


def test_get_ticket_service_dependency():
    from unittest.mock import patch
    with patch("src.routes.ticket.routes.create_engine") as mock_engine:
        service = get_ticket_service()
        assert service is not None
        mock_engine.assert_called_once()

def test_create_ticket_route():
    mock_service.create_ticket.return_value = _make_ticket()

    response = client.post(
        "/tickets/",
        json={
            "semester": "2024",
            "content": "Test",
            "ticket_type": "infrastructure",
            "author": "John",
            "email": "test@test.com"
        }
    )

    assert response.status_code == 201
    assert response.json()["protocol"] == "PROT123"

def test_get_ticket_route():
    mock_service.get_ticket_by_protocol.return_value = _make_ticket()

    response = client.get("/tickets/PROT123")

    assert response.status_code == 200
    assert response.json()["protocol"] == "PROT123"

def test_get_ticket_not_found():
    mock_service.get_ticket_by_protocol.return_value = None

    response = client.get("/tickets/UNKNOWN")

    assert response.status_code == 404

def test_update_ticket_route():
    mock_service.update_ticket.return_value = _make_ticket(content="Updated")

    response = client.patch(
        "/tickets/PROT123",
        json={"content": "Updated"}
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Updated"

def test_update_ticket_not_found():
    mock_service.update_ticket.return_value = None

    response = client.patch(
        "/tickets/UNKNOWN",
        json={"content": "Updated"}
    )

    assert response.status_code == 404


def test_admin_list_tickets():
    mock_service.list_tickets.return_value = [_make_ticket()]

    response = client.get("/admin/tickets/")

    assert response.status_code == 200
    assert len(response.json()) == 1

def test_admin_list_tickets_with_filter():
    mock_service.list_tickets.return_value = [_make_ticket()]

    response = client.get("/admin/tickets/?ticket_type=infrastructure")

    assert response.status_code == 200
    mock_service.list_tickets.assert_called_with(TicketType.infrastructure)

def test_admin_get_ticket():
    mock_service.get_ticket_by_protocol.return_value = _make_ticket()

    response = client.get("/admin/tickets/PROT123")
    assert response.status_code == 200

def test_admin_get_ticket_not_found():
    mock_service.get_ticket_by_protocol.return_value = None

    response = client.get("/admin/tickets/UNKNOWN")
    assert response.status_code == 404

def test_admin_update_ticket():
    mock_service.get_ticket_by_protocol.return_value = _make_ticket()
    mock_service.update_ticket.return_value = _make_ticket(content="Updated by admin")

    response = client.patch(
        "/admin/tickets/PROT123",
        json={"content": "Updated by admin"}
    )
    assert response.status_code == 200

def test_admin_update_ticket_not_found():
    mock_service.get_ticket_by_protocol.return_value = None
    mock_service.update_ticket.return_value = None

    response = client.patch(
        "/admin/tickets/UNKNOWN",
        json={"content": "Updated by admin"}
    )
    assert response.status_code == 404

def test_ticket_email_notification_simulation():
    from src.service.notification.email_service import EmailNotificationService
    EmailNotificationService.clear_logs()

    # 1. Create ticket
    mock_service.create_ticket.return_value = _make_ticket(
        protocol="NOTIF123",
        email="aluno@ufcg.edu.br",
        author="Maria"
    )

    resp_create = client.post(
        "/tickets/",
        json={
            "semester": "2024",
            "content": "Problema no laboratório",
            "ticket_type": "infrastructure",
            "author": "Maria",
            "email": "aluno@ufcg.edu.br"
        }
    )
    assert resp_create.status_code == 201

    logs = EmailNotificationService.get_logs()
    assert len(logs) == 1
    assert logs[0]["recipient"] == "aluno@ufcg.edu.br"
    assert logs[0]["event_type"] == "ticket_created"

    # 2. Update status as Admin
    mock_service.get_ticket_by_protocol.return_value = _make_ticket(
        protocol="NOTIF123",
        email="aluno@ufcg.edu.br",
        status="pendente"
    )
    mock_service.update_ticket.return_value = _make_ticket(
        protocol="NOTIF123",
        email="aluno@ufcg.edu.br",
        status="atendida",
        admin_notes="Equipamento substituído."
    )

    resp_update = client.patch(
        "/admin/tickets/NOTIF123",
        json={"status": "atendida", "admin_notes": "Equipamento substituído."}
    )
    assert resp_update.status_code == 200

    logs_after = EmailNotificationService.get_logs()
    assert len(logs_after) == 2
    assert logs_after[1]["event_type"] == "ticket_status_updated"
    assert "Equipamento substituído." in logs_after[1]["body"]

    # 3. Check logs audit endpoint
    resp_logs = client.get("/admin/tickets/notifications/logs")
    assert resp_logs.status_code == 200
    assert len(resp_logs.json()) == 2

