import os
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

# Set env vars before importing app
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_test")
os.environ.setdefault("SUPABASE_SECRET_KEY", "sb_secret_test")

# Mock supabase before app import
import app.db as db_module

db_module.supabase = MagicMock()

from app.auth import require_org_admin, require_org_member  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def mock_supabase():
    """Reset and return the mocked supabase client."""
    db_module.supabase.reset_mock()
    return db_module.supabase


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def _fake_member(role: str) -> dict:
    """Build a fake member dict matching the shape returned by require_org_member."""
    return {
        "id": "user-123",
        "email": "dev@example.com",
        "user_metadata": {},
        "membership": {
            "id": "membership-1",
            "org_id": "org-1",
            "user_id": "user-db-id",
            "role": role,
        },
        "user_db_id": "user-db-id",
    }


@pytest.fixture
def as_org_owner():
    """Override require_org_member/admin to simulate an org owner."""
    app.dependency_overrides[require_org_member] = lambda: _fake_member("owner")
    app.dependency_overrides[require_org_admin] = lambda: _fake_member("owner")
    yield
    app.dependency_overrides.pop(require_org_member, None)
    app.dependency_overrides.pop(require_org_admin, None)


@pytest.fixture
def as_org_member():
    """Override require_org_member to simulate a regular member (non-admin).

    Does NOT override require_org_admin — admin-only endpoints will still 403.
    """
    app.dependency_overrides[require_org_member] = lambda: _fake_member("member")
    yield
    app.dependency_overrides.pop(require_org_member, None)
