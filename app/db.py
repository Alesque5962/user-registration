import uuid
import psycopg
import os
import time
from typing import Tuple
from datetime import datetime
from psycopg import OperationalError
from psycopg.errors import UniqueViolation


def wait_for_db(retries: int = 10, delay: int = 2):
    """Wait for the database to be ready."""
    for attempt in range(retries):
        try:
            conn = psycopg.connect(
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT", "5432"),
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
            )
            conn.close()
            print("[DB] PostgreSQL is ready")
            return
        except OperationalError as e:
            print(f"[DB] Waiting for PostgreSQL... ({attempt + 1}/{retries})")
            print(e)
            time.sleep(delay)

    raise RuntimeError("PostgreSQL not available")


def create_database_if_not_exists():
    """Create the database if it doesn't exist."""
    conn = psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (os.getenv("DB_NAME"),),
    )
    exists = cur.fetchone()

    if not exists:
        cur.execute(f'CREATE DATABASE "{os.getenv("DB_NAME")}"')
        print(f"[DB] Database '{os.getenv('DB_NAME')}' created")
    else:
        print(f"[DB] Database '{os.getenv('DB_NAME')}' already exists")

    cur.close()
    conn.close()


def create_users_table_if_not_exists():
    """Create the users table if it doesn't exist."""
    conn = psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT FALSE,
            activation_code TEXT,
            activation_expires_at TIMESTAMPTZ
        );
        """
    )

    conn.commit()
    cur.close()
    conn.close()

    print("[DB] Table 'users' ready")


def get_connection():
    """Get a connection to the database."""
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def create_user(email: str, password_hash: str, code: str, expires_at: datetime):
    """Create a new user."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO users (id, email, password_hash, activation_code, activation_expires_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (str(uuid.uuid4()), email, password_hash, code, expires_at),
        )
        conn.commit()
    except UniqueViolation:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def get_user_by_email(email: str) -> Tuple[str, str, str, bool, str, datetime] | None:
    """Get a user by email."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def activate_user(email: str):
    """Activate a user."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET is_active=true WHERE email=%s",
        (email,),
    )
    conn.commit()
    cur.close()
    conn.close()
