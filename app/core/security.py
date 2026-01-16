import secrets
import bcrypt


def verify_password(password: str, stored_hash: bytes) -> bool:
    """
    Verify password against stored hash.

    Args:
        password: Plain text password
        stored_hash: Stored bcrypt hash

    Returns:
        True if password matches, False otherwise
    """
    password_bytes = password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, stored_hash)


def compare_digest_safe(a: str, b: str) -> bool:
    """
    Timing-safe string comparison.

    Args:
        a: First string
        b: Second string

    Returns:
        True if strings match, False otherwise
    """
    return secrets.compare_digest(a, b)
