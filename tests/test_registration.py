from datetime import datetime, UTC
from app.db import get_connection


def test_register_user_success(client):
    """Test successful registration."""
    response = client.post(
        "/register",
        params={
            "email": "register@test.com",
            "password": "secret",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"message": "User created"}

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT email, password_hash, is_active, activation_code, activation_expires_at "
        "FROM users WHERE email = %s",
        ("register@test.com",),
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    assert user is not None

    email, password_hash, is_active, code, expires_at = user

    assert email == "register@test.com"
    assert password_hash != "secret"
    assert is_active is False
    assert code is not None
    assert expires_at is not None
    assert expires_at > datetime.now(UTC)


def test_register_duplicate_email(client):
    """Test registration with duplicate email."""
    client.post(
        "/register",
        params={
            "email": "duplicate@test.com",
            "password": "secret",
        },
    )

    response = client.post(
        "/register",
        params={
            "email": "duplicate@test.com",
            "password": "secret",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already exists"


def test_register_activation_code_is_4_digits(client):
    """Test registration activation code is 4 digits."""
    client.post(
        "/register",
        params={"email": "digits@test.com", "password": "secret"},
    )

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT activation_code FROM users WHERE email = %s",
        ("digits@test.com",),
    )
    code = cur.fetchone()[0]
    cur.close()
    conn.close()

    assert code.isdigit()
    assert len(code) == 4
