"""User profile and identity endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import AuthenticatedPrincipal, get_current_user
from app.api.schemas.users import UserProfile, UserResponse
from app.db.models.user import User
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get current user profile",
    description="Returns profile information and authorized telemetry scopes for the currently authenticated principal.",
)
def get_my_profile(
    current_user: AuthenticatedPrincipal = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    """Return identity and scope of the authenticated client."""
    now = datetime.now(timezone.utc)
    try:
        user_row = db.execute(
            select(User).where(User.id == current_user.user_id)
        ).scalar_one_or_none()
        if user_row:
            user_role = user_row.role or current_user.role
            return UserProfile(
                id=user_row.id,
                username=user_row.username,
                email=user_row.email or current_user.email,
                display_name=user_row.display_name,
                role=user_role,
                is_active=user_row.is_active,
                created_at=user_row.created_at,
                roles=current_user.roles,
                authorized_scopes=list(current_user.authorized_scopes),
            )
    except Exception:
        # Fall back to principal data if DB is unavailable or user not yet in DB
        pass

    return UserProfile(
        id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
        display_name=current_user.display_name,
        role=current_user.role,
        is_active=True,
        created_at=now,
        roles=current_user.roles,
        authorized_scopes=list(current_user.authorized_scopes),
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Returns public profile for a specified user, strictly verifying that the caller is authorized for that scope.",
)
def get_user_by_id(
    user_id: str,
    current_user: AuthenticatedPrincipal = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Retrieve user profile ensuring caller has authorized scope."""
    if not current_user.is_authorized_for_user(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: You do not have permission to view profile for user '{user_id}'.",
        )

    now = datetime.now(timezone.utc)
    try:
        user_row = db.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()
        if user_row:
            return UserResponse(
                id=user_row.id,
                username=user_row.username,
                display_name=user_row.display_name,
                is_active=user_row.is_active,
                created_at=user_row.created_at,
            )
    except Exception:
        pass

    # Return profile for known authorized scope
    return UserResponse(
        id=user_id,
        username=user_id,
        display_name=f"User ({user_id})",
        is_active=True,
        created_at=now,
    )
