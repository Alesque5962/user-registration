import psycopg
import time
from psycopg import OperationalError
from psycopg_pool import AsyncConnectionPool
from app.core.utils import get_settings

pool: AsyncConnectionPool | None = None


def wait_for_db(retries: int = 10, delay: int = 2):
    """Wait for the database to be ready."""
    for attempt in range(retries):
        try:
            conn = psycopg.connect(
                host=get_settings().db_host,
                port=get_settings().db_port,
                dbname=get_settings().db_name,
                user=get_settings().db_user,
                password=get_settings().db_password,
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
        f"host={get_settings().db_host} "
        f"port={get_settings().db_port} "
        f"dbname={get_settings().db_name} "
        f"user={get_settings().db_user} "
        f"password={get_settings().db_password}"
    )


async def init_pool():
    global pool
    pool = AsyncConnectionPool(
        conninfo=make_conninfo(),
        min_size=get_settings().db_pool_min_size,
        max_size=get_settings().db_pool_max_size,
        timeout=get_settings().db_pool_timeout,
        open=False,
    )
    await pool.open()


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
        host=get_settings().db_host,
        port=get_settings().db_port,
        dbname=get_settings().db_name,
        user=get_settings().db_user,
        password=get_settings().db_password,
    )
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (get_settings().db_name,),
    )
    exists = cur.fetchone()

    if not exists:
        cur.execute(f'CREATE DATABASE "{get_settings().db_name}"')
        print(f"[DB] Database '{get_settings().db_name}' created")
    else:
        print(f"[DB] Database '{get_settings().db_name}' already exists")

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
