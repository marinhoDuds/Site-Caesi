"""
Instagram Integration Service for importing and automating journal/mural posts.
"""
import json
import logging
import os
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List

from src.routes.journal.schemas import PostCreate, PostType
from src.service.journal_management.service import JournalService

logger = logging.getLogger(__name__)


class InstagramService:
    """Service for synchronizing posts from Instagram to Journal/Mural."""

    def __init__(self, journal_service: JournalService) -> None:
        self.journal_service = journal_service
        self.mock_mode = os.getenv("INSTAGRAM_MOCK_MODE", "true").lower() == "true"
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
        self.account_id = os.getenv("INSTAGRAM_ACCOUNT_ID", "")

    def _infer_post_type(self, caption: str) -> str:
        """Infer post type based on hashtags present in caption."""
        caption_lower = caption.lower()
        if "#evento" in caption_lower:
            return PostType.evento.value
        elif "#vaga" in caption_lower:
            return PostType.vaga.value
        elif "#oportunidade" in caption_lower:
            return PostType.oportunidade.value
        return PostType.aviso.value

    def _extract_title(self, caption: str) -> str:
        """Extract title from the first non-empty line of the caption."""
        lines = [line.strip() for line in caption.split("\n") if line.strip()]
        if lines:
            title = lines[0]
            title = re.sub(r"#\w+", "", title).strip()
            return title[:255] if title else "Publicação do Instagram"
        return "Publicação do Instagram"

    def fetch_instagram_posts(self) -> List[Dict[str, Any]]:
        """Fetch posts from Instagram Graph API or mock data.

        Returns
        -------
        List[Dict[str, Any]]
            List of Instagram post dictionaries containing id, caption, media_url, etc.
        """
        if self.mock_mode:
            return [
                {
                    "id": "ig_101",
                    "caption": "📢 Novo edital de monitoria aberto! Confira os requisitos no site.\n#aviso #monitoria",
                    "media_url": "https://example.com/ig_101.jpg",
                    "timestamp": "2026-07-25T10:00:00Z",
                },
                {
                    "id": "ig_102",
                    "caption": "🎉 Semat 2026 está chegando! Inscreva-se já para os minicursos.\n#evento #semat",
                    "media_url": "https://example.com/ig_102.jpg",
                    "timestamp": "2026-07-26T09:00:00Z",
                },
            ]

        if not self.access_token or not self.account_id:
            logger.warning(
                "Instagram Graph API requested, but INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_ACCOUNT_ID is missing."
            )
            return []

        url = (
            f"https://graph.facebook.com/v18.0/{self.account_id}/media"
            f"?fields=id,caption,media_type,media_url,timestamp&access_token={self.access_token}"
        )

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Site-Caesi-Backend/1.0",
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode("utf-8"))
                    posts = payload.get("data", [])
                    return posts
                logger.error(
                    f"Instagram Graph API returned non-200 status code: {response.status}"
                )
                return []
        except urllib.error.HTTPError as e:
            logger.error(f"Instagram Graph API HTTP Error {e.code}: {e.reason}")
            return []
        except urllib.error.URLError as e:
            logger.error(f"Instagram Graph API Network Error: {e.reason}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Instagram Graph API JSON Parsing Error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching Instagram posts: {e}")
            return []

    def sync_posts(self) -> Dict[str, Any]:
        """Sync Instagram posts into journal/mural, skipping existing ones."""
        ig_posts = self.fetch_instagram_posts()
        existing_posts = self.journal_service.list_posts()
        existing_captions = {p.caption for p in existing_posts if p.caption}

        imported_count = 0
        skipped_count = 0
        new_posts = []

        for item in ig_posts:
            caption = item.get("caption", "")
            if not caption or caption in existing_captions:
                skipped_count += 1
                continue

            title = self._extract_title(caption)
            post_type = self._infer_post_type(caption)

            payload = PostCreate(title=title, post_type=post_type, caption=caption)
            created_post = self.journal_service.create_post(payload)
            new_posts.append(created_post)
            imported_count += 1
            existing_captions.add(caption)

        return {
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "posts": new_posts,
        }

