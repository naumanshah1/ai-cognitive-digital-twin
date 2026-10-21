"""Standard API error schemas."""

from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized API error response format."""

    error_code: str = Field(..., description="Machine-readable error classification")
    message: str = Field(..., description="Safe, human-readable error description")
    request_id: Optional[str] = Field(None, description="Correlated request identifier")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC timestamp of the error",
    )
    details: Optional[dict[str, Any]] = Field(
        None, description="Optional safe supplementary details (no secrets or stack traces)"
    )
