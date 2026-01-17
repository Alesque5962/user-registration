import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4
from unittest.mock import AsyncMock

from app.services.user_service import (
    UserAlreadyExistsError,
    UserNotFoundError,
    InvalidCredentialsError,
    AlreadyActiveError,
    CodeExpiredError,
    InvalidCodeError,
)
from app.data.models.user import User


@pytest.mark.asyncio
async def test_register_user_success(user_service, mock_repository):
    """Test successful user registration."""
    # Arrange
    email = "test@example.com"
    password = "password123"

    mock_repository.create = AsyncMock(
        return_value=User(
            id=uuid4(),
            email=email,
            password_hash=b"password123_hashed",
            is_active=False,
            activation_code="1234",
            activation_expires_at=datetime.now(UTC) + timedelta(minutes=1),
        )
    )

    # Act
    await user_service.register_user(email, password)

    # Assert
    mock_repository.create.assert_called_once()
    args = mock_repository.create.call_args[0]
    assert args[0] == email
    assert len(args[2]) == 4  # activation code


@pytest.mark.asyncio
async def test_register_user_already_exists(user_service, mock_repository):
    """Test registration with existing email."""
    # Arrange
    mock_repository.create = AsyncMock(side_effect=ValueError("User exists"))

    # Act & Assert
    with pytest.raises(UserAlreadyExistsError):
        await user_service.register_user("test@example.com", "password123")


@pytest.mark.asyncio
async def test_activate_user_success(user_service, mock_repository):
    """Test successful user activation."""
    # Arrange
    email = "test@example.com"
    password = "password123"
    code = "1234"

    # Create a user with valid activation code
    import bcrypt

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    user = User(
        id=uuid4(),
        email=email,
        password_hash=password_hash,
        is_active=False,
        activation_code=code,
        activation_expires_at=datetime.now(UTC) + timedelta(minutes=1),
    )

    mock_repository.find_by_email = AsyncMock(return_value=user)
    mock_repository.activate = AsyncMock()

    # Act
    await user_service.activate_user(email, password, code)

    # Assert
    mock_repository.find_by_email.assert_called_once_with(email)
    mock_repository.activate.assert_called_once_with(email)


@pytest.mark.asyncio
async def test_activate_user_not_found(user_service, mock_repository):
    """Test activation with non-existent user."""
    # Arrange
    mock_repository.find_by_email = AsyncMock(return_value=None)

    # Act & Assert
    with pytest.raises(UserNotFoundError):
        await user_service.activate_user("test@example.com", "password123", "1234")


@pytest.mark.asyncio
async def test_activate_user_invalid_password(user_service, mock_repository):
    """Test activation with wrong password."""
    # Arrange
    import bcrypt

    password_hash = bcrypt.hashpw(b"correct_password", bcrypt.gensalt())

    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash=password_hash,
        is_active=False,
        activation_code="1234",
        activation_expires_at=datetime.now(UTC) + timedelta(minutes=1),
    )

    mock_repository.find_by_email = AsyncMock(return_value=user)

    # Act & Assert
    with pytest.raises(InvalidCredentialsError):
        await user_service.activate_user("test@example.com", "wrong_password", "1234")


@pytest.mark.asyncio
async def test_activate_user_already_active(user_service, mock_repository):
    """Test activation of already active user."""
    # Arrange
    import bcrypt

    password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt())

    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash=password_hash,
        is_active=True,  # Already active
        activation_code="1234",
        activation_expires_at=datetime.now(UTC) + timedelta(minutes=1),
    )

    mock_repository.find_by_email = AsyncMock(return_value=user)

    # Act & Assert
    with pytest.raises(AlreadyActiveError):
        await user_service.activate_user("test@example.com", "password123", "1234")


@pytest.mark.asyncio
async def test_activate_user_expired_code(user_service, mock_repository):
    """Test activation with expired code."""
    # Arrange
    import bcrypt

    password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt())

    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash=password_hash,
        is_active=False,
        activation_code="1234",
        activation_expires_at=datetime.now(UTC) - timedelta(minutes=1),  # Expired
    )

    mock_repository.find_by_email = AsyncMock(return_value=user)

    # Act & Assert
    with pytest.raises(CodeExpiredError):
        await user_service.activate_user("test@example.com", "password123", "1234")


@pytest.mark.asyncio
async def test_activate_user_invalid_code(user_service, mock_repository):
    """Test activation with wrong code."""
    # Arrange
    import bcrypt

    password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt())

    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash=password_hash,
        is_active=False,
        activation_code="1234",
        activation_expires_at=datetime.now(UTC) + timedelta(minutes=1),
    )

    mock_repository.find_by_email = AsyncMock(return_value=user)

    # Act & Assert
    with pytest.raises(InvalidCodeError):
        await user_service.activate_user(
            "test@example.com", "password123", "9999"
        )  # Wrong code
