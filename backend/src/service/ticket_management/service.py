from datetime import date
import string
import random
from typing import List, Optional, Any
from pypika import Table, Query
from sqlalchemy import Engine, text

from src.service.database import run_query
from src.routes.ticket.schemas import (
    TicketCreate,
    TicketResponse,
    TicketType,
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

    def _generate_password(self) -> str:
        """Generate a random 6-character alphanumeric ticket password."""
        chars = string.ascii_uppercase + string.digits
        return "".join(random.choices(chars, k=6))

    def _map_row_to_response(self, row: Any) -> TicketResponse:
        """Map a raw database tuple to a TicketResponse schema."""
        op_id = row[0]
        public_id = row[1]
        protocol = row[2]
        semester = row[3]
        content = row[4]
        ticket_type = row[5]
        author = row[6]
        email = row[7]
        status_val = row[8] if len(row) > 8 and row[8] is not None else "pendente"
        pwd = row[9] if len(row) > 9 else None
        admin_notes = row[10] if len(row) > 10 else None
        updated_at = row[11] if len(row) > 11 else None

        return TicketResponse(
            id=op_id,
            public_id=public_id,
            protocol=protocol,
            password=pwd,
            semester=semester,
            content=content,
            ticket_type=ticket_type,
            author=author,
            email=email,
            status=status_val,
            admin_notes=admin_notes,
            updated_at=updated_at,
        )

    def _insert_attachment_owner(self) -> int:
        """Insert a base record into attachment_owner and return the generated ID."""
        with self.engine.connect() as conn:
            conn.execute(
                text("INSERT INTO attachment_owner (owner_type) VALUES (:t)"),
                {"t": "ticket"},
            )
            owner_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            conn.commit()
        return int(owner_id or 0)

    def create_ticket(self, payload: TicketCreate) -> TicketResponse:
        """Create a new ticket in the database."""
        owner_id = self._insert_attachment_owner()
        public_id = self._generate_public_id()
        protocol = self._generate_protocol()
        password = self._generate_password()

        with self.engine.connect() as conn:
            conn.execute(
                text(
                    "INSERT INTO ticket "
                    "(id, public_id, protocol, password, semester, content, ticket_type, author, email, status) "
                    "VALUES (:id, :pub_id, :prot, :pwd, :sem, :cnt, :tt, :aut, :em, :st)"
                ),
                {
                    "id": owner_id,
                    "pub_id": public_id,
                    "prot": protocol,
                    "pwd": password,
                    "sem": payload.semester,
                    "cnt": payload.content,
                    "tt": payload.ticket_type.value,
                    "aut": payload.author,
                    "em": payload.email,
                    "st": "Aberto",
                },
            )
            conn.commit()

        return TicketResponse(
            id=owner_id,
            public_id=public_id,
            protocol=protocol,
            password=password,
            semester=payload.semester,
            content=payload.content,
            ticket_type=payload.ticket_type,
            author=payload.author,
            email=payload.email,
            status="Aberto",
            admin_notes=None,
            updated_at=None,
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
                "status",
                "password",
                "admin_notes",
                "updated_at",
            )
            .where(ticket_table.protocol == protocol)
        )
        result = run_query(self.engine, query)

        if not result:
            return None

        return self._map_row_to_response(result[0])

    def get_ticket_by_protocol_and_password(
        self, protocol: str, password: str
    ) -> Optional[TicketResponse]:
        """Fetch a ticket by its protocol and validate password."""
        ticket = self.get_ticket_by_protocol(protocol)
        if not ticket:
            return None
        if ticket.password and ticket.password != password.strip():
            return None
        return ticket

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
                "status",
                "password",
                "admin_notes",
                "updated_at",
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

    def update_ticket(self, protocol: str, payload: Any) -> Optional[TicketResponse]:
        """Update fields of an existing ticket identified by protocol."""
        ticket = self.get_ticket_by_protocol(protocol)
        if not ticket:
            return None

        updates = {}
        if getattr(payload, "content", None) is not None:
            updates["content"] = payload.content
        if getattr(payload, "ticket_type", None) is not None:
            updates["ticket_type"] = payload.ticket_type.value
        if getattr(payload, "semester", None) is not None:
            updates["semester"] = payload.semester
        if getattr(payload, "status", None) is not None:
            updates["status"] = payload.status
        if getattr(payload, "admin_notes", None) is not None:
            updates["admin_notes"] = payload.admin_notes

        if not updates:
            return ticket

        updates["updated_at"] = date.today()
            
        with self.engine.connect() as conn:
            set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
            sql = f"UPDATE ticket SET {set_clause} WHERE protocol = :protocol"
            params = {**updates, "protocol": protocol}
            
            conn.execute(text(sql), params)
            conn.commit()

        return self.get_ticket_by_protocol(protocol)

    def delete_ticket(self, protocol: str) -> bool:
        """Delete a ticket and its attachment owner from the database."""
        ticket = self.get_ticket_by_protocol(protocol)
        if not ticket:
            return False

        with self.engine.connect() as conn:
            conn.execute(text("DELETE FROM ticket WHERE id = :id"), {"id": ticket.id})
            conn.execute(text("DELETE FROM attachment_owner WHERE id = :id"), {"id": ticket.id})
            conn.commit()
            
        return True
