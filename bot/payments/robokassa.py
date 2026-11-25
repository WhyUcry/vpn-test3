"""Robokassa payment provider."""
import os
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from loguru import logger

from sqlalchemy.orm import Session
from backend.models import Payment, PaymentStatus, PaymentProvider, PendingPayment


ROBOKASSA_ENABLED = os.getenv("ROBOKASSA_ENABLED", "true").lower() == "true"
ROBOKASSA_LOGIN = os.getenv("ROBOKASSA_LOGIN", "")
ROBOKASSA_PASSWORD1 = os.getenv("ROBOKASSA_PASSWORD1", "")  # For payment link
ROBOKASSA_PASSWORD2 = os.getenv("ROBOKASSA_PASSWORD2", "")  # For Result URL
ROBOKASSA_IS_TEST = os.getenv("ROBOKASSA_IS_TEST", "false").lower() == "true"

ROBOKASSA_URL = "https://auth.robokassa.ru/Merchant/Index.aspx" if not ROBOKASSA_IS_TEST else "https://auth.robokassa.ru/Merchant/Index.aspx"


class RobokassaError(Exception):
    """Robokassa error."""
    pass


def calculate_signature(values: list[str], password: str) -> str:
    """
    Calculate MD5 signature for Robokassa.

    Args:
        values: List of values to hash
        password: Robokassa password

    Returns:
        MD5 hash (uppercase)
    """
    string = ":".join(str(v) for v in values)
    return hashlib.md5(string.encode('utf-8')).hexdigest().upper()


async def create_payment(
    db: Session,
    user_id: int,
    amount: float,
    currency: str,
    purpose: str,
    description: str,
    result_url: str,
    success_url: str,
    fail_url: str
) -> Dict[str, Any]:
    """
    Create Robokassa payment.

    Args:
        db: Database session
        user_id: User ID
        amount: Amount in rubles
        currency: Currency code (should be empty for RUB)
        purpose: Payment purpose (subscription/extra_device)
        description: Payment description
        result_url: Result URL for webhook
        success_url: Success redirect URL
        fail_url: Failure redirect URL

    Returns:
        Dict with payment data (order_id, url)

    Raises:
        RobokassaError: If creation fails
    """
    if not ROBOKASSA_ENABLED:
        raise RobokassaError("Robokassa is disabled")

    if not ROBOKASSA_LOGIN or not ROBOKASSA_PASSWORD1:
        raise RobokassaError("Robokassa not configured")

    # Generate invoice number
    invoice_id = int(datetime.utcnow().timestamp() * 1000) % 2147483647  # Max 32-bit int
    order_id = f"rk_{uuid.uuid4().hex[:16]}"

    logger.info(f"Creating Robokassa payment: {order_id} (invoice={invoice_id}), amount={amount} RUB")

    # Calculate signature
    # Signature = MD5(MerchantLogin:OutSum:InvId:OutSumCurrency:Password1)
    signature_values = [
        ROBOKASSA_LOGIN,
        f"{amount:.2f}",
        invoice_id,
        "",  # OutSumCurrency (empty for RUB)
        ROBOKASSA_PASSWORD1
    ]

    signature = calculate_signature(signature_values, ROBOKASSA_PASSWORD1)

    # Build payment URL
    params = {
        "MerchantLogin": ROBOKASSA_LOGIN,
        "OutSum": f"{amount:.2f}",
        "InvId": invoice_id,
        "Description": description,
        "SignatureValue": signature,
        "IsTest": "1" if ROBOKASSA_IS_TEST else "0",
        "Culture": "ru",
        # Custom params
        "Shp_OrderId": order_id,
        "Shp_UserId": user_id,
        "Shp_Purpose": purpose
    }

    payment_url = f"{ROBOKASSA_URL}?{urlencode(params)}"

    try:
        # Save pending payment
        pending = PendingPayment(
            order_id=order_id,
            user_id=user_id,
            amount=int(amount * 100),  # Convert to kopeks
            currency="RUB",
            purpose=purpose,
            provider=PaymentProvider.ROBOKASSA,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        db.add(pending)
        db.commit()

        return {
            "invoice_id": invoice_id,
            "order_id": order_id,
            "url": payment_url,
            "amount": amount,
            "currency": "RUB"
        }

    except Exception as e:
        logger.error(f"Failed to create Robokassa payment: {e}", exc_info=True)
        raise RobokassaError(f"Failed to create payment: {e}")


def process_result_webhook(db: Session, params: Dict[str, Any]) -> bool:
    """
    Process Robokassa Result URL (webhook).

    Args:
        db: Database session
        params: GET/POST parameters

    Returns:
        True if processed successfully
    """
    try:
        # Extract parameters
        out_sum = params.get("OutSum")
        inv_id = params.get("InvId")
        signature = params.get("SignatureValue", "").upper()

        # Custom parameters
        order_id = params.get("Shp_OrderId")

        if not all([out_sum, inv_id, signature, order_id]):
            logger.warning(f"Missing required parameters in Robokassa webhook")
            return False

        logger.info(f"Processing Robokassa payment: {order_id} (invoice={inv_id})")

        # Verify signature
        # Signature = MD5(OutSum:InvId:Password2:Shp_OrderId:Shp_Purpose:Shp_UserId)
        # Robokassa sorts custom params alphabetically
        user_id = params.get("Shp_UserId")
        purpose = params.get("Shp_Purpose")

        signature_values = [
            out_sum,
            inv_id,
            ROBOKASSA_PASSWORD2,
            order_id,
            purpose,
            user_id
        ]

        expected_signature = calculate_signature(signature_values, ROBOKASSA_PASSWORD2)

        if signature != expected_signature:
            logger.error(f"Invalid Robokassa signature: expected={expected_signature}, got={signature}")
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
            Payment.provider_payment_id == str(inv_id)
        ).first()

        if existing:
            logger.info(f"Payment {inv_id} already processed")
            return True

        # Create payment record
        payment = Payment(
            user_id=pending.user_id,
            amount=pending.amount,
            currency=pending.currency,
            provider=PaymentProvider.ROBOKASSA,
            purpose=pending.purpose,
            provider_payment_id=str(inv_id),
            status=PaymentStatus.PAID,
            paid_at=datetime.utcnow()
        )
        db.add(payment)

        # Remove pending payment
        db.delete(pending)
        db.commit()

        logger.info(f"Robokassa payment processed: {inv_id}")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to process Robokassa webhook: {e}", exc_info=True)
        return False
