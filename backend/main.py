"""FastAPI backend for Dudonya VPN subscriptions."""
import sys
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger

from backend.db import get_db_session, init_db
from backend.schemas import HealthResponse, RotateResponse
from backend.subscription import (
    generate_subscription_response,
    SubscriptionNotFoundError,
    SubscriptionExpiredError
)


# Configure loguru
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=os.getenv("LOG_LEVEL", "INFO")
)
logger.add(
    "logs/backend_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

# Initialize FastAPI
app = FastAPI(
    title="Dudonya VPN Backend",
    description="VPN subscription service with multi-device support",
    version="1.0.0"
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info("Starting Dudonya VPN Backend...")

    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    # Create data directory for SQLite
    Path("data").mkdir(exist_ok=True)

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    logger.info("Backend started successfully")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns service status and version.
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@app.get("/sub/{token}")
@limiter.limit("10/minute")
async def get_subscription(
    token: str,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Get VPN subscription by token.

    Returns subscription configs with proper headers for VPN apps.

    Headers:
    - profile-title: Дудоня VPN
    - profile-update-interval: 12
    - subscription-userinfo: upload=0; download=0; total=0; expire=<unix_ts>
    - Content-Type: text/plain; charset=utf-8
    - Cache-Control: no-store

    Args:
        token: Subscription token (UUID)
        request: FastAPI request object (for rate limiting)
        db: Database session

    Returns:
        Response with subscription configs (base64 or plain text)

    Raises:
        HTTPException: 404 if not found, 403 if expired/inactive
    """
    logger.info(f"Subscription request: token={token[:8]}..., ip={get_remote_address(request)}")

    try:
        content, headers = generate_subscription_response(db, token)

        return Response(
            content=content,
            media_type=headers["Content-Type"],
            headers=headers
        )

    except SubscriptionNotFoundError:
        logger.warning(f"Subscription not found: {token[:8]}...")
        raise HTTPException(status_code=404, detail="Subscription not found")

    except SubscriptionExpiredError as e:
        logger.warning(f"Subscription expired/inactive: {token[:8]}... - {e}")
        raise HTTPException(status_code=403, detail=str(e))

    except Exception as e:
        logger.error(f"Error generating subscription {token[:8]}...: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/sub/{token}/rotate", response_model=RotateResponse)
@limiter.limit("5/hour")
async def rotate_subscription(
    token: str,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """
    Rotate device slot UUIDs for a subscription.

    This is an admin endpoint (should be protected by API key in production).
    Regenerates UUIDs for all device slots.

    Args:
        token: Subscription token (UUID)
        request: FastAPI request object (for rate limiting)
        db: Database session

    Returns:
        RotateResponse with success status

    Raises:
        HTTPException: 404 if not found
    """
    logger.warning(f"Rotation requested for subscription {token[:8]}...")

    # TODO: Add API key authentication for admin endpoints

    from backend.models import Subscription
    from backend.slot_generator import generate_stable_uuid, generate_short_id

    # Find subscription
    subscription = db.query(Subscription).filter(Subscription.token == token).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Regenerate UUIDs for all slots
    rotated_slots = []
    for slot in subscription.device_slots:
        # Generate new UUIDs with different seed
        new_uuid = generate_stable_uuid(
            subscription.id,
            slot.slot_index,
            seed=f"rotated-{datetime.utcnow().isoformat()}"
        )
        new_short_id = generate_short_id(subscription.id, slot.slot_index)

        slot.uuid = new_uuid
        slot.short_id = new_short_id
        rotated_slots.append(slot.slot_index)

        logger.info(f"Rotated slot {slot.slot_index}: new uuid={new_uuid[:8]}...")

    db.commit()

    return RotateResponse(
        success=True,
        message=f"Rotated {len(rotated_slots)} device slots",
        rotated_slots=rotated_slots
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting uvicorn server on {host}:{port}")

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
