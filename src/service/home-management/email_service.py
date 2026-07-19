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