"""Freekassa payment provider."""
import os
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from loguru import logger

from sqlalchemy.orm import Session
from backend.models import Payment, PaymentStatus, PaymentProvider, PendingPayment


FREEKASSA_ENABLED = os.getenv("FREEKASSA_ENABLED", "true").lower() == "true"
FREEKASSA_SHOP_ID = os.getenv("FREEKASSA_SHOP_ID", "")
FREEKASSA_SECRET_WORD_1 = os.getenv("FREEKASSA_SECRET_WORD_1", "")  # First secret word
FREEKASSA_SECRET_WORD_2 = os.getenv("FREEKASSA_SECRET_WORD_2", "")  # Second secret word
FREEKASSA_API_KEY = os.getenv("FREEKASSA_API_KEY", "")

FREEKASSA_URL = "https://pay.freekassa.ru/"


class FreekassaError(Exception):
    """Freekassa error."""
    pass


def calculate_signature(merchant_id: str, amount: str, secret: str, order_id: str) -> str:
    """
    Calculate signature for Freekassa.
    Format: MD5(shop_id:amount:secret:order_id)

    Args:
        merchant_id: Shop ID
        amount: Amount
        secret: Secret word
        order_id: Order ID

    Returns:
        MD5 hash
    """
    string = f"{merchant_id}:{amount}:{secret}:{order_id}"
    return hashlib.md5(string.encode('utf-8')).hexdigest()


async def create_payment(
    db: Session,
    user_id: int,
    amount: float,
    currency: str,
    purpose: str,
    description: str,
    success_url: str,
    fail_url: str
) -> Dict[str, Any]:
    """
    Create Freekassa payment.

    Args:
        db: Database session
        user_id: User ID
        amount: Amount in rubles
        currency: Currency code (RUB)
        purpose: Payment purpose (subscription/extra_device)
        description: Payment description
        success_url: Success redirect URL
        fail_url: Failure redirect URL

    Returns:
        Dict with payment data (order_id, url)

    Raises:
        FreekassaError: If creation fails
    """
    if not FREEKASSA_ENABLED:
        raise FreekassaError("Freekassa is disabled")

    if not FREEKASSA_SHOP_ID or not FREEKASSA_SECRET_WORD_1:
        raise FreekassaError("Freekassa not configured")

    # Generate order ID
    order_id = f"fk_{uuid.uuid4().hex[:16]}"

    logger.info(f"Creating Freekassa payment: {order_id}, amount={amount} RUB")

    # Calculate signature
    signature = calculate_signature(
        FREEKASSA_SHOP_ID,
        f"{amount:.2f}",
        FREEKASSA_SECRET_WORD_1,
        order_id
    )

    # Build payment URL
    params = {
        "m": FREEKASSA_SHOP_ID,
        "oa": f"{amount:.2f}",
        "o": order_id,
        "s": signature,
        "currency": "RUB",
        "i": description,
        "us_user_id": user_id,
        "us_purpose": purpose,
        "success_url": success_url,
        "failure_url": fail_url
    }

    payment_url = f"{FREEKASSA_URL}?{urlencode(params)}"

    try:
        # Save pending payment
        pending = PendingPayment(
            order_id=order_id,
            user_id=user_id,
            amount=int(amount * 100),  # Convert to kopeks
            currency="RUB",
            purpose=purpose,
            provider=PaymentProvider.FREEKASSA,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        db.add(pending)
        db.commit()

        return {
            "order_id": order_id,
            "url": payment_url,
            "amount": amount,
            "currency": "RUB"
        }

    except Exception as e:
        logger.error(f"Failed to create Freekassa payment: {e}", exc_info=True)
        raise FreekassaError(f"Failed to create payment: {e}")


def process_webhook(db: Session, params: Dict[str, Any]) -> bool:
    """
    Process Freekassa webhook (notification).

    Freekassa sends POST with:
    - MERCHANT_ID
    - AMOUNT
    - intid (internal payment ID)
    - MERCHANT_ORDER_ID
    - SIGN (signature)
    - us_* (custom parameters)

    Args:
        db: Database session
        params: POST parameters

    Returns:
        True if processed successfully
    """
    try:
        # Extract parameters
        merchant_id = params.get("MERCHANT_ID")
        amount = params.get("AMOUNT")
        intid = params.get("intid")
        order_id = params.get("MERCHANT_ORDER_ID")
        signature = params.get("SIGN")

        if not all([merchant_id, amount, intid, order_id, signature]):
            logger.warning(f"Missing required parameters in Freekassa webhook")
            return False

        logger.info(f"Processing Freekassa payment: {order_id} (intid={intid})")

        # Verify signature
        # Format: MD5(shop_id:amount:secret_word_2:order_id)
        expected_signature = calculate_signature(
            merchant_id,
            amount,
            FREEKASSA_SECRET_WORD_2,
            order_id
        )

        if signature != expected_signature:
            logger.error(f"Invalid Freekassa signature: expected={expected_signature}, got={signature}")
            return False

        # Check merchant ID
        if merchant_id != FREEKASSA_SHOP_ID:
            logger.error(f"Invalid merchant ID: {merchant_id}")
            return False

        # Find pending payment
        pending = db.query(PendingPayment).filter(
            PendingPayment.order_id == order_id
        ).first()

        if not pending:
            logger.warning(f"Pending payment not found: {order_id}")
            return False

        # Check if already processed (idempotency)
        existing = db.query(Payment).filter(
            Payment.provider_payment_id == str(intid)
        ).first()

        if existing:
            logger.info(f"Payment {intid} already processed")
            return True

        # Create payment record
        payment = Payment(
            user_id=pending.user_id,
            amount=pending.amount,
            currency=pending.currency,
            provider=PaymentProvider.FREEKASSA,
            purpose=pending.purpose,
            provider_payment_id=str(intid),
            status=PaymentStatus.PAID,
            paid_at=datetime.utcnow()
        )
        db.add(payment)
        db.flush()  # Get payment ID without committing

        # Remove pending payment
        db.delete(pending)
        db.commit()

        # Activate subscription
        from backend.payment_processor import process_successful_payment
        success = process_successful_payment(db, payment)

        if not success:
            logger.error(f"Failed to activate subscription for payment {intid}")
            # Payment is still recorded, manual intervention may be needed

        logger.info(f"Freekassa payment processed: {intid}")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to process Freekassa webhook: {e}", exc_info=True)
        return False
