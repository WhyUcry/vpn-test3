"""Database models for Dudonya VPN."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


class SubscriptionStatus(str, enum.Enum):
    """Subscription status enum."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class PaymentStatus(str, enum.Enum):
    """Payment status enum."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentProvider(str, enum.Enum):
    """Payment provider enum."""
    CRYPTOBOT = "cryptobot"
    FREEKASSA = "freekassa"


class PaymentPurpose(str, enum.Enum):
    """Payment purpose enum."""
    SUBSCRIPTION = "subscription"
    EXTRA_DEVICE = "extra_device"


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
    payments = relationship("Payment", back_populates="user")


class Subscription(Base):
    """Subscription model."""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(36), unique=True, nullable=False, index=True)  # UUID
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)
    base_devices = Column(Integer, default=1, nullable=False)
    extra_devices = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    device_slots = relationship("DeviceSlot", back_populates="subscription", cascade="all, delete-orphan")


class DeviceSlot(Base):
    """Device slot model - each slot has stable UUIDs for config generation."""
    __tablename__ = "device_slots"

    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    slot_index = Column(Integer, nullable=False)  # 1 to MAX_DEVICES
    uuid = Column(String(36), nullable=False)  # For {{UUID}} placeholder
    short_id = Column(String(8), nullable=False)  # For {{SHORT_ID}} placeholder
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    subscription = relationship("Subscription", back_populates="device_slots")

    def __repr__(self):
        return f"<DeviceSlot(subscription_id={self.subscription_id}, slot={self.slot_index}, uuid={self.uuid[:8]}...)>"


class Payment(Base):
    """Payment model."""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # Amount in smallest currency unit (kopeks, cents)
    currency = Column(String(3), default="RUB", nullable=False)
    provider = Column(SQLEnum(PaymentProvider), nullable=False)
    purpose = Column(SQLEnum(PaymentPurpose), nullable=False)
    provider_payment_id = Column(String, unique=True, nullable=False, index=True)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    extra_data = Column(String, nullable=True)  # JSON string for additional data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="payments")


class PendingPayment(Base):
    """Temporary storage for pending payments (for idempotency)."""
    __tablename__ = "pending_payments"

    id = Column(Integer, primary_key=True)
    order_id = Column(String, unique=True, nullable=False, index=True)
    idempotency_key = Column(String, unique=True, nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String(3), default="RUB", nullable=False)
    purpose = Column(SQLEnum(PaymentPurpose), nullable=False)
    provider = Column(SQLEnum(PaymentProvider), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
