from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class User:
    """User domain model."""

    id: UUID
    email: str
    password_hash: bytes
    is_active: bool
    activation_code: str | None
    activation_expires_at: datetime | None

    def is_activation_code_expired(self, current_time: datetime) -> bool:
        """Check if activation code is expired."""
        if not self.activation_expires_at:
            return True
        return current_time > self.activation_expires_at

    def can_activate(self, code: str, current_time: datetime) -> bool:
        """Check if user can be activated with given code."""
        if self.is_active:
            return False
        if self.is_activation_code_expired(current_time):
            return False
        return code == self.activation_code
