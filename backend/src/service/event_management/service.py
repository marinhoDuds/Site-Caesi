"""
Service for Event (Calendar) management.
"""
from typing import List, Optional
from pypika import Query, Table, Order
from sqlalchemy import Engine
from src.service.database import run_query


class EventService:
    """Business logic for managing calendar events."""

    def __init__(self, engine: Engine):
        self.engine = engine
        self.table = Table("event")

    def list_events(self) -> List[dict]:
        """Return all events ordered by scheduled date."""
        q = Query.from_(self.table).select("*").orderby(
            self.table.scheduled_to, order=Order.asc
        )
        result = run_query(self.engine, q)
        return [dict(r._mapping) if hasattr(r, "_mapping") else dict(r) for r in result]

    def get_event_by_id(self, event_id: int) -> Optional[dict]:
        """Return a single event by its ID."""
        q = Query.from_(self.table).select("*").where(self.table.id == event_id)
        result = run_query(self.engine, q)
        if not result:
            return None
        r = result[0]
        return dict(r._mapping) if hasattr(r, "_mapping") else dict(r)

    def create_event(
        self,
        title: str,
        scheduled_to: str,
        description: str = "",
        formulario_id: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        location: Optional[str] = None,
        category: Optional[str] = "CAESI",
    ) -> dict:
        """Insert a new event and return it."""
        q = Query.into(self.table).columns(
            self.table.title,
            self.table.scheduled_to,
            self.table.description,
            self.table.formulario_id,
            self.table.start_time,
            self.table.end_time,
            self.table.location,
            self.table.category,
        ).insert(title, scheduled_to, description, formulario_id, start_time, end_time, location, category)
        run_query(self.engine, q)
        return self._get_latest_event()

    def update_event(
        self,
        event_id: int,
        title: str,
        scheduled_to: str,
        description: str = "",
        formulario_id: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        location: Optional[str] = None,
        category: Optional[str] = "CAESI",
    ) -> Optional[dict]:
        """Update an existing event and return the updated version."""
        q = (
            Query.update(self.table)
            .set(self.table.title, title)
            .set(self.table.scheduled_to, scheduled_to)
            .set(self.table.description, description)
            .set(self.table.formulario_id, formulario_id)
            .set(self.table.start_time, start_time)
            .set(self.table.end_time, end_time)
            .set(self.table.location, location)
            .set(self.table.category, category)
            .where(self.table.id == event_id)
        )
        run_query(self.engine, q)
        return self.get_event_by_id(event_id)

    def delete_event(self, event_id: int) -> bool:
        """Delete an event by ID."""
        q = Query.from_(self.table).delete().where(self.table.id == event_id)
        run_query(self.engine, q)
        return True

    def _get_latest_event(self) -> dict:
        """Return the most recently inserted event."""
        q = Query.from_(self.table).select("*").orderby(
            self.table.id, order=Order.desc
        ).limit(1)
        result = run_query(self.engine, q)
        if not result:
            return {}
        r = result[0]
        return dict(r._mapping) if hasattr(r, "_mapping") else dict(r)
