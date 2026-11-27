"""
Test webhooks and payment flow.

This test verifies that:
1. Webhook is received by backend
2. Payment is processed successfully
3. Subscription is activated
4. Device slots are created
5. Notification is created for bot
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import hashlib
from datetime import datetime, timedelta

from backend.db import SessionLocal, engine
from backend.models import Base, User, Subscription, Payment, Notification, PendingPayment
from backend.models import PaymentStatus, PaymentProvider, PaymentPurpose, SubscriptionStatus
from bot.payments import freekassa, cryptobot


def setup_test_db():
    """Setup test database."""
    Base.metadata.create_all(engine)
    db = SessionLocal()

    # Create test user
    user = User(telegram_id=123456789, username="test_user")
    db.add(user)
    db.commit()
    db.refresh(user)

    return db, user


def test_freekassa_webhook():
    """Test Freekassa webhook processing."""
    print("\n🧪 Testing Freekassa Webhook...")

    db, user = setup_test_db()

    try:
        # Step 1: Create pending payment
        order_id = "fk_test123456"
        pending = PendingPayment(
            order_id=order_id,
            user_id=user.id,
            amount=19900,  # 199 RUB in kopeks
            currency="RUB",
            purpose=PaymentPurpose.SUBSCRIPTION,
            provider=PaymentProvider.FREEKASSA,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        db.add(pending)
        db.commit()
        print("✅ Step 1: Pending payment created")

        # Step 2: Simulate webhook from Freekassa
        import os
        shop_id = os.getenv("FREEKASSA_SHOP_ID", "12345")
        secret_word_2 = os.getenv("FREEKASSA_SECRET_WORD_2", "secret123")

        amount = "199.00"
        intid = "999888777"

        # Calculate signature
        signature = hashlib.md5(
            f"{shop_id}:{amount}:{secret_word_2}:{order_id}".encode()
        ).hexdigest()

        webhook_data = {
            "MERCHANT_ID": shop_id,
            "AMOUNT": amount,
            "intid": intid,
            "MERCHANT_ORDER_ID": order_id,
            "SIGN": signature
        }

        print("✅ Step 2: Webhook data prepared")

        # Step 3: Process webhook
        success = freekassa.process_webhook(db, webhook_data)

        if not success:
            print("❌ Webhook processing failed!")
            return False

        print("✅ Step 3: Webhook processed successfully")

        # Step 4: Check that payment was created
        payment = db.query(Payment).filter(
            Payment.provider_payment_id == str(intid)
        ).first()

        if not payment:
            print("❌ Payment record not created!")
            return False

        if payment.status != PaymentStatus.PAID:
            print(f"❌ Payment status is {payment.status}, expected PAID")
            return False

        print(f"✅ Step 4: Payment created (ID: {payment.id}, Status: {payment.status.value})")

        # Step 5: Check that subscription was created
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id
        ).first()

        if not subscription:
            print("❌ Subscription not created!")
            return False

        if subscription.status != SubscriptionStatus.ACTIVE:
            print(f"❌ Subscription status is {subscription.status}, expected ACTIVE")
            return False

        days_until_expiry = (subscription.expires_at - datetime.utcnow()).days
        print(f"✅ Step 5: Subscription created (Token: {subscription.token[:8]}..., Expires in: {days_until_expiry} days)")

        # Step 6: Check that device slots were created
        slots_count = len(subscription.device_slots)

        if slots_count == 0:
            print("❌ Device slots not created!")
            return False

        print(f"✅ Step 6: Device slots created (Count: {slots_count})")

        for slot in subscription.device_slots:
            print(f"   - Slot {slot.slot_index}: UUID={slot.uuid[:8]}..., Short ID={slot.short_id}")

        # Step 7: Check that notification was created
        notification = db.query(Notification).filter(
            Notification.user_id == user.id,
            Notification.telegram_id == user.telegram_id
        ).first()

        if not notification:
            print("❌ Notification not created!")
            return False

        if notification.sent != 0:
            print(f"⚠️  Warning: Notification already sent (sent={notification.sent})")

        print(f"✅ Step 7: Notification created (ID: {notification.id}, Type: {notification.type.value}, Sent: {notification.sent})")

        # Parse notification data
        if notification.data:
            data = json.loads(notification.data)
            print(f"   - Subscription token: {data.get('subscription_token', 'N/A')[:8]}...")
            print(f"   - Days: {data.get('days', 'N/A')}")
            print(f"   - Amount: {data.get('amount', 'N/A')} {data.get('currency', 'N/A')}")

        print("\n✅ ✅ ✅ ALL TESTS PASSED! ✅ ✅ ✅")
        print("\nPayment flow working correctly:")
        print("  Webhook → Payment → Subscription → Device Slots → Notification")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        db.query(Notification).delete()
        db.query(Payment).delete()
        db.query(Subscription).delete()
        db.query(PendingPayment).delete()
        db.query(User).delete()
        db.commit()
        db.close()


def test_cryptobot_webhook():
    """Test CryptoBot webhook processing."""
    print("\n🧪 Testing CryptoBot Webhook...")

    db, user = setup_test_db()

    try:
        # Step 1: Create pending payment
        order_id = "cb_test123456"
        pending = PendingPayment(
            order_id=order_id,
            user_id=user.id,
            amount=219,  # 2.19 USDT in cents
            currency="USDT",
            purpose=PaymentPurpose.SUBSCRIPTION,
            provider=PaymentProvider.CRYPTOBOT,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        db.add(pending)
        db.commit()
        print("✅ Step 1: Pending payment created")

        # Step 2: Simulate webhook from CryptoBot
        webhook_data = {
            "update_type": "invoice_paid",
            "payload": {
                "payload": order_id,
                "status": "paid",
                "amount": "2.19",
                "asset": "USDT"
            }
        }

        print("✅ Step 2: Webhook data prepared")

        # Step 3: Process webhook
        success = cryptobot.process_webhook(db, webhook_data)

        if not success:
            print("❌ Webhook processing failed!")
            return False

        print("✅ Step 3: Webhook processed successfully")

        # Verify results (same as Freekassa test)
        payment = db.query(Payment).filter(
            Payment.provider_payment_id == order_id
        ).first()

        if not payment or payment.status != PaymentStatus.PAID:
            print("❌ Payment not created or not paid!")
            return False

        print(f"✅ Step 4: Payment created (ID: {payment.id})")

        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id
        ).first()

        if not subscription or subscription.status != SubscriptionStatus.ACTIVE:
            print("❌ Subscription not created or not active!")
            return False

        print(f"✅ Step 5: Subscription created (Token: {subscription.token[:8]}...)")

        if len(subscription.device_slots) == 0:
            print("❌ Device slots not created!")
            return False

        print(f"✅ Step 6: Device slots created (Count: {len(subscription.device_slots)})")

        notification = db.query(Notification).filter(
            Notification.user_id == user.id
        ).first()

        if not notification:
            print("❌ Notification not created!")
            return False

        print(f"✅ Step 7: Notification created")

        print("\n✅ ✅ ✅ CRYPTOBOT TEST PASSED! ✅ ✅ ✅")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        db.query(Notification).delete()
        db.query(Payment).delete()
        db.query(Subscription).delete()
        db.query(PendingPayment).delete()
        db.query(User).delete()
        db.commit()
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTING PAYMENT WEBHOOKS")
    print("=" * 60)

    # Test both payment providers
    freekassa_ok = test_freekassa_webhook()
    cryptobot_ok = test_cryptobot_webhook()

    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    print(f"Freekassa: {'✅ PASS' if freekassa_ok else '❌ FAIL'}")
    print(f"CryptoBot: {'✅ PASS' if cryptobot_ok else '❌ FAIL'}")

    if freekassa_ok and cryptobot_ok:
        print("\n🎉 ALL TESTS PASSED! Payment system is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED! Check the output above.")
        sys.exit(1)
