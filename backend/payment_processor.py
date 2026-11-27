"""Payment processing and subscription activation logic."""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger
from sqlalchemy.orm import Session

from backend.models import (
    Payment, Subscription, SubscriptionStatus,
    PaymentPurpose, User
)
from backend.slot_generator import create_device_slots, add_device_slot


def process_successful_payment(db: Session, payment: Payment) -> bool:
    """
    Process a successful payment and activate/extend subscription.

    Args:
        db: Database session
        payment: Payment object (must be PAID status)

    Returns:
        True if processed successfully, False otherwise
    """
    try:
        logger.info(f"Processing payment {payment.id} for user {payment.user_id}")

        # Get user
        user = db.query(User).filter(User.id == payment.user_id).first()
        if not user:
            logger.error(f"User not found: {payment.user_id}")
            return False

        if payment.purpose == PaymentPurpose.SUBSCRIPTION:
            # Activate or extend subscription
            return _activate_subscription(db, payment, user)

        elif payment.purpose == PaymentPurpose.EXTRA_DEVICE:
            # Add extra device slot
            return _add_extra_device(db, payment, user)

        else:
            logger.error(f"Unknown payment purpose: {payment.purpose}")
            return False

    except Exception as e:
        logger.error(f"Failed to process payment {payment.id}: {e}", exc_info=True)
        return False


def _activate_subscription(db: Session, payment: Payment, user: User) -> bool:
    """
    Activate or extend user's subscription based on payment.

    Args:
        db: Database session
        payment: Payment object
        user: User object

    Returns:
        True if successful
    """
    # Determine subscription duration based on amount
    # This is a simplified mapping - adjust to your actual pricing
    amount_rub = payment.amount / 100  # Convert from kopeks to rubles

    # Map amount to days (adjust these values to match your pricing)
    if amount_rub >= 1400:  # 12 months
        days = 365
        base_devices = 1
    elif amount_rub >= 450:  # 3 months
        days = 90
        base_devices = 1
    elif amount_rub >= 150:  # 1 month
        days = 30
        base_devices = 1
    else:
        logger.error(f"Invalid subscription amount: {amount_rub} RUB")
        return False

    # Check if user has an active subscription
    now = datetime.utcnow()
    active_sub = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == SubscriptionStatus.ACTIVE,
        Subscription.expires_at > now
    ).first()

    if active_sub:
        # Extend existing subscription
        logger.info(f"Extending subscription {active_sub.id} by {days} days")
        active_sub.expires_at = active_sub.expires_at + timedelta(days=days)
        db.commit()

        logger.info(f"Subscription extended until {active_sub.expires_at}")

        # Notify user
        notify_user_payment_success(db, user, active_sub, payment)

        return True

    else:
        # Create new subscription
        logger.info(f"Creating new subscription for user {user.id}")

        token = str(uuid.uuid4())
        expires_at = now + timedelta(days=days)

        subscription = Subscription(
            user_id=user.id,
            token=token,
            status=SubscriptionStatus.ACTIVE,
            base_devices=base_devices,
            extra_devices=0,
            expires_at=expires_at
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        # Create device slots
        create_device_slots(db, subscription.id, base_devices)

        logger.info(
            f"Subscription created: id={subscription.id}, "
            f"token={token[:8]}..., expires={expires_at}"
        )

        # Notify user
        notify_user_payment_success(db, user, subscription, payment)

        return True


def _add_extra_device(db: Session, payment: Payment, user: User) -> bool:
    """
    Add an extra device slot to user's active subscription.

    Args:
        db: Database session
        payment: Payment object
        user: User object

    Returns:
        True if successful
    """
    # Find active subscription
    now = datetime.utcnow()
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == SubscriptionStatus.ACTIVE,
        Subscription.expires_at > now
    ).first()

    if not subscription:
        logger.error(f"No active subscription found for user {user.id}")
        return False

    # Add extra device
    subscription.extra_devices += 1

    # Create new device slot
    slot_index = subscription.base_devices + subscription.extra_devices
    add_device_slot(db, subscription.id, slot_index)

    db.commit()

    logger.info(
        f"Added extra device to subscription {subscription.id}. "
        f"Total devices: {subscription.base_devices + subscription.extra_devices}"
    )
    return True


def notify_user_payment_success(
    db: Session,
    user: User,
    subscription: Subscription,
    payment: Payment
):
    """
    Create notification for user about successful payment.

    Args:
        db: Database session
        user: User object
        subscription: Subscription object
        payment: Payment object
    """
    from backend.models import Notification, NotificationType
    import json

    try:
        notification_data = {
            "subscription_token": subscription.token,
            "expires_at": subscription.expires_at.isoformat(),
            "days": (subscription.expires_at - datetime.utcnow()).days,
            "amount": payment.amount / 100,
            "currency": payment.currency,
            "provider": payment.provider.value,
            "devices": subscription.base_devices + subscription.extra_devices
        }

        notification = Notification(
            user_id=user.id,
            telegram_id=user.telegram_id,
            type=NotificationType.PAYMENT_SUCCESS,
            subscription_id=subscription.id,
            payment_id=payment.id,
            data=json.dumps(notification_data),
            sent=0
        )
        db.add(notification)
        db.commit()

        logger.info(
            f"Created notification for user {user.telegram_id}: "
            f"subscription {subscription.token[:8]}..."
        )
    except Exception as e:
        logger.error(f"Failed to create notification: {e}", exc_info=True)
