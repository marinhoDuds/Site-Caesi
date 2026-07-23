from fastapi import APIRouter, Depends, HTTPException
from typing import List

from src.routes.calendar.schemas import EventResponse
from src.service.calendar_management.service import CalendarService
from src.service.database import create_engine


router = APIRouter(tags=["Calendário - Eventos"])


def get_calendar_service() -> CalendarService:
    """Dependency injector for CalendarService.

    Returns
    -------
    CalendarService
        An instantiated CalendarService with a valid database engine.
    """
    engine = create_engine()
    return CalendarService(engine)


@router.get("/events", response_model=List[EventResponse])
async def list_events(
    service: CalendarService = Depends(get_calendar_service)
) -> List[EventResponse]:
    """Retrieve all public events from the calendar.
    
    Returns a list of all scheduled events ordered by their
    scheduled date in ascending order (closest first).
    
    Parameters
    ----------
    service : CalendarService, optional
        The injected calendar service dependency.
        
    Returns
    -------
    List[EventResponse]
        A list of retrieved events. Returns an empty list if none exist.
    
    Raises
    ------
    HTTPException
        If an internal error occurs while fetching the events.
    """
    try:
        return service.list_events()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list events: {str(e)}"
        )


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    service: CalendarService = Depends(get_calendar_service)
) -> EventResponse:
    """Retrieve an existing event using its unique numeric ID.
    
    Parameters
    ----------
    event_id : int
        The numeric identifier of the event to retrieve.
    service : CalendarService, optional
        The injected calendar service dependency.
        
    Returns
    -------
    EventResponse
        The retrieved event data.
        
    Raises
    ------
    HTTPException
        If no event matches the provided ID.
    """
    result = service.get_event(event_id)

    if not result:
        raise HTTPException(status_code=404, detail="Event not found")

    return result