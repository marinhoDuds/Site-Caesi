"""
API routes for Ticket (Ouvidoria) management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from src.service.database import create_engine
from src.service.ticket_management.service import TicketService
from src.routes.ticket.schemas import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    TicketType,
)
from src.service.authentication.auth import get_current_admin

router = APIRouter(prefix="/tickets", tags=["tickets"])
admin_router = APIRouter(prefix="/admin/tickets", tags=["admin-tickets"])


def get_ticket_service() -> TicketService:
    """Dependency injection for the TicketService."""
    engine = create_engine()
    return TicketService(engine)


@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    """Create a new ticket and receive its unique protocol."""
    return service.create_ticket(payload)


@router.get("/{protocol}", response_model=TicketResponse)
def get_ticket_by_protocol(
    protocol: str,
    service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    """Access a ticket using its unique protocol."""
    ticket = service.get_ticket_by_protocol(protocol)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )
    return ticket


@router.patch("/{protocol}", response_model=TicketResponse)
def update_ticket(
    protocol: str,
    payload: TicketUpdate,
    service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    """Update a ticket using its unique protocol (User)."""
    ticket = service.update_ticket(protocol, payload)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )
    return ticket


@admin_router.get("/", response_model=List[TicketResponse])
def list_tickets(
    ticket_type: Optional[TicketType] = None,
    service: TicketService = Depends(get_ticket_service),
    _admin: dict = Depends(get_current_admin),
) -> List[TicketResponse]:
    """List all tickets with optional filtering by type (Admin only)."""
    return service.list_tickets(ticket_type)


@admin_router.get("/{protocol}", response_model=TicketResponse)
def get_ticket_admin(
    protocol: str,
    service: TicketService = Depends(get_ticket_service),
    _admin: dict = Depends(get_current_admin),
) -> TicketResponse:
    """Access a specific ticket details (Admin only)."""
    ticket = service.get_ticket_by_protocol(protocol)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )
    return ticket


@admin_router.patch("/{protocol}", response_model=TicketResponse)
def update_ticket_admin(
    protocol: str,
    payload: TicketUpdate,
    service: TicketService = Depends(get_ticket_service),
    _admin: dict = Depends(get_current_admin),
) -> TicketResponse:
    """Update a ticket (Admin only)."""
    ticket = service.update_ticket(protocol, payload)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )
    return ticket
