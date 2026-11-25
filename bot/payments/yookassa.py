"""YooKassa payment provider."""
import os
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from yookassa import Configuration, Payment as YKPayment
from loguru import logger

from sqlalchemy.orm import Session
from backend.models import Payment, PaymentStatus, PaymentProvider, PendingPayment, PaymentPurpose


YOOKASSA_ENABLED = os.getenv("YOOKASSA_ENABLED", "true").lower() == "true"
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "")

# Allowed YooKassa IPs for webhook validation
YOOKASSA_IPS = [
    "185.71.76.0/27",
    "185.71.77.0/27",
    "77.75.153.0/25",
    "77.75.156.11",
    "77.75.156.35",
    "77.75.154.128/25",
    "2a02:5180::/32"
]


class YooKassaError(Exception):
    """YooKassa API error."""
    pass


def configure():
    """Configure YooKassa."""
    if YOOKASSA_ENABLED and YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY:
        Configuration.account_id = YOOKASSA_SHOP_ID
        Configuration.secret_key = YOOKASSA_SECRET_KEY
        logger.info("YooKassa configured")


async def create_payment(
    db: Session,
    user_id: int,
    amount: float,
    currency: str,
    purpose: str,
    description: str,
    return_url: str
) -> Dict[str, Any]:
    """
    Create YooKassa payment.

    Args:
        db: Database session
        user_id: User ID
        amount: Amount in rubles
        currency: Currency code (RUB)
        purpose: Payment purpose (subscription/extra_device)
        description: Payment description
        return_url: URL to redirect after payment

    Returns:
        Dict with payment data (payment_id, url)

    Raises:
        YooKassaError: If API request fails
    """
    if not YOOKASSA_ENABLED:
        raise YooKassaError("YooKassa is disabled")

    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        raise YooKassaError("YooKassa not configured")

    configure()

    # Generate idempotency key
    idempotency_key = str(uuid.uuid4())
    order_id = f"yk_{uuid.uuid4().hex[:16]}"

    logger.info(f"Creating YooKassa payment: {order_id}, amount={amount} {currency}")

    try:
        # Create payment
        payment = YKPayment.create({
            "amount": {
                "value": f"{amount:.2f}",
                "currency": currency
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "capture": True,
            "description": description,
            "metadata": {
                "order_id": order_id,
                "user_id": user_id,
                "purpose": purpose
            }
        }, idempotency_key)

        payment_id = payment.id
        confirmation_url = payment.confirmation.confirmation_url

        logger.info(f"YooKassa payment created: {payment_id}")

        # Save pending payment
        pending = PendingPayment(
            order_id=order_id,
            idempotency_key=idempotency_key,
            user_id=user_id,
            amount=int(amount * 100),  # Convert to kopeks
            currency=currency,
            purpose=purpose,
            provider=PaymentProvider.YOOKASSA,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        db.add(pending)
        db.commit()

        return {
            "payment_id": payment_id,
            "order_id": order_id,
            "url": confirmation_url,
            "amount": amount,
            "currency": currency
        }

    except Exception as e:
        logger.error(f"Failed to create YooKassa payment: {e}", exc_info=True)
        raise YooKassaError(f"Failed to create payment: {e}")


def process_webhook(db: Session, webhook_data: Dict[str, Any]) -> bool:
    """
    Process YooKassa webhook.

    Args:
        db: Database session
        webhook_data: Webhook payload

    Returns:
        True if processed successfully
    """
    try:
        event_type = webhook_data.get("event")

        if event_type != "payment.succeeded":
            logger.debug(f"Ignoring YooKassa event: {event_type}")
            return True

        payment_obj = webhook_data.get("object", {})
        payment_id = payment_obj.get("id")
        status = payment_obj.get("status")

        if status != "succeeded":
            logger.debug(f"Payment {payment_id} not succeeded: {status}")
            return True

        metadata = payment_obj.get("metadata", {})
        order_id = metadata.get("order_id")

        if not order_id:
            logger.warning(f"No order_id in payment metadata: {payment_id}")
            return False

        logger.info(f"Processing YooKassa payment: {order_id} ({payment_id})")

        # Find pending payment
        pending = db.query(PendingPayment).filter(
            PendingPayment.order_id == order_id
        ).first()

        if not pending:
            logger.warning(f"Pending payment not found: {order_id}")
            return False

        # Check if already processed (idempotency)
        existing = db.query(Payment).filter(
            Payment.provider_payment_id == payment_id
        ).first()

        if existing:
            logger.info(f"Payment {payment_id} already processed")
            return True

        # Create payment record
        payment = Payment(
            user_id=pending.user_id,
            amount=pending.amount,
            currency=pending.currency,
            provider=PaymentProvider.YOOKASSA,
            purpose=pending.purpose,
            provider_payment_id=payment_id,
            status=PaymentStatus.PAID,
            paid_at=datetime.utcnow()
        )
        db.add(payment)

        # Remove pending payment
        db.delete(pending)
        db.commit()

        logger.info(f"YooKassa payment processed: {payment_id}")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to process YooKassa webhook: {e}", exc_info=True)
        return False


def validate_webhook_ip(ip: str) -> bool:
    """
    Validate that webhook comes from YooKassa IP.

    Args:
        ip: Request IP address

    Returns:
        True if IP is valid
    """
    # TODO: Implement CIDR matching for IP validation
    # For now, accept all (should be fixed in production)
    logger.warning(f"YooKassa webhook IP validation not implemented, accepting IP: {ip}")
    return True
