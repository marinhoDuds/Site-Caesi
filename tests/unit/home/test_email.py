import smtplib
from email import message_from_string
from unittest.mock import MagicMock, patch

import pytest

from src.service.home_management.email_service import EmailService


def _set_smtp_env(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.test.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "no-reply@caesi.org")
    monkeypatch.setenv("SMTP_PASSWORD", "segredo")


class TestEnviarSenha:
    def test_levanta_erro_quando_smtp_nao_configurado(self, monkeypatch):
        monkeypatch.delenv("SMTP_HOST", raising=False)
        monkeypatch.delenv("SMTP_USER", raising=False)
        monkeypatch.delenv("SMTP_PASSWORD", raising=False)
        service = EmailService()

        with pytest.raises(ValueError):
            service.enviar_senha("admin@example.com", "senha123")

    def test_envia_email_com_login_e_conteudo_corretos(self, monkeypatch):
        _set_smtp_env(monkeypatch)
        mock_server = MagicMock()
        mock_smtp_cls = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server
        service = EmailService()

        with patch("smtplib.SMTP", mock_smtp_cls):
            service.enviar_senha("admin@example.com", "senha123")

        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("no-reply@caesi.org", "segredo")
        mock_server.sendmail.assert_called_once()

        destinatario, mensagem_raw = mock_server.sendmail.call_args.args[1:]
        assert destinatario == ["admin@example.com"]

        corpo = (
            message_from_string(mensagem_raw).get_payload(decode=True).decode("utf-8")
        )
        assert "senha123" in corpo

    def test_levanta_erro_quando_smtp_falha(self, monkeypatch):
        _set_smtp_env(monkeypatch)
        mock_smtp_cls = MagicMock()
        mock_smtp_cls.return_value.__enter__.side_effect = smtplib.SMTPException("boom")
        service = EmailService()

        with patch("smtplib.SMTP", mock_smtp_cls):
            with pytest.raises(ValueError):
                service.enviar_senha("admin@example.com", "senha123")
