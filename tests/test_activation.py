import base64
import hashlib
from datetime import datetime, timedelta, UTC

from app.db import create_user, activate_user


def basic_auth(email: str, password: str):
    """Generate HTTP Basic Auth header."""
    token = base64.b64encode(f"{email}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_activate_success(client):
    """Test successful activation."""
    email = "success@test.com"
    password = "secret"
    code = "1234"

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    create_user(
        email=email,
        password_hash=password_hash,
        code=code,
        expires_at=datetime.now(UTC) + timedelta(seconds=30),
    )

    response = client.post(
        f"/activate?code={code}",
        headers=basic_auth(email, password),
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Account activated"}


def test_activate_wrong_code(client):
    """Test activation with wrong code."""
    email = "wrongcode@test.com"
    password = "secret"

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    create_user(
        email=email,
        password_hash=password_hash,
        code="9999",
        expires_at=datetime.now(UTC) + timedelta(seconds=30),
    )

    response = client.post(
        "/activate?code=0000",
        headers=basic_auth(email, password),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid code"


def test_activate_expired_code(client):
    """Test activation with expired code."""
    email = "expired@test.com"
    password = "secret"
    code = "1111"

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    create_user(
        email=email,
        password_hash=password_hash,
        code=code,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    response = client.post(
        f"/activate?code={code}",
        headers=basic_auth(email, password),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Code expired"


def test_activate_wrong_password(client):
    """Test activation with wrong password."""
    email = "wrongpass@test.com"
    password = "correct"

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    create_user(
        email=email,
        password_hash=password_hash,
        code="2222",
        expires_at=datetime.now(UTC) + timedelta(seconds=30),
    )

    response = client.post(
        "/activate?code=2222",
        headers=basic_auth(email, "incorrect"),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_activate_user_not_found(client):
    """Test activation with non-existent user."""
    response = client.post(
        "/activate?code=1234",
        headers=basic_auth("unknown@test.com", "secret"),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_activate_already_active(client):
    """Test activation with already active user."""
    email = "active@test.com"
    password = "secret"
    code = "3333"

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    create_user(
        email=email,
        password_hash=password_hash,
        code=code,
        expires_at=datetime.now(UTC) + timedelta(seconds=30),
    )

    activate_user(email)

    response = client.post(
        f"/activate?code={code}",
        headers=basic_auth(email, password),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Already active"
