import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from src.main import app
from src.service.notification.email_service import EmailNotificationService
from src.routes.ticket.routes import get_ticket_service


@pytest.fixture(autouse=True)
def clear_email_logs():
    EmailNotificationService.clear_logs()
    yield
    EmailNotificationService.clear_logs()


def test_email_service_missing_email():
    service = EmailNotificationService()

    # None email
    res1 = service.send_ticket_created_notification("PROT-100", None, "User")
    assert res1 is False
    assert len(service.get_logs()) == 0

    # Empty string email
    res2 = service.send_ticket_created_notification("PROT-101", "", "User")
    assert res2 is False
    assert len(service.get_logs()) == 0


def test_global_state_simulation_logs_leak():
    s1 = EmailNotificationService()
    s2 = EmailNotificationService()

    s1.send_ticket_created_notification("PROT-1", "user1@caesi.ufcg.edu.br", "User 1")

    # Class variable _simulation_logs means s2 sees s1's logs
    assert len(s2.get_logs()) == 1
    assert s2.get_logs()[0]["protocol"] == "PROT-1"


def test_background_tasks_execution_via_fastapi(monkeypatch):
    # Mock ticket service
    mock_ticket = MagicMock()
    mock_ticket.id = 1
    mock_ticket.public_id = "pub-123"
    mock_ticket.protocol = "TICK-888"
    mock_ticket.password = "PASS88"
    mock_ticket.semester = "2026.1"
    mock_ticket.content = "Computador não liga no LCC"
    mock_ticket.ticket_type = "infrastructure"
    mock_ticket.email = "aluno@ufcg.edu.br"
    mock_ticket.author = "Aluno Teste"
    mock_ticket.status = "pendente"
    mock_ticket.admin_notes = None
    mock_ticket.updated_at = None

    mock_ticket_service = MagicMock()
    mock_ticket_service.create_ticket.return_value = mock_ticket

    app.dependency_overrides[get_ticket_service] = lambda: mock_ticket_service

    client = TestClient(app)

    # Post to create ticket
    payload = {
        "semester": "2026.1",
        "content": "Computador não liga no LCC",
        "ticket_type": "infrastructure",
        "email": "aluno@ufcg.edu.br",
        "author": "Aluno Teste",
    }
    resp = client.post("/tickets/", json=payload)
    assert resp.status_code == 201

    # Verify background task fired synchronously under TestClient
    logs = EmailNotificationService.get_logs()
    assert len(logs) == 1
    assert logs[0]["recipient"] == "aluno@ufcg.edu.br"
    assert logs[0]["protocol"] == "TICK-888"
    assert logs[0]["event_type"] == "ticket_created"

    app.dependency_overrides.clear()


def test_smtp_mode_stub_behavior(monkeypatch):
    monkeypatch.setenv("EMAIL_MODE", "smtp")
    service = EmailNotificationService()
    assert service.mode == "smtp"

    # In smtp mode without active server, _dispatch_email fails gracefully returning False after logging
    res = service.send_ticket_created_notification(
        "PROT-999", "admin@caesi.ufcg.edu.br", "Admin"
    )
    assert res is False
    logs = service.get_logs()
    assert len(logs) == 1
    assert logs[0]["mode"] == "smtp"


def test_smtp_mode_successful_dispatch(monkeypatch):
    from unittest.mock import patch, MagicMock

    monkeypatch.setenv("EMAIL_MODE", "smtp")
    monkeypatch.setenv("SMTP_HOST", "smtp.test.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@test.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setenv("SMTP_TLS", "true")

    mock_smtp_inst = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_smtp_inst) as mock_smtp_class:
        service = EmailNotificationService()
        res = service.send_ticket_created_notification(
            "PROT-777", "recipient@caesi.ufcg.edu.br", "User"
        )
        assert res is True
        mock_smtp_class.assert_called_once_with("smtp.test.com", 587, timeout=10)
        mock_smtp_inst.starttls.assert_called_once()
        mock_smtp_inst.login.assert_called_once_with("user@test.com", "secret")
        mock_smtp_inst.send_message.assert_called_once()
        mock_smtp_inst.quit.assert_called_once()


def test_smtp_ssl_mode_successful_dispatch(monkeypatch):
    from unittest.mock import patch, MagicMock

    monkeypatch.setenv("EMAIL_MODE", "smtp")
    monkeypatch.setenv("SMTP_HOST", "smtp.ssl.test.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USER", "ssluser@test.com")
    monkeypatch.setenv("SMTP_PASSWORD", "sslsecret")
    monkeypatch.setenv("SMTP_TLS", "false")

    mock_ssl_inst = MagicMock()
    with patch("smtplib.SMTP_SSL", return_value=mock_ssl_inst) as mock_ssl_class:
        service = EmailNotificationService()
        res = service.send_ticket_status_notification(
            "PROT-888",
            "recipient@caesi.ufcg.edu.br",
            "pendente",
            "atendida",
            "Resolvido",
        )
        assert res is True
        mock_ssl_class.assert_called_once_with("smtp.ssl.test.com", 465, timeout=10)
        mock_ssl_inst.login.assert_called_once_with("ssluser@test.com", "sslsecret")
        mock_ssl_inst.send_message.assert_called_once()
        mock_ssl_inst.quit.assert_called_once()
