"""Notification service for sending messages to users."""
import asyncio
import json
from datetime import datetime
from typing import Optional
from loguru import logger

from aiogram import Bot
from sqlalchemy.orm import Session

from backend.db import SessionLocal
from backend.models import Notification, NotificationType


async def process_notifications(bot: Bot, check_interval: int = 10):
    """
    Background task to process pending notifications.

    Args:
        bot: Bot instance
        check_interval: Interval in seconds between checks
    """
    logger.info("Notification service started")

    while True:
        try:
            await _check_and_send_notifications(bot)
        except Exception as e:
            logger.error(f"Error processing notifications: {e}", exc_info=True)

        await asyncio.sleep(check_interval)


async def _check_and_send_notifications(bot: Bot):
    """Check for pending notifications and send them."""
    db = SessionLocal()
    try:
        # Get pending notifications
        notifications = db.query(Notification).filter(
            Notification.sent == 0
        ).order_by(Notification.created_at).limit(10).all()

        if not notifications:
            return

        logger.info(f"Found {len(notifications)} pending notifications")

        for notification in notifications:
            success = await _send_notification(bot, db, notification)

            if success:
                notification.sent = 1
                notification.sent_at = datetime.utcnow()
            else:
                notification.sent = 2  # Failed

            db.commit()

            # Small delay between messages
            await asyncio.sleep(0.5)

    finally:
        db.close()


async def _send_notification(bot: Bot, db: Session, notification: Notification) -> bool:
    """
    Send a single notification.

    Args:
        bot: Bot instance
        db: Database session
        notification: Notification object

    Returns:
        True if sent successfully
    """
    try:
        if notification.type == NotificationType.PAYMENT_SUCCESS:
            return await _send_payment_success(bot, notification)

        elif notification.type == NotificationType.SUBSCRIPTION_EXTENDED:
            return await _send_subscription_extended(bot, notification)

        elif notification.type == NotificationType.DEVICE_ADDED:
            return await _send_device_added(bot, notification)

        else:
            logger.warning(f"Unknown notification type: {notification.type}")
            return False

    except Exception as e:
        logger.error(f"Failed to send notification {notification.id}: {e}", exc_info=True)
        return False


async def _send_payment_success(bot: Bot, notification: Notification) -> bool:
    """Send payment success notification."""
    try:
        data = json.loads(notification.data) if notification.data else {}

        token = data.get("subscription_token", "")
        expires_at = data.get("expires_at", "")
        days = data.get("days", 0)
        amount = data.get("amount", 0)
        currency = data.get("currency", "RUB")
        devices = data.get("devices", 1)

        # Parse expiry date
        try:
            expires_dt = datetime.fromisoformat(expires_at)
            expires_str = expires_dt.strftime("%d.%m.%Y")
        except:
            expires_str = "неизвестно"

        # Import here to avoid circular imports
        import os
        from bot import keyboards

        DOMAIN = os.getenv("DOMAIN", "https://dudonya.online")
        subscription_url = f"{DOMAIN}/sub/{token}"

        # Beautiful message with emojis
        text = (
            "✅ <b>Оплата успешно получена!</b>\n\n"
            f"💎 Ваша подписка активирована на <b>{days} дней</b>\n"
            f"📅 Действует до: <b>{expires_str}</b>\n"
            f"📱 Устройств: <b>{devices}</b>\n\n"
            "🔗 <b>Ссылка для подключения:</b>\n"
            f"<code>{subscription_url}</code>\n\n"
            "👇 Нажмите кнопку ниже, чтобы скопировать ссылку и посмотреть инструкции по подключению."
        )

        await bot.send_message(
            chat_id=notification.telegram_id,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboards.get_subscription_active_keyboard()
        )

        logger.info(f"Sent payment success notification to {notification.telegram_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send payment success notification: {e}", exc_info=True)
        return False


async def _send_subscription_extended(bot: Bot, notification: Notification) -> bool:
    """Send subscription extended notification."""
    try:
        data = json.loads(notification.data) if notification.data else {}

        days = data.get("days", 0)
        expires_at = data.get("expires_at", "")

        try:
            expires_dt = datetime.fromisoformat(expires_at)
            expires_str = expires_dt.strftime("%d.%m.%Y")
        except:
            expires_str = "неизвестно"

        text = (
            "✅ <b>Подписка продлена!</b>\n\n"
            f"💎 Добавлено: <b>{days} дней</b>\n"
            f"📅 Действует до: <b>{expires_str}</b>\n\n"
            "Ваша VPN-подписка продолжает работать без перерывов!"
        )

        await bot.send_message(
            chat_id=notification.telegram_id,
            text=text,
            parse_mode="HTML"
        )

        logger.info(f"Sent subscription extended notification to {notification.telegram_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send subscription extended notification: {e}", exc_info=True)
        return False


async def _send_device_added(bot: Bot, notification: Notification) -> bool:
    """Send device added notification."""
    try:
        data = json.loads(notification.data) if notification.data else {}

        devices = data.get("devices", 0)

        text = (
            "✅ <b>Устройство добавлено!</b>\n\n"
            f"📱 Доступно устройств: <b>{devices}</b>\n\n"
            "Теперь вы можете подключить больше устройств к VPN!"
        )

        await bot.send_message(
            chat_id=notification.telegram_id,
            text=text,
            parse_mode="HTML"
        )

        logger.info(f"Sent device added notification to {notification.telegram_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send device added notification: {e}", exc_info=True)
        return False
