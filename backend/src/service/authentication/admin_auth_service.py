import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple, Any

import bcrypt
from sqlalchemy import Engine, text

from src.service.authentication.auth import create_access_token, create_refresh_token

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "caesi@ccc.ufcg.edu.br")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "caesi2025")

# In-memory tracking for failed login attempts
_FAILED_ATTEMPTS: Dict[str, Dict[str, Any]] = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


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
        """Ensure the default admin account exists in the database."""
        with self.engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM administrator")).scalar()
            if count == 0:
                conn.execute(
                    text("INSERT INTO attachment_owner (owner_type) VALUES ('administrator')")
                )
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

    def check_lockout(self, email: str) -> bool:
        """Return True if the email is currently locked out."""
        record = _FAILED_ATTEMPTS.get(email)
        if not record:
            return False
        lock_until = record.get("lock_until")
        if lock_until and datetime.now(timezone.utc) < lock_until:
            return True
        if lock_until and datetime.now(timezone.utc) >= lock_until:
            _FAILED_ATTEMPTS.pop(email, None)
            return False
        return False

    def record_failed_attempt(self, email: str) -> int:
        """Record a failed login attempt for the given email and return attempt count."""
        now = datetime.now(timezone.utc)
        record = _FAILED_ATTEMPTS.setdefault(email, {"count": 0, "lock_until": None})
        record["count"] += 1
        if record["count"] >= MAX_FAILED_ATTEMPTS:
            record["lock_until"] = now + timedelta(minutes=LOCKOUT_MINUTES)
        return record["count"]

    def reset_failed_attempts(self, email: str) -> None:
        """Reset failed attempt counter upon successful login."""
        _FAILED_ATTEMPTS.pop(email, None)

    def login(self, email: str, password: str) -> Optional[Tuple[str, str]]:
        """Validate admin credentials and return (access_token, refresh_token)."""
        clean_email = email.strip().lower()
        if self.check_lockout(clean_email):
            return None

        self._ensure_default_admin()
        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, password FROM administrator WHERE email = :e"),
                {"e": clean_email},
            ).fetchone()

        if row is None or not verify_password(password, row[1]):
            self.record_failed_attempt(clean_email)
            return None

        self.reset_failed_attempts(clean_email)
        admin_id = str(row[0])
        access_token = create_access_token({"sub": admin_id})
        refresh_token = create_refresh_token({"sub": admin_id})
        return access_token, refresh_token

    def change_password(self, admin_id: int, new_password: str) -> bool:
        """Update the password of an existing administrator."""
        hashed = hash_password(new_password)
        with self.engine.connect() as conn:
            result = conn.execute(
                text("UPDATE administrator SET password = :pwd WHERE id = :id"),
                {"pwd": hashed, "id": admin_id},
            )
            conn.commit()
            return result.rowcount > 0
