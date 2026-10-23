"""Authentication and account lifecycle endpoints."""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.dependencies import AuthenticatedPrincipal, get_current_user
from app.api.schemas.auth import AuthResponse, ChangePasswordRequest, LoginRequest, RegisterRequest
from app.api.schemas.users import UserProfile
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.user import User
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new personal user account",
    description="Creates a new standard user account with secure password hashing. Always assigns standard 'user' role.",
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """Register a new user account with secure hashed password."""
    email_clean = payload.email.strip().lower()

    # 1. Check for existing account by email
    existing_user = db.execute(
        select(User).where(User.email == email_clean)
    ).scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    # 2. Derive or validate unique username and stable user ID
    if payload.username:
        clean_username = payload.username.strip()
        existing_username = db.execute(
            select(User).where(User.username == clean_username)
        ).scalar_one_or_none()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username is already taken. Please choose another username.",
            )
        username = clean_username
    else:
        base_username = email_clean.split("@")[0].replace(".", "_")[:32]
        unique_suffix = uuid.uuid4().hex[:6]
        username = f"{base_username}_{unique_suffix}"
    user_id = f"usr_{uuid.uuid4().hex[:12]}"

    # 3. Create user record
    new_user = User(
        id=user_id,
        username=username,
        email=email_clean,
        display_name=payload.name.strip(),
        hashed_password=hash_password(payload.password),
        role="user",
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 4. Generate signed access token
    token = create_access_token({
        "sub": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "role": new_user.role,
        "display_name": new_user.display_name,
    })

    user_profile = UserProfile(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        display_name=new_user.display_name,
        role=new_user.role,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        roles=[new_user.role],
        authorized_scopes=[new_user.id],
    )

    return AuthResponse(
        access_token=token,
        token=token,
        token_type="Bearer",
        user=user_profile,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Authenticate with email and password",
    description="Validates credentials and returns a signed JWT access token for session authorization.",
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """Authenticate user credentials and issue signed session token."""
    identifier = payload.email.strip().lower()

    # Lookup by email or username
    user = db.execute(
        select(User).where(
            or_(
                User.email == identifier,
                User.username == identifier,
            ),
            User.is_active == True,
        )
    ).scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate token
    user_role = user.role or "user"
    is_admin = (user_role == "admin")

    token = create_access_token({
        "sub": user.id,
        "username": user.username,
        "email": user.email,
        "role": user_role,
        "display_name": user.display_name,
    })

    roles_list = ["admin", "user"] if is_admin else [user_role]
    scopes_list = ["*"] if is_admin else [user.id]

    user_profile = UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        role=user_role,
        is_active=user.is_active,
        created_at=user.created_at,
        roles=roles_list,
        authorized_scopes=scopes_list,
    )

    return AuthResponse(
        access_token=token,
        token=token,
        token_type="Bearer",
        user=user_profile,
    )


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get verified session profile",
    description="Returns profile information and verified role for the current authenticated principal.",
)
def get_current_session(
    current_user: AuthenticatedPrincipal = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    """Retrieve verified profile of the authenticated session."""
    now = datetime.now(timezone.utc)
    try:
        user_row = db.get(User, current_user.user_id)
        if user_row:
            user_role = user_row.role or current_user.role
            return UserProfile(
                id=user_row.id,
                username=user_row.username,
                email=user_row.email or current_user.email,
                display_name=user_row.display_name or current_user.display_name,
                role=user_role,
                is_active=user_row.is_active,
                created_at=user_row.created_at,
                roles=current_user.roles,
                authorized_scopes=list(current_user.authorized_scopes),
            )
    except Exception:
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


@router.post(
    "/logout",
    summary="Terminate session",
    description="Confirms session termination for the authenticated principal.",
)
def logout(
    current_user: AuthenticatedPrincipal = Depends(get_current_user),
) -> dict[str, str]:
    """Logout endpoint acknowledging session termination."""
    return {"message": "Logged out successfully", "user_id": current_user.user_id}


@router.post(
    "/change-password",
    summary="Change account password",
    description="Allows authenticated user to update their account password after validating their current password.",
)
def change_password(
    payload: ChangePasswordRequest,
    current_user: AuthenticatedPrincipal = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Secure password change for authenticated users."""
    user = db.get(User, current_user.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found.",
        )

    if not user.hashed_password or not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password.",
        )

    user.hashed_password = hash_password(payload.new_password)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Password changed successfully."}

