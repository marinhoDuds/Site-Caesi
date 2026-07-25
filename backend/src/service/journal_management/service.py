from datetime import date
from typing import List, Optional, Any
from pypika import Table, Query, Order
from sqlalchemy import Engine, text

from src.service.database import run_query
from src.routes.journal.schemas import PostCreate, PostUpdate, PostResponse

post_table = Table("post")
attachment_owner_table = Table("attachment_owner")

class JournalService:
    """Service layer for managing journal/mural posts."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def _map_row_to_response(self, row: Any) -> PostResponse:
        """Map a raw database tuple to a PostResponse schema."""
        op_id, title, post_type, created_at, updated_at, caption = row
        return PostResponse(
            id=op_id,
            title=title,
            post_type=post_type,
            created_at=created_at,
            updated_at=updated_at,
            caption=caption,
        )

    def _insert_attachment_owner(self) -> int:
        """Insert a base record into attachment_owner and return the generated ID."""
        with self.engine.connect() as conn:
            conn.execute(
                text("INSERT INTO attachment_owner (owner_type) VALUES (:t)"),
                {"t": "post"},
            )
            if self.engine.dialect.name == "sqlite":
                owner_id = conn.execute(text("SELECT last_insert_rowid()")).scalar()
            else:
                owner_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            conn.commit()
        return int(owner_id or 0)

    def create_post(self, payload: PostCreate) -> PostResponse:
        """Create a new post in the database."""
        owner_id = self._insert_attachment_owner()
        today = date.today()

        with self.engine.connect() as conn:
            conn.execute(
                text(
                    "INSERT INTO post "
                    "(id, title, post_type, created_at, caption) "
                    "VALUES (:id, :title, :type, :created_at, :caption)"
                ),
                {
                    "id": owner_id,
                    "title": payload.title,
                    "type": payload.post_type,
                    "created_at": today,
                    "caption": payload.caption,
                },
            )
            conn.commit()

        return PostResponse(
            id=owner_id,
            title=payload.title,
            post_type=payload.post_type,
            created_at=today,
            updated_at=None,
            caption=payload.caption,
        )

    def get_post(self, post_id: int) -> Optional[PostResponse]:
        """Fetch a post by its ID."""
        query = (
            Query.from_(post_table)
            .select("id", "title", "post_type", "created_at", "updated_at", "caption")
            .where(post_table.id == post_id)
        )
        result = run_query(self.engine, query)
        
        if not result:
            return None
        return self._map_row_to_response(result[0])

    def list_posts(self, post_type: Optional[str] = None) -> List[PostResponse]:
        """List all posts, optionally filtering by type, ordered by creation date descending."""
        query = Query.from_(post_table).select("id", "title", "post_type", "created_at", "updated_at", "caption")
        
        if post_type:
            query = query.where(post_table.post_type == post_type)
            
        
        query = query.orderby(post_table.created_at, order=Order.desc)
        
        result = run_query(self.engine, query)
        
        posts = []
        if result:
            for row in result:
                posts.append(self._map_row_to_response(row))
        return posts

    def update_post(self, post_id: int, payload: PostUpdate) -> Optional[PostResponse]:
        """Update an existing post."""
        post = self.get_post(post_id)
        if not post:
            return None

        updates = {}
        if payload.title is not None:
            updates["title"] = payload.title
        if payload.post_type is not None:
            updates["post_type"] = payload.post_type
        if payload.caption is not None:
            updates["caption"] = payload.caption

        if not updates:
            return post

        updates["updated_at"] = date.today()

        with self.engine.connect() as conn:
            set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
            sql = f"UPDATE post SET {set_clause} WHERE id = :id"
            params = {**updates, "id": post_id}
            
            conn.execute(text(sql), params)
            conn.commit()

        return self.get_post(post_id)

    def delete_post(self, post_id: int) -> bool:
        """Delete a post by ID. Returns True if deleted, False if not found."""
        post = self.get_post(post_id)
        if not post:
            return False
            
        with self.engine.connect() as conn:
            conn.execute(text("DELETE FROM post WHERE id = :id"), {"id": post_id})
            
            conn.execute(text("DELETE FROM attachment_owner WHERE id = :id"), {"id": post_id})
            conn.commit()
            
        return True
