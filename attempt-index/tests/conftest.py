from dotenv import load_dotenv

load_dotenv()  # must run before any app import so pydantic-settings picks up .env

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.client import get_client  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def db():
    return get_client()


@pytest.fixture
def cleanup_db(db):
    """Delete test records after each integration test. Request this fixture explicitly."""
    yield
    # record_frontiers FK must be removed before attempt_records rows
    db.table("record_frontiers").delete().like("submission_id", "test:%").execute()
    db.table("record_frontiers").delete().like("submission_id", "bootstrap:test:%").execute()
    db.table("record_frontiers").delete().like("frontier_id", "test-%").execute()
    db.table("attempt_records").delete().like("submission_id", "test:%").execute()
    db.table("attempt_records").delete().like("submission_id", "bootstrap:test:%").execute()
    db.table("frontiers").delete().like("frontier_id", "test-%").execute()
