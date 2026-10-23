"""Security primitives for password hashing, verification, and signed token handling."""

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Dict, Optional

from app.core.config import get_settings


def _b64encode(data: bytes) -> str:
    """URL-safe base64 encoding without trailing padding."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode(data: str) -> bytes:
    """URL-safe base64 decoding with restored padding."""
    rem = len(data) % 4
    if rem > 0:
        data += "=" * (4 - rem)
    return base64.urlsafe_b64decode(data.encode("utf-8"))


# --- Password Hashing (OWASP PBKDF2-HMAC-SHA256) ---

ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """Hashes a plaintext password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    if not password:
        raise ValueError("Password cannot be empty")
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS,
    )
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${key.hex()}"


# Convenient alias
get_password_hash = hash_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored PBKDF2-HMAC-SHA256 hash in constant time."""
    if not plain_password or not hashed_password:
        return False
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_key = bytes.fromhex(parts[3])

        candidate_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(candidate_key, expected_key)
    except Exception:
        return False


# --- Signed JWT Token Handling (HS256) ---

DEFAULT_EXPIRATION_SECONDS = 86400 * 7  # 7 days


def create_access_token(
    payload: Dict[str, Any],
    expires_delta: Optional[float] = None,
) -> str:
    """Generates a standard HS256-signed JWT token."""
    settings = get_settings()
    now = time.time()
    exp = now + (expires_delta if expires_delta is not None else DEFAULT_EXPIRATION_SECONDS)

    header = {"alg": "HS256", "typ": "JWT"}
    token_claims = {
        **payload,
        "iat": int(now),
        "exp": int(exp),
    }

    header_b64 = _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64encode(json.dumps(token_claims, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    secret = settings.api_auth_secret.encode("utf-8")
    sig = hmac.new(secret, signing_input, hashlib.sha256).digest()
    sig_b64 = _b64encode(sig)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Validates the HMAC-SHA256 signature and expiration of a JWT token."""
    if not token or not isinstance(token, str):
        return None
    parts = token.strip().split(".")
    if len(parts) != 3:
        return None

    header_b64, payload_b64, sig_b64 = parts
    settings = get_settings()
    secret = settings.api_auth_secret.encode("utf-8")
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(secret, signing_input, hashlib.sha256).digest()

    try:
        actual_sig = _b64decode(sig_b64)
        if not hmac.compare_digest(actual_sig, expected_sig):
            return None

        claims = json.loads(_b64decode(payload_b64).decode("utf-8"))
        # Validate expiration
        exp = claims.get("exp")
        if exp is not None and time.time() > float(exp):
            return None

        return claims
    except Exception:
        return None
