from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from ..schemas.user import UserRegistration, UserActivation
from ..schemas.common import MessageResponse
from ...services.user_service import (
    UserService,
    UserAlreadyExistsError,
    UserNotFoundError,
    InvalidCredentialsError,
    AlreadyActiveError,
    CodeExpiredError,
    InvalidCodeError,
)
from ...data.repositories.user_repository import UserRepository
from ...data.db import get_pool


router = APIRouter(prefix="/users", tags=["Users"])
security = HTTPBasic()


def get_user_repository() -> UserRepository:
    """Dependency to get user repository."""
    pool = get_pool()
    return UserRepository(pool)


def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    """Dependency to get user service."""
    return UserService(repository)


@router.post(
    "/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserRegistration,
    service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Register a new user.

    - **email**: User email address
    - **password**: User password (min 8 characters)

    Returns a success message and sends activation code by email.
    """
    try:
        await service.register_user(user_data.email, user_data.password)
        return MessageResponse(message="User created")
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )


@router.post("/activate", response_model=MessageResponse)
async def activate(
    activation_data: UserActivation,
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Activate user account.

    - **code**: 4-digit activation code received by email
    - **HTTP Basic Auth**: Username (email) and password

    Returns a success message if activation succeeds.
    """
    try:
        await service.activate_user(
            credentials.username,
            credentials.password,
            activation_data.code,
        )
        return MessageResponse(message="Account activated")

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    except AlreadyActiveError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already active",
        )

    except CodeExpiredError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code expired",
        )

    except InvalidCodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid code",
        )
