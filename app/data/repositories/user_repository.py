import uuid
from datetime import datetime
from typing import Optional

from psycopg.errors import UniqueViolation
from psycopg_pool import AsyncConnectionPool

from ..models.user import User


class UserRepository:
    """Repository for User data access."""

    def __init__(self, pool: AsyncConnectionPool):
        self.pool = pool

    async def create(
        self,
        email: str,
        password_hash: bytes,
        activation_code: str,
        expires_at: datetime,
    ) -> User:
        """Create a new user in database."""
        user_id = uuid.uuid4()

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        INSERT INTO users (id, email, password_hash, activation_code, activation_expires_at)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            str(user_id),
                            email,
                            password_hash,
                            activation_code,
                            expires_at,
                        ),
                    )
        except UniqueViolation:
            raise ValueError(f"User with email {email} already exists")

        return User(
            id=user_id,
            email=email,
            password_hash=password_hash,
            is_active=False,
            activation_code=activation_code,
            activation_expires_at=expires_at,
        )

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email."""
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM users WHERE email=%s", (email,))
                row = await cur.fetchone()

        if not row:
            return None

        return User(
            id=row[0],
            email=row[1],
            password_hash=row[2],
            is_active=row[3],
            activation_code=row[4],
            activation_expires_at=row[5],
        )

    async def activate(self, email: str) -> None:
        """Activate user account."""
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE users SET is_active=true WHERE email=%s",
                    (email,),
                )
