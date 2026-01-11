import random
from datetime import datetime, timedelta, UTC


def generate_code() -> str:
    """Generate a random 4 digits code."""
    return str(random.randint(1000, 9999))


def expiration_time() -> datetime:
    """Return the expiration time for the activation code."""
    return datetime.now(UTC) + timedelta(minutes=1)
