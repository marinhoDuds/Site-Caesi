from functools import lru_cache

from fastapi import Depends
from sqlalchemy import Engine

from ...service.database import create_engine
from ...service.home_management.admin_service import AdminService
from ...service.home_management.caesi_service import CaesiService
from ...service.home_management.email_service import EmailService
from ...service.home_management.password_service import PasswordService
from ...service.home_management.storage_service import StorageService


@lru_cache
def get_engine() -> Engine:
    """Return a cached SQLAlchemy engine shared across requests."""
    return create_engine()


def get_admin_service(engine: Engine = Depends(get_engine)) -> AdminService:
    """Build an AdminService wired with its collaborator services."""
    return AdminService(
        engine=engine,
        password_service=PasswordService(),
        storage_service=StorageService(),
        email_service=EmailService(),
    )


def get_caesi_service(engine: Engine = Depends(get_engine)) -> CaesiService:
    """Build a CaesiService bound to the shared engine."""
    return CaesiService(engine)
