#!/usr/bin/env python3
"""Initialize database - create tables and optionally add test data."""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db import init_db, SessionLocal
from backend.models import User, Subscription, SubscriptionStatus
from backend.slot_generator import create_device_slots
from datetime import datetime, timedelta
from loguru import logger
import uuid


def create_test_data():
    """Create test user and subscription for development."""
    db = SessionLocal()

    try:
        # Check if test user exists
        test_user = db.query(User).filter(User.telegram_id == 123456789).first()

        if test_user:
            logger.info("Test user already exists")
        else:
            # Create test user
            test_user = User(
                telegram_id=123456789,
                username="test_user"
            )
            db.add(test_user)
            db.commit()
            logger.info(f"Created test user: {test_user.username} (ID: {test_user.id})")

        # Create test subscription
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=30)

        subscription = Subscription(
            user_id=test_user.id,
            token=token,
            status=SubscriptionStatus.ACTIVE,
            base_devices=1,
            extra_devices=0,
            expires_at=expires_at
        )
        db.add(subscription)
        db.commit()

        # Create device slots
        create_device_slots(db, subscription.id, subscription.base_devices)

        logger.info(f"Created test subscription:")
        logger.info(f"  Token: {token}")
        logger.info(f"  URL: http://localhost:8000/sub/{token}")
        logger.info(f"  Expires: {expires_at.isoformat()}")
        logger.info(f"  Devices: {subscription.base_devices}")

        return token

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create test data: {e}")
        raise

    finally:
        db.close()


def main():
    """Main function."""
    logger.info("Initializing database...")

    # Initialize database
    init_db()
    logger.info("Database tables created successfully")

    # Ask if user wants to create test data
    if "--test-data" in sys.argv:
        logger.info("Creating test data...")
        token = create_test_data()
        logger.success(f"Database initialized with test data. Test subscription token: {token}")
    else:
        logger.success("Database initialized successfully")
        logger.info("Run with --test-data flag to create test user and subscription")


if __name__ == "__main__":
    main()
