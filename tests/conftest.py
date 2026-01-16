import pytest
from unittest.mock import Mock
from app.data.repositories.user_repository import UserRepository
from app.services.user_service import UserService


@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    return Mock(spec=UserRepository)


@pytest.fixture
def user_service(mock_repository):
    """Create a user service with mock repository."""
    return UserService(mock_repository)
