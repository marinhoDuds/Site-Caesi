import string
import random
from typing import List, Optional, Any
from pypika import Table, Query
from sqlalchemy import Engine, text

from src.service.database import run_query
from src.routes.ticket.schemas import (
    TicketCreate,
    TicketUpdate,
    TicketType,
    TicketResponse,
)

ticket_table = Table("ticket")
attachment_owner_table = Table("attachment_owner")

class TicketService:
    """Service layer for managing tickets (Ouvidoria)."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def _generate_protocol(self) -> str:
        """Generate a random 10-character alphanumeric protocol."""
        chars = string.ascii_uppercase + string.digits
        return "".join(random.choices(chars, k=10))
        
    def _generate_public_id(self) -> str:
        """Generate a random 16-character alphanumeric public ID."""
        chars = string.ascii_letters + string.digits
        return "".join(random.choices(chars, k=16))

    def _map_row_to_response(self, row: Any) -> TicketResponse:
        """Map a raw database tuple to a TicketResponse schema."""
        op_id, public_id, protocol, semester, content, ticket_type, author, email = row
        return TicketResponse(
            id=op_id,
            public_id=public_id,
            protocol=protocol,
            semester=semester,
            content=content,
            ticket_type=ticket_type,
            author=author,
            email=email,
        )

    def _insert_attachment_owner(self) -> int:
        """Insert a base record into attachment_owner and return the generated ID."""
        with self.engine.connect() as conn:
            conn.execute(
                text("INSERT INTO attachment_owner (owner_type) VALUES (:t)"),
                {"t": "ticket"},
            )
            if self.engine.dialect.name == "sqlite":
                owner_id = conn.execute(text("SELECT last_insert_rowid()")).scalar()
            else:
                owner_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            conn.commit()
        return int(owner_id or 0)

    def create_ticket(self, payload: TicketCreate) -> TicketResponse:
        """Create a new ticket in the database."""
        owner_id = self._insert_attachment_owner()
        public_id = self._generate_public_id()
        protocol = self._generate_protocol()

        with self.engine.connect() as conn:
            conn.execute(
                text(
                    "INSERT INTO ticket "
                    "(id, public_id, protocol, semester, content, ticket_type, author, email) "
                    "VALUES (:id, :pub_id, :prot, :sem, :cnt, :tt, :aut, :em)"
                ),
                {
                    "id": owner_id,
                    "pub_id": public_id,
                    "prot": protocol,
                    "sem": payload.semester,
                    "cnt": payload.content,
                    "tt": payload.ticket_type.value,
                    "aut": payload.author,
                    "em": payload.email,
                },
            )
            conn.commit()

        

        return TicketResponse(
            id=owner_id,
            public_id=public_id,
            protocol=protocol,
            semester=payload.semester,
            content=payload.content,
            ticket_type=payload.ticket_type,
            author=payload.author,
            email=payload.email,
        )

    def get_ticket_by_protocol(self, protocol: str) -> Optional[TicketResponse]:
        """Fetch a ticket by its protocol code."""
        query = (
            Query.from_(ticket_table)
            .select(
                "id",
                "public_id",
                "protocol",
                "semester",
                "content",
                "ticket_type",
                "author",
                "email",
            )
            .where(ticket_table.protocol == protocol)
        )
        result = run_query(self.engine, query)

        if not result:
            return None

        return self._map_row_to_response(result[0])

    def list_tickets(
        self, ticket_type: Optional[TicketType] = None
    ) -> List[TicketResponse]:
        """List all tickets, optionally filtering by ticket_type."""
        query = (
            Query.from_(ticket_table)
            .select(
                "id",
                "public_id",
                "protocol",
                "semester",
                "content",
                "ticket_type",
                "author",
                "email",
            )
        )
        if ticket_type:
            query = query.where(ticket_table.ticket_type == ticket_type.value)

        result = run_query(self.engine, query)

        tickets = []
        if result:
            for row in result:
                tickets.append(self._map_row_to_response(row))
        return tickets

    def update_ticket(self, protocol: str, payload: TicketUpdate) -> Optional[TicketResponse]:
        """Update fields of an existing ticket identified by protocol."""
        ticket = self.get_ticket_by_protocol(protocol)
        if not ticket:
            return None

        updates = {}
        if payload.content is not None:
            updates["content"] = payload.content
        if payload.ticket_type is not None:
            updates["ticket_type"] = payload.ticket_type.value
        if payload.semester is not None:
            updates["semester"] = payload.semester

        if not updates:
            return ticket
            
        with self.engine.connect() as conn:
            set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
            sql = f"UPDATE ticket SET {set_clause} WHERE protocol = :protocol"
            params = {**updates, "protocol": protocol}
            
            conn.execute(text(sql), params)
            conn.commit()

        

        return self.get_ticket_by_protocol(protocol)
