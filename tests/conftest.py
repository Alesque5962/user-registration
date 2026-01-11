import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import get_connection


@pytest.fixture(scope="session")
def client():
    """Create a test client."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def cleanup_db():
    """Cleanup the database."""
    yield
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users")
    conn.commit()
    cur.close()
    conn.close()
