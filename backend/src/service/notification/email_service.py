"""
Email Notification Service for sending and simulating ticket notifications.
"""

import logging
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for handling email notifications for tickets."""

    _simulation_logs: List[Dict[str, Any]] = []

    def __init__(self) -> None:
        self.mode = os.getenv("EMAIL_MODE", "simulation").lower()
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_tls = os.getenv("SMTP_TLS", "true").lower() == "true"
        self.smtp_from_email = os.getenv(
            "SMTP_FROM_EMAIL", self.smtp_user or "noreply@caesi.ufcg.edu.br"
        )

    def send_ticket_created_notification(
        self,
        protocol: str,
        email: Optional[str],
        author: Optional[str],
        password: Optional[str] = None,
    ) -> bool:
        """Send notification when a ticket is created."""
        if not email:
            return False
        subject = f"[CAESI] Confirmação de Ticket #{protocol}"
        pwd_line = f"Senha de acesso: {password}\n" if password else ""
        body = (
            f"Olá {author or 'Usuário'},\n\n"
            f"Seu ticket foi recebido com sucesso!\n"
            f"Protocolo: {protocol}\n"
            f"{pwd_line}\n"
            f"Acompanhe a resolução pelo site da ouvidoria informando seu protocolo e senha."
        )
        return self._dispatch_email(email, subject, body, protocol, "ticket_created")

    def send_ticket_status_notification(
        self,
        protocol: str,
        email: Optional[str],
        old_status: str,
        new_status: str,
        admin_notes: Optional[str],
    ) -> bool:
        """Send notification when a ticket status is updated."""
        if not email:
            return False
        subject = f"[CAESI] Atualização do Ticket #{protocol}"
        body = f"Seu ticket #{protocol} teve o status alterado de '{old_status}' para '{new_status}'.\n"
        if admin_notes:
            body += f"\nNota da Gestão:\n{admin_notes}\n"
        return self._dispatch_email(
            email, subject, body, protocol, "ticket_status_updated"
        )

    def _dispatch_email(
        self, recipient: str, subject: str, body: str, protocol: str, event_type: str
    ) -> bool:
        """Dispatch email or log in simulation mode."""
        log_entry = {
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "protocol": protocol,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": self.mode,
        }
        EmailNotificationService._simulation_logs.append(log_entry)

        if self.mode == "smtp":
            try:
                msg = MIMEMultipart()
                msg["From"] = self.smtp_from_email
                msg["To"] = recipient
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain", "utf-8"))

                if self.smtp_port == 465 and not self.smtp_tls:
                    server = smtplib.SMTP_SSL(
                        self.smtp_host, self.smtp_port, timeout=10
                    )
                else:
                    server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
                    if self.smtp_tls:
                        server.starttls()

                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)

                server.send_message(msg)
                server.quit()
                return True
            except smtplib.SMTPException as e:
                logger.error(f"SMTP error dispatching email to {recipient}: {e}")
                return False
            except Exception as e:
                logger.error(f"Unexpected error dispatching email to {recipient}: {e}")
                return False

        return True

    @classmethod
    def get_logs(cls) -> List[Dict[str, Any]]:
        """Retrieve simulation logs."""
        return cls._simulation_logs

    @classmethod
    def clear_logs(cls) -> None:
        """Clear simulation logs."""
        cls._simulation_logs.clear()
