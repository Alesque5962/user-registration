"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import Mock

from app.services.user_service import UserService
from app.data.repositories.user_repository import UserRepository


@pytest.fixture
def mock_repository():
    """
    Create a mock repository for testing services.
    
    This allows testing the service layer in isolation
    without requiring a real database connection.
    """
    return Mock(spec=UserRepository)


@pytest.fixture
def user_service(mock_repository):
    """
    Create a UserService instance with a mocked repository.
    
    This fixture provides a UserService ready for testing
    with all database dependencies mocked out.
    """
    return UserService(mock_repository)