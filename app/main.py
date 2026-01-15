import bcrypt
from typing import Annotated
from datetime import datetime, UTC
from contextlib import asynccontextmanager
from psycopg.errors import UniqueViolation

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware

from .services.activation import generate_code, expiration_time
from .services.mailer import send_activation_email
from .security import security, verify_basic_auth
from .db import (
    init_pool,
    close_pool,
    wait_for_db,
    create_database_if_not_exists,
    create_users_table_if_not_exists,
    create_user,
    get_user_by_email,
    activate_user,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup event handler."""
    wait_for_db()
    create_database_if_not_exists()
    await init_pool()
    await create_users_table_if_not_exists()
    yield
    await close_pool()


app = FastAPI(lifespan=lifespan)


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/register")
async def register(email: str, password: str):
    """Register a new user."""
    bytes = password.encode("utf-8")  # converting password to array of bytes
    salt = bcrypt.gensalt()  # generating the salt
    password_hash = bcrypt.hashpw(bytes, salt)  # Hashing the password

    code = generate_code()
    expires_at = expiration_time()

    try:
        await create_user(email, password_hash, code, expires_at)
    except UniqueViolation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    send_activation_email(email, code)
    return {"message": "User created"}


@app.post("/activate")
async def activate(
    code: str,
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    """Activate a user."""
    user = await get_user_by_email(credentials.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    _, email, pwd_hash, is_active, stored_code, expires_at = user

    if is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already active",
        )

    if datetime.now(UTC) > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code expired",
        )

    if code != stored_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid code",
        )

    if not verify_basic_auth(credentials, email, pwd_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    await activate_user(email)
    return {"message": "Account activated"}
