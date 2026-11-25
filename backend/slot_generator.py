"""Device slot UUID generator with stable IDs."""
import uuid
import hashlib
from sqlalchemy.orm import Session
from backend.models import DeviceSlot, Subscription
from loguru import logger
from typing import List


def generate_stable_uuid(subscription_id: int, slot_index: int, seed: str = "dudonya-vpn") -> str:
    """
    Generate stable UUID based on subscription_id and slot_index.
    Same inputs always produce same UUID.

    Args:
        subscription_id: Subscription ID
        slot_index: Slot index (1 to MAX_DEVICES)
        seed: Salt for hash generation

    Returns:
        UUID string
    """
    # Create deterministic hash from subscription_id + slot_index + seed
    data = f"{seed}:{subscription_id}:{slot_index}".encode('utf-8')
    hash_digest = hashlib.sha256(data).hexdigest()

    # Convert hash to UUID format (use first 32 hex chars)
    uuid_str = f"{hash_digest[:8]}-{hash_digest[8:12]}-{hash_digest[12:16]}-{hash_digest[16:20]}-{hash_digest[20:32]}"
    return uuid_str


def generate_short_id(subscription_id: int, slot_index: int) -> str:
    """
    Generate stable short ID (8 chars) for {{SHORT_ID}} placeholder.

    Args:
        subscription_id: Subscription ID
        slot_index: Slot index

    Returns:
        8-character hex string
    """
    data = f"short:{subscription_id}:{slot_index}".encode('utf-8')
    hash_digest = hashlib.md5(data).hexdigest()
    return hash_digest[:8]


def create_device_slots(db: Session, subscription_id: int, num_slots: int) -> List[DeviceSlot]:
    """
    Create device slots for a subscription.

    Args:
        db: Database session
        subscription_id: Subscription ID
        num_slots: Number of slots to create

    Returns:
        List of created DeviceSlot objects
    """
    logger.info(f"Creating {num_slots} device slots for subscription {subscription_id}")

    # Check existing slots
    existing_slots = db.query(DeviceSlot).filter(
        DeviceSlot.subscription_id == subscription_id
    ).all()

    existing_count = len(existing_slots)
    logger.debug(f"Existing slots: {existing_count}")

    # If we already have enough slots, return existing
    if existing_count >= num_slots:
        logger.info(f"Subscription {subscription_id} already has {existing_count} slots")
        return existing_slots[:num_slots]

    # Create additional slots
    new_slots = []
    for slot_index in range(existing_count + 1, num_slots + 1):
        slot_uuid = generate_stable_uuid(subscription_id, slot_index)
        short_id = generate_short_id(subscription_id, slot_index)

        slot = DeviceSlot(
            subscription_id=subscription_id,
            slot_index=slot_index,
            uuid=slot_uuid,
            short_id=short_id
        )
        db.add(slot)
        new_slots.append(slot)
        logger.debug(f"Created slot {slot_index}: uuid={slot_uuid[:8]}..., short_id={short_id}")

    db.commit()
    logger.info(f"Created {len(new_slots)} new device slots")

    # Return all slots (existing + new)
    all_slots = existing_slots + new_slots
    return sorted(all_slots, key=lambda s: s.slot_index)


def get_device_slots(db: Session, subscription_id: int) -> List[DeviceSlot]:
    """
    Get all device slots for a subscription, ordered by slot_index.

    Args:
        db: Database session
        subscription_id: Subscription ID

    Returns:
        List of DeviceSlot objects
    """
    slots = db.query(DeviceSlot).filter(
        DeviceSlot.subscription_id == subscription_id
    ).order_by(DeviceSlot.slot_index).all()

    return slots


def add_device_slot(db: Session, subscription_id: int) -> DeviceSlot:
    """
    Add one more device slot to subscription.

    Args:
        db: Database session
        subscription_id: Subscription ID

    Returns:
        Newly created DeviceSlot
    """
    # Get current max slot index
    existing_slots = get_device_slots(db, subscription_id)
    next_index = len(existing_slots) + 1

    logger.info(f"Adding device slot {next_index} to subscription {subscription_id}")

    slot_uuid = generate_stable_uuid(subscription_id, next_index)
    short_id = generate_short_id(subscription_id, next_index)

    slot = DeviceSlot(
        subscription_id=subscription_id,
        slot_index=next_index,
        uuid=slot_uuid,
        short_id=short_id
    )
    db.add(slot)
    db.commit()

    logger.info(f"Added device slot {next_index}: uuid={slot_uuid[:8]}..., short_id={short_id}")
    return slot
