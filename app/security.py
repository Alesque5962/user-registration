import secrets
from typing import Annotated
import hashlib

from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()


def verify_basic_auth(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    email: str,
    stored_password_hash: str,
) -> bool:
    """Verify basic auth credentials."""
    input_password_hash = hashlib.sha256(credentials.password.encode()).hexdigest()
    correct_email = secrets.compare_digest(credentials.username, email)
    correct_password = secrets.compare_digest(input_password_hash, stored_password_hash)
    return correct_email and correct_password
