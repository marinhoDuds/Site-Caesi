"""
Administrator authentication service.
"""
import os
from typing import Optional

import bcrypt
from sqlalchemy import Engine, text

from src.service.authentication.auth import create_access_token

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "caesi@ccc.ufcg.edu.br")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "caesi2025")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    pw_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        pw_bytes = password.encode("utf-8")[:72]
        return bcrypt.checkpw(pw_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False


class AdminAuthService:
    """Service for administrator login and credential management."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def _ensure_default_admin(self) -> None:
        """Ensure the default admin account exists in the database.

        Creates a seed admin row if the administrator table is empty.
        """
        with self.engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM administrator")).scalar()
            if count == 0:
                conn.execute(
                    text("INSERT INTO attachment_owner (owner_type) VALUES ('administrator')")
                )
                if self.engine.dialect.name == "sqlite":
                    owner_id = conn.execute(text("SELECT last_insert_rowid()")).scalar()
                else:
                    owner_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
                hashed = hash_password(ADMIN_PASSWORD)
                conn.execute(
                    text(
                        "INSERT INTO administrator (id, name, email, password) "
                        "VALUES (:id, :name, :email, :pwd)"
                    ),
                    {"id": owner_id, "name": "Admin CAESI", "email": ADMIN_EMAIL, "pwd": hashed},
                )
                conn.commit()

    def login(self, email: str, password: str) -> Optional[str]:
        """Validate admin credentials and return a JWT access token.

        Parameters
        ----------
        email : str
            The administrator's e-mail address.
        password : str
            The plain-text password supplied by the user.

        Returns
        -------
        Optional[str]
            A signed JWT token if the credentials are valid, ``None`` otherwise.
        """
        self._ensure_default_admin()
        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, password FROM administrator WHERE email = :e"),
                {"e": email.strip().lower()},
            ).fetchone()

        if row is None:
            return None

        admin_id, hashed_pw = row[0], row[1]
        if not verify_password(password, hashed_pw):
            return None

        return create_access_token({"sub": str(admin_id)})

    def change_password(self, admin_id: int, new_password: str) -> bool:
        """Update the password of an existing administrator.

        Parameters
        ----------
        admin_id : int
            The primary key of the administrator record.
        new_password : str
            The new plain-text password to hash and store.

        Returns
        -------
        bool
            ``True`` if the record was updated, ``False`` if not found.
        """
        hashed = hash_password(new_password)
        with self.engine.connect() as conn:
            result = conn.execute(
                text("UPDATE administrator SET password = :pwd WHERE id = :id"),
                {"pwd": hashed, "id": admin_id},
            )
            conn.commit()
            return result.rowcount > 0
