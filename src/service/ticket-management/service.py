import random
import string
from datetime import date
from typing import Optional, Any
from pypika import Table, Query
from sqlalchemy import Engine, text

from src.service.database import run_query
from src.routes.ticket.schemas import (
    TicketCreate,
    TicketResponse
)


ticket_table = Table("ticket")
attachment_owner_table = Table("attachment_owner")

#TODO: PROVAVEMENTE ISSO DEVE SER IMPORTADO POR OUTRO MÓDULO, ALGO COMO "src.service.email" ou algo similar
def send_email_notification(email: str, subject: str, body: str) -> None:
    """Send an email notification"""
    pass


class TicketService:
    """Service to handle business logic for ticket operations.

    This service manages the creation and retrieval of tickets submitted
    by users. It handles the generation of unique protocols and public IDs,
    and ensures the attachment_owner polymorphism is respected.

    Attributes
    ----------
    engine: Engine
        The SQLAlchemy engine used to connect to the database.
    """


    def __init__(self, engine: Engine) -> None:
        """Initialize a new TicketService.

        Parameters
        ----------
        engine: Engine
            The SQLAlchemy database engine instance.
        """
        self.engine = engine

    def _map_row_to_response(self, row: Any) -> TicketResponse:
        """Map a raw database row to a TicketResponse model.

        Parameters
        ----------
        row: Any
            The database row - a tuple of
            (id, public_id, protocol, semester, content, ticket_type, author, email).
        
        Returns
        -------
        TicketResponse
            The mapped pydantic response model.
        """
        t_id, pub_id, prot, sem, cnt, t_type, auth, email = row
        return TicketResponse(
            id=t_id,
            public_id=pub_id,
            protocol=prot,
            semester=sem,
            content=cnt,
            ticket_type=t_type,
            author=auth,
            email=email
        )
    
    def _insert_attachment_owner(self) -> int:
        """Insert a attachment_owner record of type 'ticket'.

        Returns
        -------
        int
            The auto-generated ID of the new attachment_owner row.

        Raises
        ------
        Exception
            If the database insertion fails.
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(
                    text("INSERT INTO attachment_owner (owner_type) VALUES (:t)"),
                    {"t": "ticket"},
                )
                owner_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
                conn.commit()
            return int(owner_id or 0)
        except Exception as e:
            raise Exception(f"Failed to create attachment_owner: {str(e)}")

    def _generate_protocol(self) -> str:
        """Generate a unique protocol for the ticket.

        Format: DDMMYYYY:8_random_digits (e.g., 18072026:12345678)

        Returns
        -------
        str
            The generated protocol string.
        """
        current_date = date.today().strftime("%d%m%Y")
        random_digits = "".join(random.choices(string.digits, k=8))
        return f"{current_date}:{random_digits}"
    
    def _generate_public_id(self) -> str:
        """Generate a random 16-character public ID.

        Returns
        -------
        str
            The generated public ID string.
        """
        return "".join(random.choices(string.ascii_letters + string.digits, k=16))
    
    def create_ticket(self, payload: TicketCreate) -> TicketResponse:
        """Create a new ticket from user submission.

        The ticket id reuses the attachment_owner id so that foreign key
        constraints are satisfied. If an email is provided, an email
        notification containing the protocol is sent.

        Parameters
        ----------
        payload : TicketCreate
            The data submitted by the user to create the ticket.

        Returns
        -------
        TicketResponse
            The newly created ticket data.

        Raises
        ------
        Exception
            If the database insertion fails.
        """
        try:
            owner_id = self._insert_attachment_owner()
            protocol = self._generate_protocol()
            public_id = self._generate_public_id()

            query = (
                Query.into(ticket_table)
                .columns(
                    "id",
                    "public_id",
                    "protocol",
                    "semester",
                    "content",
                    "ticket_type",
                    "author",
                    "email"
                )
                .insert(
                    owner_id,
                    public_id,
                    protocol,
                    payload.semester,
                    payload.content,
                    payload.ticket_type,
                    payload.author,
                    payload.email
                )
            )
            run_query(self.engine, query)

            if payload.email:
                subject = "Confirmação de Ticket - Ouvidoria"
                body = (
                    f"Olá {payload.author or 'Usuário'}, \n\n"
                    f"Seu relato foi registrado com sucesso!\n"
                    f"Guarde seu protocolo de acesso com muito cuidado: {protocol}\n\n"
                    f"Você pode acompanhar o status do seu ticket usando este protocolo."
                )
                send_email_notification(payload.email, subject, body)
            
            created_row = (
                owner_id,
                public_id,
                protocol,
                payload.semester,
                payload.content,
                payload.ticket_type.value,
                payload.author,
                payload.email
            )

            return self._map_row_to_response(created_row)
        except Exception as e:
            raise Exception(f"Failed to create ticket: {str(e)}")

    def access_ticket(self, protocol: str) -> Optional[TicketResponse]:
        """Fetch a specific ticket using its unique protocol.

        Parameters
        ----------
        protocol : str
            The protocol string of the ticket to retrieve.

        Returns
        -------
        Optional[TicketResponse]
            The ticket data, or None if not found.

        Raises
        ------
        Exception
            If the database query fails.
        """
        try:
            query = (
                Query.from_(ticket_table)
                .select(
                    ticket_table.id,
                    ticket_table.public_id,
                    ticket_table.protocol,
                    ticket_table.semester,
                    ticket_table.content,
                    ticket_table.ticket_type,
                    ticket_table.author,
                    ticket_table.email
                )
                .where(ticket_table.protocol == protocol)
            )
            result = run_query(self.engine, query)

            if not result:
                return None
            
            return self._map_row_to_response(result[0])
        except Exception as e:
            raise Exception(f"Failed to access ticket: {str(e)}")
    
    def update_ticket_content(self, protocol: str, new_content: str) -> Optional[TicketResponse]:
        """Update the content of an existing ticket identified by its protocol.

        Parameters
        ----------
        protocol : str
            The protocol string of the ticket to update.
        new_content : str
            The new message content for the ticket.

        Returns
        -------
        Optional[TicketResponse]
            The updated ticket data, or None if the ticket protocol was not found.
        
        Raises
        ------
        Exception
            If the database update fails
        """

        existing_ticket = self.access_ticket(protocol)

        if not existing_ticket:
            return None

        try:
            update_query = (
                Query.update(ticket_table)
                .set(ticket_table.content, new_content)
                .where(ticket_table.protocol == protocol)
            )

            run_query(self.engine, update_query)

            if existing_ticket.email:
                subject = "Atualização em seu Ticket - Ouvidoria"
                body = (
                    f"Olá {existing_ticket.author or 'Usuário'}, \n\n"
                    f"Houve uma atualização na mensagem do seu ticket sob o protocolo {protocol}.\n"
                    f"Acesse o sistema para verificar os detalhes."
                )
                send_email_notification(existing_ticket.email, subject, body)

            updated_ticket = existing_ticket.model_copy(update={"content": new_content})
            return updated_ticket
        
        except Exception as e:
            raise Exception(f"Failed to update ticket content: {str(e)}")
