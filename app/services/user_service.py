import bcrypt
from datetime import datetime, UTC

from ..data.repositories.user_repository import UserRepository
from .activation import generate_code, expiration_time
from .mailer import send_activation_email
from ..core.security import verify_password


class UserAlreadyExistsError(Exception):
    """Raised when user already exists."""

    pass


class UserNotFoundError(Exception):
    """Raised when user is not found."""

    pass


class InvalidCredentialsError(Exception):
    """Raised when credentials are invalid."""

    pass


class AlreadyActiveError(Exception):
    """Raised when user is already active."""

    pass


class CodeExpiredError(Exception):
    """Raised when activation code is expired."""

    pass


class InvalidCodeError(Exception):
    """Raised when activation code is invalid."""

    pass


class UserService:
    """Service layer for user operations."""

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def register_user(self, email: str, password: str) -> None:
        """
        Register a new user.

        Business logic:
        1. Hash password
        2. Generate activation code
        3. Create user in database
        4. Send activation email
        """
        # Hash password
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt)

        # Generate activation code and expiration
        code = generate_code()
        expires_at = expiration_time()

        # Create user
        try:
            user = await self.repository.create(email, password_hash, code, expires_at)
        except ValueError as e:
            raise UserAlreadyExistsError(str(e))

        # Send activation email
        send_activation_email(user.email, code)

    async def activate_user(self, email: str, password: str, code: str) -> None:
        """
        Activate user account.

        Business logic:
        1. Find user by email
        2. Verify password
        3. Check if already active
        4. Verify activation code
        5. Check expiration
        6. Activate user
        """
        # Find user
        user = await self.repository.find_by_email(email)
        if not user:
            raise UserNotFoundError(f"User with email {email} not found")

        # Verify password
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid password")

        # Check if already active
        if user.is_active:
            raise AlreadyActiveError("User is already active")

        # Check code expiration
        current_time = datetime.now(UTC)
        if user.is_activation_code_expired(current_time):
            raise CodeExpiredError("Activation code has expired")

        # Verify code
        if not user.can_activate(code, current_time):
            raise InvalidCodeError("Invalid activation code")

        # Activate user
        await self.repository.activate(email)
