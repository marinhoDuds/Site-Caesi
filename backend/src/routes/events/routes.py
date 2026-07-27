"""
API routes for Event (Calendar) management.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from src.service.database import create_engine
from src.service.event_management.service import EventService
from src.routes.events.schemas import EventCreate, EventUpdate, EventResponse
from src.service.authentication.auth import get_current_admin

router = APIRouter(prefix="/events", tags=["events"])
admin_router = APIRouter(prefix="/admin/events", tags=["admin-events"])


def get_event_service() -> EventService:
    """Dependency injection for the EventService."""
    engine = create_engine()
    return EventService(engine)


@router.get("/", response_model=List[EventResponse])
def list_events(
    service: EventService = Depends(get_event_service),
):
    """List all calendar events."""
    return service.list_events()


@admin_router.post(
    "/", response_model=EventResponse, status_code=status.HTTP_201_CREATED
)
def create_event(
    payload: EventCreate,
    service: EventService = Depends(get_event_service),
    _admin: dict = Depends(get_current_admin),
):
    """Create a new calendar event (Admin only)."""
    return service.create_event(
        title=payload.title,
        scheduled_to=payload.scheduled_to,
        description=payload.description or "",
        formulario_id=payload.formulario_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        location=payload.location,
        category=payload.category,
    )


@admin_router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    payload: EventUpdate,
    service: EventService = Depends(get_event_service),
    _admin: dict = Depends(get_current_admin),
):
    """Update an existing calendar event (Admin only)."""
    existing = service.get_event_by_id(event_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return service.update_event(
        event_id=event_id,
        title=payload.title,
        scheduled_to=payload.scheduled_to,
        description=payload.description or "",
        formulario_id=payload.formulario_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        location=payload.location,
        category=payload.category,
    )


@admin_router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    service: EventService = Depends(get_event_service),
    _admin: dict = Depends(get_current_admin),
):
    """Delete a calendar event (Admin only)."""
    existing = service.get_event_by_id(event_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    service.delete_event(event_id)
