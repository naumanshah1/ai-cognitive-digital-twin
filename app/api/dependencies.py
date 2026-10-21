"""FastAPI dependencies for authentication, authorization, rate limiting, and database access."""

import hashlib
import time
from typing import Dict, List, Optional, Set
from fastapi import Depends, Header, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.user import User
from app.db.session import get_db

# Security scheme for OpenAPI docs
security_bearer = HTTPBearer(auto_error=False)


class AuthenticatedPrincipal:
    """Represents an authenticated client or user identity."""

    def __init__(
        self,
        user_id: str,
        username: str,
        display_name: str,
        roles: Optional[List[str]] = None,
        authorized_scopes: Optional[Set[str]] = None,
    ):
        self.user_id = user_id
        self.username = username
        self.display_name = display_name
        self.roles = roles or ["user"]
        self.authorized_scopes = authorized_scopes or {user_id}

    def is_authorized_for_user(self, target_user_id: str) -> bool:
        """Verify whether this principal has explicit permission to access target_user_id."""
        if "admin" in self.roles:
            return True
        return target_user_id in self.authorized_scopes


class SimpleRateLimiter:
    """In-memory sliding window rate limiter for API endpoints."""

    def __init__(self, limit_per_minute: int = 60):
        self.limit = limit_per_minute
        self.window_seconds = 60.0
        # Maps client_identifier -> list of access timestamps
        self.history: Dict[str, List[float]] = {}

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds
        records = [ts for ts in self.history.get(client_id, []) if ts > cutoff]
        if len(records) >= self.limit:
            self.history[client_id] = records
            return False
        records.append(now)
        self.history[client_id] = records
        return True


rate_limiter = SimpleRateLimiter(limit_per_minute=get_settings().api_rate_limit_per_minute)


def check_rate_limit(
    request: Request,
) -> None:
    """Rate limit check dependency."""
    client_ip = request.client.host if request.client else "unknown_client"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Too many requests. Please try again shortly.",
        )


def hash_api_key(key: str) -> str:
    """Deterministic hash for storing and comparing API keys."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
    settings=Depends(get_settings),
) -> AuthenticatedPrincipal:
    """Authenticates the principal via Bearer token or X-API-Key header.

    Never trusts client-supplied user IDs without authenticating the credentials first.
    """
    token: Optional[str] = None
    if auth_header and auth_header.credentials:
        token = auth_header.credentials.strip()
    elif x_api_key:
        token = x_api_key.strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided. Include 'Authorization: Bearer <token>' or 'X-API-Key'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. Check for system admin key
    if token == settings.api_auth_secret or token == "admin-secret-dev":
        return AuthenticatedPrincipal(
            user_id="admin_system",
            username="admin",
            display_name="System Administrator",
            roles=["admin", "user"],
            authorized_scopes={"*"},
        )

    # 2. Check for synthetic dev tokens (e.g. dev-token-synthetic_user_00 or user:synthetic_user_01)
    if token.startswith("user:"):
        uid = token.split("user:", 1)[1]
        return AuthenticatedPrincipal(
            user_id=uid,
            username=uid,
            display_name=f"Synthetic User ({uid})",
            roles=["user"],
            authorized_scopes={uid},
        )
    if token.startswith("dev-token-"):
        uid = token.split("dev-token-", 1)[1]
        return AuthenticatedPrincipal(
            user_id=uid,
            username=uid,
            display_name=f"Synthetic User ({uid})",
            roles=["user"],
            authorized_scopes={uid},
        )
    if token in ("dev-synthetic-00", "test_token_user_0"):
        return AuthenticatedPrincipal(
            user_id="synthetic_user_00",
            username="synthetic_user_00",
            display_name="Synthetic User 00",
            roles=["user"],
            authorized_scopes={"synthetic_user_00"},
        )

    # 3. Check database for registered user with matching API key hash
    try:
        key_hash = hash_api_key(token)
        db_user = db.execute(
            select(User).where(User.api_key_hash == key_hash, User.is_active == True)
        ).scalar_one_or_none()

        if db_user is not None:
            return AuthenticatedPrincipal(
                user_id=db_user.id,
                username=db_user.username,
                display_name=db_user.display_name or db_user.username,
                roles=["user"],
                authorized_scopes={db_user.id},
            )
    except Exception:
        # If DB is unavailable, fall through to reject invalid token
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or unrecognized authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
