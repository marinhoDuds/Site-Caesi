"""
API routes for Journal (Mural) management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from src.service.database import create_engine
from src.service.journal_management.service import JournalService
from src.service.instagram_management.service import InstagramService
from src.routes.journal.schemas import PostCreate, PostUpdate, PostResponse
from src.service.authentication.auth import get_current_admin

router = APIRouter(prefix="/journal", tags=["journal"])
admin_router = APIRouter(prefix="/admin/journal", tags=["admin-journal"])


def get_journal_service() -> JournalService:
    """Dependency injection for the JournalService."""
    engine = create_engine()
    return JournalService(engine)


@router.get("/", response_model=List[PostResponse])
def list_posts(
    post_type: Optional[str] = None,
    service: JournalService = Depends(get_journal_service),
) -> List[PostResponse]:
    """List all public posts (Mural) with optional filtering by type."""
    return service.list_posts(post_type)


@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    service: JournalService = Depends(get_journal_service),
) -> PostResponse:
    """Access a specific public post by ID."""
    post = service.get_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return post


@admin_router.post(
    "/", response_model=PostResponse, status_code=status.HTTP_201_CREATED
)
def create_post_admin(
    payload: PostCreate,
    service: JournalService = Depends(get_journal_service),
    _admin: dict = Depends(get_current_admin),
) -> PostResponse:
    """Create a new post (Admin only)."""
    return service.create_post(payload)


@admin_router.patch("/{post_id}", response_model=PostResponse)
def update_post_admin(
    post_id: int,
    payload: PostUpdate,
    service: JournalService = Depends(get_journal_service),
    _admin: dict = Depends(get_current_admin),
) -> PostResponse:
    """Update a post (Admin only)."""
    post = service.update_post(post_id, payload)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return post


@admin_router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post_admin(
    post_id: int,
    service: JournalService = Depends(get_journal_service),
    _admin: dict = Depends(get_current_admin),
):
    """Delete a post (Admin only)."""
    success = service.delete_post(post_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return


@admin_router.post("/sync-instagram")
def sync_instagram_posts(
    service: JournalService = Depends(get_journal_service),
    _admin: dict = Depends(get_current_admin),
):
    """Import recent Instagram posts into Journal/Mural (Admin only)."""
    ig_service = InstagramService(service)
    return ig_service.sync_posts()
