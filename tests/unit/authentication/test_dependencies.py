import pytest
from fastapi import HTTPException

from src.service.authentication.dependencies import get_active_admin


class TestGetActiveAdmin:
    def test_allows_admin_without_pending_change(self):
        admin = {"id": "1", "must_change_password": False}

        result = get_active_admin(admin)

        assert result == admin

    def test_blocks_admin_with_pending_change(self):
        admin = {"id": "1", "must_change_password": True}

        with pytest.raises(HTTPException) as exc_info:
            get_active_admin(admin)

        assert exc_info.value.status_code == 403