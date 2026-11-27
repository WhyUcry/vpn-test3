"""Migration: Add notifications table."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db import engine
from backend.models import Base, Notification
from loguru import logger


def migrate():
    """Add notifications table to database."""
    try:
        logger.info("Creating notifications table...")

        # Create only the notifications table
        Notification.__table__.create(engine, checkfirst=True)

        logger.info("✅ Notifications table created successfully")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    migrate()
