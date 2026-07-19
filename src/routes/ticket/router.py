from fastapi import APIRouter, Depends, HTTPException 

from src.routes.ticket.schemas import TicketCreate, TicketResponse
from src.service.ticket_management.service import TicketService
from src.service.database import create_engine


router = APIRouter(tags=["Ouvidoria - Tickets"])


def get_ticket_service() -> TicketService:
    """Dependency injector for TicketService.

    Returns
    -------
    TicketService
        An instantiated TicketService with a valid database engine.
    """
    engine = create_engine()
    return TicketService(engine)


@router.post("/tickets", response_model=TicketResponse, status_code=201)
async def create_ticket(
    payload: TicketCreate,
    service: TicketService = Depends(get_ticket_service)
) -> TicketResponse:
    """Create a new ticket endpoint for users.

    Accepts a JSON request with the ticket fields. Anonymous submissions
    are allowed. If an email is provided, a notification will be sent.

    Parameters
    ----------
    payload : TicketCreate
        The JSON payload containing the ticket data.
    service : TicketService, optional
        The injected ticket service dependency.

    Returns
    -------
    TicketResponse
        The created ticket data, including the generated protocol.

    Raises
    ------
    HTTPException
        If the ticket cannot be created due to an internal error.
    """
    try:
        return service.create_ticket(payload)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create ticket: {str(e)}"
        )


@router.get("/tickets/{protocol}", response_model=TicketResponse)
async def access_ticket(
    protocol: str,
    service: TicketService = Depends(get_ticket_service)
) -> TicketResponse:
    """Retrieve an existing ticket using its unique protocol

    Parameters
    ----------
    protocol : str
        The protocol string generated when ticket was created.
    service : TicketService, optional
        The injected ticket service dependency.
    
    Returns
    -------
    TicketResponse
        The retrieved ticket data.

    Raises
    ------
    HTTPException
        If no ticket matches the provided protocol.
    """
    result = service.access_ticket(protocol)
    if not result:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return result


@router.patch("/tickets/{protocol}", response_model=TicketResponse)
async def update_ticket_content(
    protocol: str,
    new_content: str,
    service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    """Update the message content of an existing ticket.

    Parameters
    ----------
    protocol : str
        The protocol of the ticket to update.
    new_content : str
        The updated message text.
    service : TicketService, optional
        The injected ticket service dependency.

    Returns
    -------
    TicketResponse
        The updated ticket data.

    Raises
    ------
    HTTPException
        If the ticket cannot be found, or if the new content is empty.
    """
    if not new_content or not new_content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty")
    
    try:
        result = service.update_ticket_content(protocol, new_content)

        if not result:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update ticket: {str(e)}")