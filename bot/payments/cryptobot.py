"""CryptoBot (Crypto Pay API) payment provider."""
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import aiohttp
from loguru import logger

from sqlalchemy.orm import Session
from backend.models import Payment, PaymentStatus, PaymentProvider, PendingPayment


CRYPTOBOT_ENABLED = os.getenv("CRYPTOBOT_ENABLED", "true").lower() == "true"
CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN", "")
CRYPTOBOT_ASSET = os.getenv("CRYPTOBOT_ASSET", "USDT")
CRYPTOBOT_API_URL = "https://pay.crypt.bot/api"


class CryptoBotError(Exception):
    """CryptoBot API error."""
    pass


async def create_invoice(
    db: Session,
    user_id: int,
    amount: float,
    currency: str,
    purpose: str,
    description: str
) -> Dict[str, Any]:
    """
    Create CryptoBot invoice.

    Args:
        db: Database session
        user_id: User ID
        amount: Amount in USDT (or other crypto)
        currency: Currency code (USDT, BTC, etc)
        purpose: Payment purpose (subscription/extra_device)
        description: Payment description

    Returns:
        Dict with invoice data (invoice_id, url)

    Raises:
        CryptoBotError: If API request fails
    """
    if not CRYPTOBOT_ENABLED:
        raise CryptoBotError("CryptoBot is disabled")

    if not CRYPTOBOT_TOKEN:
        raise CryptoBotError("CryptoBot token not configured")

    # Generate unique invoice ID
    invoice_id = f"cb_{uuid.uuid4().hex[:16]}"

    logger.info(f"Creating CryptoBot invoice: {invoice_id}, amount={amount} {currency}")

    # API request
    headers = {
        "Crypto-Pay-API-Token": CRYPTOBOT_TOKEN
    }

    payload = {
        "asset": CRYPTOBOT_ASSET,
        "amount": str(amount),
        "description": description,
        "paid_btn_name": "callback",
        "paid_btn_url": f"https://t.me/YOUR_BOT_USERNAME",  # TODO: Replace with actual bot username
        "payload": invoice_id
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{CRYPTOBOT_API_URL}/createInvoice",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                data = await response.json()

                if not data.get("ok"):
                    error = data.get("error", {})
                    raise CryptoBotError(f"CryptoBot API error: {error.get('name', 'Unknown')}")

                result = data.get("result", {})
                invoice_url = result.get("bot_invoice_url") or result.get("mini_app_invoice_url")
                crypto_invoice_id = result.get("invoice_id")

                logger.info(f"CryptoBot invoice created: {crypto_invoice_id}")

                # Save pending payment
                pending = PendingPayment(
                    order_id=invoice_id,
                    user_id=user_id,
                    amount=int(amount * 100),  # Convert to cents
                    currency=currency,
                    purpose=purpose,
                    provider=PaymentProvider.CRYPTOBOT,
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(minutes=15)
                )
                db.add(pending)
                db.commit()

                return {
                    "invoice_id": invoice_id,
                    "crypto_invoice_id": crypto_invoice_id,
                    "url": invoice_url,
                    "amount": amount,
                    "currency": currency
                }

    except aiohttp.ClientError as e:
        logger.error(f"CryptoBot API request failed: {e}")
        raise CryptoBotError(f"Network error: {e}")
    except Exception as e:
        logger.error(f"Failed to create CryptoBot invoice: {e}", exc_info=True)
        raise CryptoBotError(f"Failed to create invoice: {e}")


async def check_invoice_status(invoice_id: str) -> Optional[str]:
    """
    Check CryptoBot invoice status.

    Args:
        invoice_id: Invoice ID

    Returns:
        Status: "paid", "pending", "expired", or None if not found
    """
    if not CRYPTOBOT_ENABLED or not CRYPTOBOT_TOKEN:
        return None

    headers = {
        "Crypto-Pay-API-Token": CRYPTOBOT_TOKEN
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{CRYPTOBOT_API_URL}/getInvoices",
                headers=headers,
                params={"invoice_ids": invoice_id},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                data = await response.json()

                if not data.get("ok"):
                    return None

                items = data.get("result", {}).get("items", [])
                if not items:
                    return None

                invoice = items[0]
                status = invoice.get("status")  # "active", "paid", "expired"

                return "paid" if status == "paid" else "pending" if status == "active" else "expired"

    except Exception as e:
        logger.error(f"Failed to check CryptoBot invoice status: {e}")
        return None


def process_webhook(db: Session, webhook_data: Dict[str, Any]) -> bool:
    """
    Process CryptoBot webhook.

    Args:
        db: Database session
        webhook_data: Webhook payload

    Returns:
        True if processed successfully
    """
    try:
        update_type = webhook_data.get("update_type")

        if update_type != "invoice_paid":
            logger.debug(f"Ignoring CryptoBot webhook type: {update_type}")
            return True

        payload_data = webhook_data.get("payload", {})
        invoice_id = payload_data.get("payload")  # Our custom payload
        status = payload_data.get("status")

        if status != "paid":
            logger.debug(f"Invoice {invoice_id} not paid yet: {status}")
            return True

        logger.info(f"Processing CryptoBot payment: {invoice_id}")

        # Find pending payment
        pending = db.query(PendingPayment).filter(
            PendingPayment.order_id == invoice_id
        ).first()

        if not pending:
            logger.warning(f"Pending payment not found: {invoice_id}")
            return False

        # Check if already processed (idempotency)
        existing = db.query(Payment).filter(
            Payment.provider_payment_id == invoice_id
        ).first()

        if existing:
            logger.info(f"Payment {invoice_id} already processed")
            return True

        # Create payment record
        payment = Payment(
            user_id=pending.user_id,
            amount=pending.amount,
            currency=pending.currency,
            provider=PaymentProvider.CRYPTOBOT,
            purpose=pending.purpose,
            provider_payment_id=invoice_id,
            status=PaymentStatus.PAID,
            paid_at=datetime.utcnow()
        )
        db.add(payment)

        # Remove pending payment
        db.delete(pending)
        db.commit()

        logger.info(f"CryptoBot payment processed: {invoice_id}")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to process CryptoBot webhook: {e}", exc_info=True)
        return False
