from typing import Any, Optional

from pypika import Query, Table
from sqlalchemy import Engine

from src.service.database import run_query

ADMINS_TABLE = Table("administrator")


def _row_to_dict(row: Any) -> dict:
    """Convert a SQLAlchemy result row into a plain dict."""
    return dict(row._mapping)


def get_admin_by_email(engine: Engine, email: str) -> Optional[dict]:
    """Fetch an administrator by email.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine.
    email : str
        Email address to look up.

    Returns
    -------
    Optional[dict]
        The administrator row as a dict, or None if not found.
    """
    query = Query.from_(ADMINS_TABLE).select("*").where(ADMINS_TABLE.email == email)
    rows = run_query(engine, query)
    return _row_to_dict(rows[0]) if rows else None


def get_admin_by_google_id(engine: Engine, google_id: str) -> Optional[dict]:
    """Fetch an administrator by their linked Google account ID.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine.
    google_id : str
        The Google account's "sub" claim.

    Returns
    -------
    Optional[dict]
        The administrator row as a dict, or None if not found.
    """
    query = (
        Query.from_(ADMINS_TABLE)
        .select("*")
        .where(ADMINS_TABLE.google_id == google_id)
    )
    rows = run_query(engine, query)
    return _row_to_dict(rows[0]) if rows else None


def get_admin_by_id(engine: Engine, admin_id: int) -> Optional[dict]:
    """Fetch an administrator by ID.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine.
    admin_id : int
        The administrator's ID.

    Returns
    -------
    Optional[dict]
        The administrator row as a dict, or None if not found.
    """
    query = Query.from_(ADMINS_TABLE).select("*").where(ADMINS_TABLE.id == admin_id)
    rows = run_query(engine, query)
    return _row_to_dict(rows[0]) if rows else None


def update_password(engine: Engine, admin_id: int, password_hash: str, salt: str) -> None:
    """Update an administrator's password hash and clear the forced-change flag.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine.
    admin_id : int
        The administrator's ID.
    password_hash : str
        The new salted SHA-256 password hash.
    salt : str
        The salt used to generate the hash.
    """
    query = (
        Query.update(ADMINS_TABLE)
        .set(ADMINS_TABLE.password, password_hash)
        .set(ADMINS_TABLE.salt, salt)
        .set(ADMINS_TABLE.must_change_password, False)
        .where(ADMINS_TABLE.id == admin_id)
    )
    run_query(engine, query)


def link_google_account(engine: Engine, admin_id: int, google_id: str) -> None:
    """Link a Google account ID to an existing administrator.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy engine.
    admin_id : int
        The administrator's ID.
    google_id : str
        The Google account's "sub" claim.
    """
    query = (
        Query.update(ADMINS_TABLE)
        .set(ADMINS_TABLE.google_id, google_id)
        .where(ADMINS_TABLE.id == admin_id)
    )
    run_query(engine, query)