from ..crypto import generate_random_password, generate_salt, hash_password


class PasswordService:
    """Handle generation and encryption of admin passwords."""

    def gerar_senha_aleatoria(self, length: int = 12) -> str:
        """Generate a random plaintext password.

        Parameters
        ----------
        length : int, optional
            The desired length of the generated password.

        Returns
        -------
        str
            A randomly generated plaintext password.
        """
        return generate_random_password(length)

    def hash_sha256_salt(self, senha: str) -> tuple[str, str]:
        """Hash a plaintext password using SHA256 with a random salt.

        Parameters
        ----------
        senha : str
            The plaintext password to hash.

        Returns
        -------
        tuple[str, str]
            A tuple containing the resulting (senha_hash, salt).
        """
        salt = generate_salt()
        senha_hash = hash_password(senha, salt)
        return senha_hash, salt
