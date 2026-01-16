from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import users
from app.core.utils import get_settings
from app.data.db import (
    init_pool,
    close_pool,
    wait_for_db,
    create_database_if_not_exists,
    create_users_table_if_not_exists,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    wait_for_db()
    create_database_if_not_exists()
    await init_pool()
    await create_users_table_if_not_exists()
    yield
    # Shutdown
    await close_pool()


app = FastAPI(
    title=get_settings().api_title,
    description=get_settings().api_description,
    version=get_settings().api_version,
    lifespan=lifespan,
)


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(users.router)
