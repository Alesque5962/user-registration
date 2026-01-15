import uuid
import psycopg
import os
import time
from typing import Tuple
from datetime import datetime
from psycopg import OperationalError
from psycopg.errors import UniqueViolation
from psycopg_pool import AsyncConnectionPool

pool: AsyncConnectionPool | None = None


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


def make_conninfo() -> str:
    return (
        f"host={os.getenv('DB_HOST')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.getenv('DB_NAME')} "
        f"user={os.getenv('DB_USER')} "
        f"password={os.getenv('DB_PASSWORD')}"
    )


async def init_pool():
    global pool
    pool = AsyncConnectionPool(
        conninfo=make_conninfo(),
        min_size=2,
        max_size=10,
        timeout=30,
        open=True,
    )


async def close_pool():
    if pool:
        await pool.close()


def get_pool() -> AsyncConnectionPool:
    if pool is None:
        raise RuntimeError("Database pool not initialized")
    return pool


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


async def create_users_table_if_not_exists():
    """Create the users table if it doesn't exist."""
    async with get_pool().connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash BYTEA NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT FALSE,
                    activation_code TEXT,
                    activation_expires_at TIMESTAMPTZ
                );
                """
            )

    print("[DB] Table 'users' ready")


async def create_user(email: str, password_hash: str, code: str, expires_at: datetime):
    """Create a new user."""
    try:
        async with get_pool().connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                INSERT INTO users (id, email, password_hash, activation_code, activation_expires_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
                    (str(uuid.uuid4()), email, password_hash, code, expires_at),
                )
    except UniqueViolation:
        raise


async def get_user_by_email(
    email: str,
) -> Tuple[str, str, str, bool, str, datetime] | None:
    """Get a user by email."""
    async with get_pool().connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            row = await cur.fetchone()
    return row


async def activate_user(email: str):
    """Activate a user."""
    async with get_pool().connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE users SET is_active=true WHERE email=%s",
                (email,),
            )
