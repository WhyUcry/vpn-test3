"""Dudonya VPN Telegram Bot."""
import asyncio
import os
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.handlers import router


# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def configure_logging():
    """Configure loguru logging."""
    logger.remove()

    # Console logging
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=LOG_LEVEL
    )

    # File logging
    Path("logs").mkdir(exist_ok=True)
    logger.add(
        "logs/bot_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )

    logger.info("Logging configured")


async def main():
    """Main bot function."""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set in environment")
        sys.exit(1)

    configure_logging()
    logger.info("Starting Dudonya VPN Bot...")

    # Initialize bot and dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()
    dp.include_router(router)

    # Start notification service in background
    from bot.notification_service import process_notifications
    notification_task = asyncio.create_task(process_notifications(bot, check_interval=10))

    # Start polling
    logger.info("Bot started, polling for updates...")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
        raise
    finally:
        # Cancel notification task
        notification_task.cancel()
        try:
            await notification_task
        except asyncio.CancelledError:
            pass

        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
