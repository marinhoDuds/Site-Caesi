from typing import List, Optional, Any
from pypika import Table, Query, Order
from sqlalchemy import Engine

from src.service.database import run_query
from src.routes.calendar.schemas import EventResponse


event_table = Table("event")

class CalendarService:
    """Service to handle business logic for calendar operations.

    This service manages the retrieval of public events, allowing
    users to view the academic and institutional calendar.

    Attributes
    ----------
    engine: Engine
        The SQLAlchemy engine used to connect to the database.
    """

    def __init__(self, engine: Engine) -> None:
        """Initialize a new CalendarService.

        Parameters
        ----------
        engine: Engine
            The SQLAlchemy database engine instance.
        """
        self.engine = engine

    def _map_row_to_response(self, row: Any) -> EventResponse:
        """Map a raw database row to an EventResponse model.

        Parameters
        ----------
        row: Any
            The database row - a tuple of
            (id, title, scheduled_to, description).

        Returns
        -------
        EventResponse
            The mapped pydantic response model.
        """
        e_id, title, sched, desc = row
        return EventResponse(
            id=e_id,
            title=title,
            scheduled_to=sched,
            description=desc
        )

    def list_events(self) -> List[EventResponse]:
        """Retrieve all scheduled events from the calendar.

        The events are returned ordered by their scheduled date in
        ascending order (closest events first).

        Returns
        -------
        List[EventResponse]
            A list containing all retrieved events. Returns an empty
            list if no events are found.
        
        Raises
        ------
        Exception
            If the database query fails.
        """
        try:
            query = (
                Query.from_(event_table)
                .select(
                    event_table.id,
                    event_table.title,
                    event_table.scheduled_to,
                    event_table.description
                )
                .orderby(event_table.scheduled_to, order=Order.asc)
            )
            results = run_query(self.engine, query)

            if not results:
                return []

            return [self._map_row_to_response(row) for row in results]

        except Exception as e:
            raise Exception(f"Failed to list event: {str(e)}")

    def get_event(self, event_id: int) -> Optional[EventResponse]:
        """Fetch a specific event using its unique numeric ID.

        Parameters
        ----------
        event_id : int
            The numeric identifier of the event to retrieve.
        
        Returns
        -------
        Optional[EventResponse]
            The event data, or None if not found.

        Raises
        ------
        Exception
            If the database query fails.
        """

        try:
            query = (
                Query.from_(event_table)
                .select(
                    event_table.id,
                    event_table.title,
                    event_table.scheduled_to,
                    event_table.description
                )
                .where(event_table.id == event_id)
            )
            result = run_query(self.engine, query)

            if not result:
                return None

            return self._map_row_to_response(result[0])

        except Exception as e:
            raise Exception(f"Failed to access event: {str(e)}")