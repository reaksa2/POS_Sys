"""Password hashing helpers (standard library only, no extra dependency).

Stored format:  pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>

Older databases kept passwords in plain text. `is_hashed()` lets the database
layer detect those rows and upgrade them automatically on startup.
"""
import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 200_000


def is_hashed(stored):
    return isinstance(stored, str) and stored.startswith(ALGORITHM + "$")


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), ITERATIONS)
    return f"{ALGORITHM}${ITERATIONS}${salt}${digest.hex()}"


def verify_password(password, stored):
    """Returns True if `password` matches `stored` (hashed, or legacy plain text)."""
    if stored is None or password is None:
        return False
    if not is_hashed(stored):
        # Legacy plain-text value — constant-time compare
        return hmac.compare_digest(str(stored), str(password))
    try:
        _, iterations, salt, expected = stored.split("$", 3)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False
