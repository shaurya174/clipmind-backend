from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
import hashlib

# Configure Argon2id password hasher
password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """
    Hash a plain text password using Argon2id.
    """

    if not password or not password.strip():
        raise ValueError("Password cannot be empty.")

    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a plain text password against its Argon2id hash.
    """

    try:
        return password_hasher.verify(password_hash, password)

    except (VerifyMismatchError, VerificationError):
        return False
    
def hash_token(token: str) -> str:
    """
    Returns a SHA-256 hash of a token for secure database storage.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
