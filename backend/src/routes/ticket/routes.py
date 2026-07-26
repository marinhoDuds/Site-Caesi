"""
API routes for Ticket (Ouvidoria) management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from src.service.database import create_engine
from src.service.ticket_management.service import TicketService
from src.service.notification.email_service import EmailNotificationService
from src.routes.ticket.schemas import (
    TicketAdminUpdate,
    TicketCreate,
    TicketResponse,
    TicketType,
    TicketUpdate,
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
    background_tasks: BackgroundTasks,
    service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    """Create a new ticket and receive its unique protocol."""
    ticket = service.create_ticket(payload)
    if ticket.email:
        notifier = EmailNotificationService()
        background_tasks.add_task(
            notifier.send_ticket_created_notification,
            ticket.protocol,
            ticket.email,
            ticket.author,
            ticket.password,
        )
    return ticket


@router.get("/{protocol}", response_model=TicketResponse)
def get_ticket_by_protocol(
    protocol: str,
    password: str,
    service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    """Access a ticket using its unique protocol and password."""
    ticket = service.get_ticket_by_protocol_and_password(protocol, password)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found or invalid credentials"
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


@admin_router.get("/notifications/logs")
def get_notification_logs(
    _admin: dict = Depends(get_current_admin),
):
    """Retrieve email simulation logs for verification (Admin only)."""
    return EmailNotificationService.get_logs()


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
    payload: TicketAdminUpdate,
    background_tasks: BackgroundTasks,
    service: TicketService = Depends(get_ticket_service),
    _admin: dict = Depends(get_current_admin),
) -> TicketResponse:
    """Update a ticket (Admin only)."""
    old_ticket = service.get_ticket_by_protocol(protocol)
    if not old_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )

    updated_ticket = service.update_ticket(protocol, payload)
    if not updated_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )

    if updated_ticket.email and payload.status and payload.status != old_ticket.status:
        notifier = EmailNotificationService()
        background_tasks.add_task(
            notifier.send_ticket_status_notification,
            updated_ticket.protocol,
            updated_ticket.email,
            old_ticket.status,
            updated_ticket.status,
            payload.admin_notes,
        )
    return updated_ticket
