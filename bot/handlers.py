"""Bot handlers for Dudonya VPN."""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import uuid

from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db import SessionLocal
from backend.models import User, Subscription, SubscriptionStatus, PaymentPurpose
from backend.slot_generator import create_device_slots, add_device_slot
from bot import texts, keyboards
from bot.payments import cryptobot, freekassa


# Configuration
DOMAIN = os.getenv("DOMAIN", "https://vpn.example.com")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BASE_DEVICES = int(os.getenv("BASE_DEVICES", "1"))
MAX_DEVICES = int(os.getenv("MAX_DEVICES", "5"))
PRICE_1M = int(os.getenv("PRICE_1M", "199"))
PRICE_3M = int(os.getenv("PRICE_3M", "499"))
PRICE_12M = int(os.getenv("PRICE_12M", "1499"))
PRICE_PER_DEVICE = int(os.getenv("PRICE_PER_DEVICE", "99"))
CURRENCY = os.getenv("CURRENCY", "RUB")

CRYPTOBOT_ENABLED = os.getenv("CRYPTOBOT_ENABLED", "true").lower() == "true"
FREEKASSA_ENABLED = os.getenv("FREEKASSA_ENABLED", "true").lower() == "true"

router = Router()


# FSM States
class BroadcastStates(StatesGroup):
    """Broadcast states."""
    waiting_for_message = State()


# Helpers
def get_or_create_user(db: Session, telegram_id: int, username: Optional[str] = None) -> User:
    """Get or create user."""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created new user: {telegram_id}")
    return user


def get_active_subscription(db: Session, user_id: int) -> Optional[Subscription]:
    """Get user's active subscription."""
    now = datetime.utcnow()
    return db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status == SubscriptionStatus.ACTIVE,
        Subscription.expires_at > now
    ).first()


def calculate_discount(original: int, discounted: int) -> int:
    """Calculate discount percentage."""
    return int((1 - discounted / (original * 1)) * 100) if original else 0


# Command handlers
@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command."""
    db = SessionLocal()
    try:
        user = get_or_create_user(db, message.from_user.id, message.from_user.username)
        subscription = get_active_subscription(db, user.id)

        await message.answer(
            texts.WELCOME_TEXT,
            reply_markup=keyboards.get_main_menu_keyboard(has_subscription=bool(subscription))
        )
    finally:
        db.close()


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Handle main menu callback."""
    db = SessionLocal()
    try:
        user = get_or_create_user(db, callback.from_user.id, callback.from_user.username)
        subscription = get_active_subscription(db, user.id)

        await callback.message.edit_text(
            texts.WELCOME_TEXT,
            reply_markup=keyboards.get_main_menu_keyboard(has_subscription=bool(subscription))
        )
        await callback.answer()
    finally:
        db.close()


# Subscription info
@router.callback_query(F.data == "my_subscription")
async def callback_my_subscription(callback: CallbackQuery):
    """Show user's subscription info."""
    db = SessionLocal()
    try:
        user = get_or_create_user(db, callback.from_user.id)
        subscription = get_active_subscription(db, user.id)

        if not subscription:
            await callback.message.edit_text(
                texts.NO_SUBSCRIPTION_TEXT,
                reply_markup=keyboards.get_main_menu_keyboard(has_subscription=False)
            )
            await callback.answer()
            return

        # Format subscription info
        url = f"{DOMAIN}/sub/{subscription.token}"
        devices_current = subscription.base_devices + subscription.extra_devices

        text = texts.SUBSCRIPTION_INFO_TEMPLATE.format(
            token=subscription.token[:8] + "...",
            status=texts.SUBSCRIPTION_ACTIVE,
            expires_at=subscription.expires_at.strftime("%d.%m.%Y %H:%M"),
            devices_current=devices_current,
            devices_max=MAX_DEVICES,
            url=url
        )

        await callback.message.edit_text(
            text,
            reply_markup=keyboards.get_copy_subscription_keyboard(url)
        )
        await callback.answer()
    finally:
        db.close()


# Pricing
@router.callback_query(F.data == "pricing")
async def callback_pricing(callback: CallbackQuery):
    """Show pricing."""
    discount_3m = calculate_discount(PRICE_1M * 3, PRICE_3M)
    discount_12m = calculate_discount(PRICE_1M * 12, PRICE_12M)

    text = texts.PRICING_TEXT.format(
        price_1m=PRICE_1M,
        price_3m=PRICE_3M,
        price_12m=PRICE_12M,
        currency=CURRENCY,
        discount_3m=discount_3m,
        discount_12m=discount_12m,
        base_devices=BASE_DEVICES,
        price_per_device=PRICE_PER_DEVICE,
        max_devices=MAX_DEVICES
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboards.get_pricing_keyboard()
    )
    await callback.answer()


# Buy subscription
@router.callback_query(F.data.startswith("buy:"))
async def callback_buy(callback: CallbackQuery):
    """Handle buy callback."""
    plan = callback.data.split(":")[1]

    # Determine price and description
    if plan == "1m":
        amount = PRICE_1M
        description = "Подписка Дудоня VPN — 1 месяц"
        plan_text = "1 месяц"
    elif plan == "3m":
        amount = PRICE_3M
        description = "Подписка Дудоня VPN — 3 месяца"
        plan_text = "3 месяца"
    elif plan == "12m":
        amount = PRICE_12M
        description = "Подписка Дудоня VPN — 12 месяцев"
        plan_text = "12 месяцев"
    elif plan == "extra_device":
        amount = PRICE_PER_DEVICE
        description = "Дополнительное устройство"
        plan_text = "Дополнительное устройство"
    else:
        await callback.answer("Неизвестный тариф", show_alert=True)
        return

    text = texts.PAYMENT_METHOD_TEXT.format(
        plan=plan_text,
        amount=amount,
        currency=CURRENCY
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboards.get_payment_method_keyboard(
            plan, CRYPTOBOT_ENABLED, FREEKASSA_ENABLED
        )
    )
    await callback.answer()


# Extra device
@router.callback_query(F.data == "extra_device")
async def callback_extra_device(callback: CallbackQuery):
    """Show extra device info."""
    db = SessionLocal()
    try:
        user = get_or_create_user(db, callback.from_user.id)
        subscription = get_active_subscription(db, user.id)

        if not subscription:
            await callback.message.edit_text(
                texts.EXTRA_DEVICE_NO_SUBSCRIPTION,
                reply_markup=keyboards.get_main_menu_keyboard(has_subscription=False)
            )
            await callback.answer()
            return

        current_devices = subscription.base_devices + subscription.extra_devices

        if current_devices >= MAX_DEVICES:
            await callback.message.edit_text(
                texts.EXTRA_DEVICE_LIMIT_REACHED.format(max=MAX_DEVICES),
                reply_markup=keyboards.get_back_to_main_keyboard()
            )
            await callback.answer()
            return

        text = texts.EXTRA_DEVICE_INFO.format(
            current=current_devices,
            max=MAX_DEVICES,
            price=PRICE_PER_DEVICE,
            currency=CURRENCY
        )

        await callback.message.edit_text(
            text,
            reply_markup=keyboards.get_extra_device_keyboard()
        )
        await callback.answer()
    finally:
        db.close()


# Payment processing
@router.callback_query(F.data.startswith("pay:"))
async def callback_pay(callback: CallbackQuery):
    """Process payment."""
    parts = callback.data.split(":")
    provider_name = parts[1]
    plan = parts[2]

    db = SessionLocal()
    try:
        user = get_or_create_user(db, callback.from_user.id)

        # Determine amount and purpose
        if plan == "1m":
            amount = PRICE_1M
            days = 30
            purpose = PaymentPurpose.SUBSCRIPTION
        elif plan == "3m":
            amount = PRICE_3M
            days = 90
            purpose = PaymentPurpose.SUBSCRIPTION
        elif plan == "12m":
            amount = PRICE_12M
            days = 365
            purpose = PaymentPurpose.SUBSCRIPTION
        elif plan == "extra_device":
            amount = PRICE_PER_DEVICE
            days = 0
            purpose = PaymentPurpose.EXTRA_DEVICE
        else:
            await callback.answer("Ошибка: неизвестный тариф", show_alert=True)
            return

        # Create payment based on provider
        try:
            if provider_name == "cryptobot":
                # Convert RUB to USDT (approximate rate 1 RUB = 0.011 USDT)
                amount_crypto = round(amount * 0.011, 2)
                result = await cryptobot.create_invoice(
                    db, user.id, amount_crypto, "USDT",
                    purpose.value, f"Дудоня VPN — {plan}"
                )

            elif provider_name == "freekassa":
                result = await freekassa.create_payment(
                    db, user.id, amount, CURRENCY,
                    purpose.value, f"Дудоня VPN — {plan}",
                    success_url=f"https://t.me/YOUR_BOT_USERNAME",
                    fail_url=f"https://t.me/YOUR_BOT_USERNAME"
                )

            else:
                await callback.answer(texts.ERROR_PAYMENT_PROVIDER_DISABLED, show_alert=True)
                return

            # Send payment link
            text = texts.PAYMENT_CREATED.format(
                amount=result["amount"],
                currency=result["currency"],
                provider=provider_name.capitalize(),
                url=result["url"]
            )

            await callback.message.edit_text(text)
            await callback.answer()

        except Exception as e:
            logger.error(f"Payment creation failed: {e}", exc_info=True)
            await callback.answer(
                texts.ERROR_GENERIC,
                show_alert=True
            )

    finally:
        db.close()


# Instructions
@router.callback_query(F.data == "instructions_menu")
async def callback_instructions_menu(callback: CallbackQuery):
    """Show instructions menu."""
    await callback.message.edit_text(
        texts.INSTRUCTIONS_MENU,
        reply_markup=keyboards.get_instructions_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("instructions:"))
async def callback_instructions(callback: CallbackQuery):
    """Show specific instructions."""
    app = callback.data.split(":")[1]

    text_map = {
        "happ": texts.INSTRUCTIONS_HAPP,
        "v2rayng": texts.INSTRUCTIONS_V2RAYNG,
        "streisand": texts.INSTRUCTIONS_STREISAND,
        "hiddify": texts.INSTRUCTIONS_HIDDIFY,
        "shadowrocket": texts.INSTRUCTIONS_SHADOWROCKET
    }

    text = text_map.get(app, texts.ERROR_GENERIC)

    await callback.message.edit_text(
        text,
        reply_markup=keyboards.get_back_to_instructions_keyboard()
    )
    await callback.answer()


# Support
@router.callback_query(F.data == "support")
async def callback_support(callback: CallbackQuery):
    """Show support info."""
    await callback.message.edit_text(
        texts.SUPPORT_TEXT,
        reply_markup=keyboards.get_back_to_main_keyboard()
    )
    await callback.answer()


# Admin commands
@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Show statistics (admin only)."""
    if message.from_user.id != ADMIN_ID:
        return

    db = SessionLocal()
    try:
        from backend.models import Payment, PaymentProvider
        from sqlalchemy import func

        # Count users and subscriptions
        total_users = db.query(User).count()
        active_subscriptions = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.expires_at > datetime.utcnow()
        ).count()

        # Calculate revenue by provider
        revenue_cryptobot = db.query(func.sum(Payment.amount)).filter(
            Payment.provider == PaymentProvider.CRYPTOBOT,
            Payment.status == "paid"
        ).scalar() or 0

            revenue_freekassa=revenue_freekassa / 100,
            date=datetime.utcnow().strftime("%d.%m.%Y %H:%M")
        )

        await message.answer(text)
    finally:
        db.close()


@router.message(Command("grant"))
async def cmd_grant(message: Message, command: CommandObject):
    """Grant subscription (admin only)."""
    if message.from_user.id != ADMIN_ID:
        return

    args = command.args.split() if command.args else []
    if len(args) < 2:
        await message.answer("Использование: /grant <telegram_id> <days> [devices]")
        return

    try:
        telegram_id = int(args[0])
        days = int(args[1])
        devices = int(args[2]) if len(args) > 2 else BASE_DEVICES

        db = SessionLocal()
        try:
            # Get or create user
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                user = User(telegram_id=telegram_id)
                db.add(user)
                db.commit()
                db.refresh(user)

            # Create subscription
            token = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(days=days)

            subscription = Subscription(
                user_id=user.id,
                token=token,
                status=SubscriptionStatus.ACTIVE,
                base_devices=devices,
                extra_devices=0,
                expires_at=expires_at
            )
            db.add(subscription)
            db.commit()
            db.refresh(subscription)

            # Create device slots
            create_device_slots(db, subscription.id, devices)

            text = texts.GRANT_SUCCESS.format(
                telegram_id=telegram_id,
                days=days,
                devices=devices
            )
            await message.answer(text)
        finally:
            db.close()

    except ValueError:
        await message.answer("Ошибка: неверный формат аргументов")
    except Exception as e:
        logger.error(f"Grant failed: {e}", exc_info=True)
        await message.answer(texts.ERROR_GENERIC)


@router.message(Command("revoke"))
async def cmd_revoke(message: Message, command: CommandObject):
    """Revoke subscription (admin only)."""
    if message.from_user.id != ADMIN_ID:
        return

    if not command.args:
        await message.answer("Использование: /revoke <telegram_id>")
        return

    try:
        telegram_id = int(command.args)

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                await message.answer("Пользователь не найден")
                return

            # Revoke all active subscriptions
            subscriptions = db.query(Subscription).filter(
                Subscription.user_id == user.id,
                Subscription.status == SubscriptionStatus.ACTIVE
            ).all()

            for sub in subscriptions:
                sub.status = SubscriptionStatus.REVOKED

            db.commit()

            text = texts.REVOKE_SUCCESS.format(telegram_id=telegram_id)
            await message.answer(text)
        finally:
            db.close()

    except ValueError:
        await message.answer("Ошибка: неверный telegram_id")
    except Exception as e:
        logger.error(f"Revoke failed: {e}", exc_info=True)
        await message.answer(texts.ERROR_GENERIC)


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject, state: FSMContext):
    """Start broadcast (admin only)."""
    if message.from_user.id != ADMIN_ID:
        return

    if not command.args:
        await message.answer("Использование: /broadcast <текст сообщения>")
        return

    text = command.args

    # Save message and ask for confirmation
    await state.update_data(broadcast_text=text)

    confirm_text = texts.BROADCAST_CONFIRM.format(text=text)
    await message.answer(
        confirm_text,
        reply_markup=keyboards.get_broadcast_confirm_keyboard()
    )


@router.callback_query(F.data == "broadcast:confirm")
async def callback_broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    """Confirm and send broadcast."""
    if callback.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()
    text = data.get("broadcast_text")

    if not text:
        await callback.answer("Ошибка: текст не найден", show_alert=True)
        return

    db = SessionLocal()
    try:
        users = db.query(User).all()
        total = len(users)
        sent = 0
        failed = 0

        await callback.message.edit_text(
            texts.BROADCAST_STARTED.format(total=total)
        )

        for user in users:
            try:
                await callback.bot.send_message(user.telegram_id, text)
                sent += 1
            except Exception as e:
                logger.warning(f"Failed to send broadcast to {user.telegram_id}: {e}")
                failed += 1

        await callback.message.answer(
            texts.BROADCAST_COMPLETED.format(sent=sent, failed=failed)
        )
        await callback.answer()
        await state.clear()
    finally:
        db.close()


@router.callback_query(F.data == "broadcast:cancel")
async def callback_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel broadcast."""
    await state.clear()
    await callback.message.edit_text("Рассылка отменена.")
    await callback.answer()
