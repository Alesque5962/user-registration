import secrets
import bcrypt
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()


def verify_basic_auth(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    email: str,
    stored_password_hash: str,
) -> bool:
    """Verify basic auth credentials."""
    # input_password_hash = hashlib.sha256(credentials.password.encode()).hexdigest()
    input_password_hash = credentials.password.encode("utf-8")
    correct_email = secrets.compare_digest(credentials.username, email)
    # correct_password = secrets.compare_digest(input_password_hash, stored_password_hash)
    correct_password = bcrypt.hashpw(input_password_hash, stored_password_hash)
    return correct_email and correct_password
