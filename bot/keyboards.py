"""Keyboard layouts for Dudonya VPN bot."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# Main menu
def get_main_menu_keyboard(has_subscription: bool = False) -> InlineKeyboardMarkup:
    """
    Get main menu keyboard.

    Args:
        has_subscription: Whether user has active subscription

    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()

    if has_subscription:
        builder.button(text="📱 Моя подписка", callback_data="my_subscription")
        builder.button(text="🔄 Продлить", callback_data="pricing")
        builder.button(text="➕ Докупить устройство", callback_data="extra_device")
    else:
        builder.button(text="💰 Купить подписку", callback_data="pricing")

    builder.button(text="📖 Как подключить", callback_data="instructions_menu")
    builder.button(text="💬 Поддержка", callback_data="support")

    builder.adjust(2 if has_subscription else 1)
    return builder.as_markup()


# Pricing keyboard
def get_pricing_keyboard() -> InlineKeyboardMarkup:
    """Get pricing keyboard with tariff options."""
    builder = InlineKeyboardBuilder()

    builder.button(text="📅 1 месяц", callback_data="buy:1m")
    builder.button(text="📅 3 месяца", callback_data="buy:3m")
    builder.button(text="📅 12 месяцев", callback_data="buy:12m")
    builder.button(text="◀️ Назад", callback_data="main_menu")

    builder.adjust(1)
    return builder.as_markup()


# Payment method keyboard
def get_payment_method_keyboard(plan: str, cryptobot_enabled: bool, freekassa_enabled: bool) -> InlineKeyboardMarkup:
    """
    Get payment method selection keyboard.

    Args:
        plan: Plan identifier (1m, 3m, 12m, extra_device)
        cryptobot_enabled: CryptoBot enabled
        freekassa_enabled: Freekassa enabled

    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()

    if cryptobot_enabled:
        builder.button(text="💎 CryptoBot", callback_data=f"pay:cryptobot:{plan}")

    if freekassa_enabled:
        builder.button(text="💳 Фрикасса", callback_data=f"pay:freekassa:{plan}")

    builder.button(text="◀️ Назад", callback_data="pricing")

    builder.adjust(1)
    return builder.as_markup()


# Instructions menu
def get_instructions_keyboard() -> InlineKeyboardMarkup:
    """Get instructions menu keyboard."""
    builder = InlineKeyboardBuilder()

    builder.button(text="📱 Happ", callback_data="instructions:happ")
    builder.button(text="📱 v2rayNG", callback_data="instructions:v2rayng")
    builder.button(text="📱 Streisand", callback_data="instructions:streisand")
    builder.button(text="📱 Hiddify", callback_data="instructions:hiddify")
    builder.button(text="📱 Shadowrocket", callback_data="instructions:shadowrocket")
    builder.button(text="◀️ Назад", callback_data="main_menu")

    builder.adjust(2)
    return builder.as_markup()


# Back to instructions menu
def get_back_to_instructions_keyboard() -> InlineKeyboardMarkup:
    """Get back to instructions menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ К списку приложений", callback_data="instructions_menu")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


# Back to main menu
def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Get back to main menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    return builder.as_markup()


# Extra device keyboard
def get_extra_device_keyboard() -> InlineKeyboardMarkup:
    """Get extra device purchase keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Купить устройство", callback_data="buy:extra_device")
    builder.button(text="◀️ Назад", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


# Admin broadcast confirm
def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Get broadcast confirmation keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, отправить", callback_data="broadcast:confirm")
    builder.button(text="❌ Отмена", callback_data="broadcast:cancel")
    builder.adjust(2)
    return builder.as_markup()


# Copy subscription URL
def get_copy_subscription_keyboard(url: str) -> InlineKeyboardMarkup:
    """
    Get keyboard with copy subscription URL button.

    Args:
        url: Subscription URL

    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Скопировать ссылку", callback_data=f"copy_url")
    builder.button(text="📖 Как подключить", callback_data="instructions_menu")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()
