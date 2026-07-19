import logging
import os
import smtplib
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


class EmailService:
    """Handle notification emails for the Quem Somos module."""

    def enviar_senha(self, email: str, senha: str) -> None:
        """Send the generated password to the admin's email.

        Parameters
        ----------
        email : str
            The recipient's email address.
        senha : str
            The plaintext password to send.
        """
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")

        if not smtp_host or not smtp_user or not smtp_password:
            raise ValueError(
                "SMTP is not configured. Set SMTP_HOST, SMTP_USER and "
                "SMTP_PASSWORD in your .env file."
            )

        message = MIMEText(
            "Olá!\n\n"
            "Sua conta de administrador do Quem Somos foi criada.\n"
            f"Sua senha de acesso é: {senha}\n\n"
            "Recomendamos alterá-la após o primeiro login."
        )
        message["Subject"] = "Sua senha de acesso - Quem Somos CAESI"
        message["From"] = smtp_user
        message["To"] = email

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, [email], message.as_string())
        except smtplib.SMTPException as e:
            logger.error(f"Failed to send password email: {e}")
            raise ValueError(f"Failed to send password email to '{email}'.") from e
