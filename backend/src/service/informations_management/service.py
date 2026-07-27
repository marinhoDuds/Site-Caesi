"""
Service for managing generic information records (announcements, labs, professors, etc.).
"""

from typing import List, Optional

from pypika import Order, Query, Table
from sqlalchemy import Engine, text

from src.service.attachment_service import AttachmentService
from src.service.database import run_query


class InformationService:
    """Service layer for managing generic information records.

    Parameters
    ----------
    engine : Engine
        SQLAlchemy database engine instance.
    """

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def _insert_attachment_owner(self) -> int:
        """Insert a base record into attachment_owner and return the generated ID."""
        with self.engine.connect() as conn:
            conn.execute(
                text("INSERT INTO attachment_owner (owner_type) VALUES (:t)"),
                {"t": "information"},
            )
            owner_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            conn.commit()
        return int(owner_id or 0)

    def create_information(self, information_type: str, content: str) -> dict:
        """Create a new information entry in the database.

        Parameters
        ----------
        information_type : str
            Category or type of the information record (e.g. 'tamburetei', 'laboratorios').
        content : str
            JSON string or text payload representing the information contents.

        Returns
        -------
        dict
            The newly created information record dictionary.
        """
        owner_id = self._insert_attachment_owner()
        table = Table("information")
        q = (
            Query.into(table)
            .columns(table.id, table.information_type, table.content)
            .insert(owner_id, information_type, content)
        )

        run_query(self.engine, q)
        return self.get_information_by_id(owner_id) or {}

    def get_latest_information(self) -> Optional[dict]:
        """Fetch the most recently created information entry.

        Returns
        -------
        Optional[dict]
            Dictionary representing the latest information entry, or None if empty.
        """
        table = Table("information")
        q = Query.from_(table).select("*").orderby(table.id, order=Order.desc).limit(1)
        result = run_query(self.engine, q)
        if not result:
            return None
        r = result[0]
        return dict(r._mapping) if hasattr(r, "_mapping") else dict(r)

    def get_information_by_id(self, info_id: int) -> Optional[dict]:
        """Retrieve a specific information record by its unique ID.

        Parameters
        ----------
        info_id : int
            Primary key ID of the information record.

        Returns
        -------
        Optional[dict]
            Information record dictionary if found, otherwise None.
        """
        table = Table("information")
        q = Query.from_(table).select("*").where(table.id == info_id)
        result = run_query(self.engine, q)
        if not result:
            return None
        r = result[0]
        return dict(r._mapping) if hasattr(r, "_mapping") else dict(r)

    def get_informations_by_type(self, information_type: str) -> List[dict]:
        """Retrieve all information records matching a specified category/type.

        Parameters
        ----------
        information_type : str
            Category filter for information records.

        Returns
        -------
        List[dict]
            List of matching information record dictionaries.
        """
        table = Table("information")
        q = (
            Query.from_(table)
            .select("*")
            .where(table.information_type == information_type)
        )
        result = run_query(self.engine, q)
        return [dict(r._mapping) if hasattr(r, "_mapping") else dict(r) for r in result]

    def update_information(
        self, info_id: int, information_type: str, content: str
    ) -> Optional[dict]:
        """Update an existing information entry by ID.

        Parameters
        ----------
        info_id : int
            ID of the record to update.
        information_type : str
            Updated type/category for the record.
        content : str
            Updated content payload.

        Returns
        -------
        Optional[dict]
            Updated information record dictionary, or None if record does not exist.
        """
        table = Table("information")
        q = (
            Query.update(table)
            .set(table.information_type, information_type)
            .set(table.content, content)
            .where(table.id == info_id)
        )
        run_query(self.engine, q)
        return self.get_information_by_id(info_id)

    def delete_information(self, info_id: int) -> bool:
        """Delete an information entry by ID.

        Parameters
        ----------
        info_id : int
            ID of the record to delete.

        Returns
        -------
        bool
            True if deletion was executed successfully.
        """
        AttachmentService(self.engine).delete_for_owner(info_id)
        table = Table("information")
        q = Query.from_(table).delete().where(table.id == info_id)
        run_query(self.engine, q)
        with self.engine.connect() as conn:
            conn.execute(
                text("DELETE FROM attachment_owner WHERE id = :id"), {"id": info_id}
            )
            conn.commit()
        return True
