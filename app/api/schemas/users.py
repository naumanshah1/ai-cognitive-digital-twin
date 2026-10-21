"""User API schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """User representation returned by API."""

    id: str = Field(..., description="Unique stable user identifier")
    username: str = Field(..., description="Unique login handle")
    display_name: str = Field(..., description="User full or display name")
    is_active: bool = Field(True, description="Account active state")
    created_at: datetime = Field(..., description="Timestamp of registration")


class UserProfile(UserResponse):
    """Authenticated user profile with access scope."""

    roles: List[str] = Field(default_factory=lambda: ["user"], description="Assigned principal roles")
    authorized_scopes: List[str] = Field(
        default_factory=list, description="List of user IDs this principal is authorized to query"
    )
