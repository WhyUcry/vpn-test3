"""Pydantic schemas for API validation."""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class SubscriptionInfo(BaseModel):
    """Subscription information response."""
    token: str
    status: str
    expires_at: datetime
    base_devices: int
    extra_devices: int
    total_devices: int

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"


class RotateResponse(BaseModel):
    """Rotation response."""
    success: bool
    message: str
    rotated_slots: Optional[list[int]] = None
