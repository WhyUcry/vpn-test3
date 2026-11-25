"""Subscription generation and config serving logic."""
import base64
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from urllib.parse import quote

from loguru import logger
from sqlalchemy.orm import Session

from backend.models import Subscription, SubscriptionStatus
from backend.slot_generator import get_device_slots


MAX_DEVICES = int(os.getenv("MAX_DEVICES", "5"))
CONFIGS_DIR = os.getenv("CONFIGS_DIR", "configs")


class SubscriptionError(Exception):
    """Base exception for subscription errors."""
    pass


class SubscriptionNotFoundError(SubscriptionError):
    """Subscription not found."""
    pass


class SubscriptionExpiredError(SubscriptionError):
    """Subscription expired or inactive."""
    pass


def load_config_files() -> List[Tuple[str, str, str]]:
    """
    Load all config files from CONFIGS_DIR.

    Returns:
        List of tuples (filename, content, format) where format is 'json' or 'text'
    """
    configs_path = Path(CONFIGS_DIR)
    if not configs_path.exists():
        logger.warning(f"Configs directory not found: {CONFIGS_DIR}")
        return []

    configs = []
    for file_path in configs_path.iterdir():
        if file_path.is_file() and not file_path.name.startswith('.'):
            try:
                content = file_path.read_text(encoding='utf-8')

                # Determine format
                file_format = 'json' if file_path.suffix.lower() == '.json' else 'text'

                # Validate JSON if format is json
                if file_format == 'json':
                    try:
                        json.loads(content)  # Validate JSON
                        logger.debug(f"Loaded JSON config: {file_path.name}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in {file_path.name}: {e}")
                        continue

                configs.append((file_path.name, content, file_format))
                logger.debug(f"Loaded config: {file_path.name} ({len(content)} bytes, format={file_format})")
            except Exception as e:
                logger.error(f"Failed to load config {file_path.name}: {e}")

    logger.info(f"Loaded {len(configs)} config files from {CONFIGS_DIR}")
    return configs


def parse_json_config(content: str) -> Dict[str, Any]:
    """
    Parse JSON config file.

    Expected formats:
    1. {"configs": ["vless://...", "ss://..."]}
    2. {"servers": [{"url": "vless://...", "name": "Server1"}]}
    3. {"template": "vless://{{UUID}}@..."}
    4. {"url": "vless://..."}

    Args:
        content: JSON content

    Returns:
        Parsed JSON object
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON config: {e}")
        return {}


def extract_urls_from_json(json_data: Dict[str, Any]) -> List[str]:
    """
    Extract URL strings from JSON config.

    Supports multiple formats:
    - {"configs": ["url1", "url2"]}
    - {"servers": [{"url": "..."}, {"url": "..."}]}
    - {"template": "url"}
    - {"url": "..."}

    Args:
        json_data: Parsed JSON object

    Returns:
        List of URL strings
    """
    urls = []

    # Format 1: {"configs": [...]}
    if "configs" in json_data:
        configs = json_data["configs"]
        if isinstance(configs, list):
            urls.extend([str(c) for c in configs if c])

    # Format 2: {"servers": [{"url": ...}]}
    if "servers" in json_data:
        servers = json_data["servers"]
        if isinstance(servers, list):
            for server in servers:
                if isinstance(server, dict) and "url" in server:
                    urls.append(str(server["url"]))
                elif isinstance(server, str):
                    urls.append(server)

    # Format 3: {"template": "..."}
    if "template" in json_data and not urls:
        urls.append(str(json_data["template"]))

    # Format 4: {"url": "..."}
    if "url" in json_data and not urls:
        urls.append(str(json_data["url"]))

    return urls


def has_placeholders(content: str) -> bool:
    """
    Check if content has placeholders like {{UUID}}, {{DEVICE_ID}}, {{SHORT_ID}}.

    Args:
        content: Config content

    Returns:
        True if placeholders found
    """
    placeholders = [r'\{\{UUID\}\}', r'\{\{DEVICE_ID\}\}', r'\{\{SHORT_ID\}\}']
    for placeholder in placeholders:
        if re.search(placeholder, content, re.IGNORECASE):
            return True
    return False


def substitute_placeholders(content: str, uuid: str, device_id: str, short_id: str) -> str:
    """
    Substitute placeholders in config content.

    Args:
        content: Config content with placeholders
        uuid: UUID to substitute for {{UUID}}
        device_id: Device ID to substitute for {{DEVICE_ID}}
        short_id: Short ID to substitute for {{SHORT_ID}}

    Returns:
        Content with substituted values
    """
    # Case-insensitive replacement
    result = re.sub(r'\{\{UUID\}\}', uuid, content, flags=re.IGNORECASE)
    result = re.sub(r'\{\{DEVICE_ID\}\}', device_id, result, flags=re.IGNORECASE)
    result = re.sub(r'\{\{SHORT_ID\}\}', short_id, result, flags=re.IGNORECASE)
    return result


def generate_configs_for_slots(db: Session, subscription: Subscription) -> List[str]:
    """
    Generate configs for all device slots.

    Logic:
    1. Load config files from CONFIGS_DIR (supports JSON and text)
    2. Parse JSON configs to extract URLs
    3. Check if they have placeholders
    4. If yes: substitute {{UUID}}, {{DEVICE_ID}}, {{SHORT_ID}} for each slot
    5. If no: return first N configs (or repeat if fewer than slots)

    Args:
        db: Database session
        subscription: Subscription object

    Returns:
        List of config strings (one per device slot)
    """
    device_limit = subscription.base_devices + subscription.extra_devices
    if device_limit > MAX_DEVICES:
        device_limit = MAX_DEVICES

    logger.debug(f"Generating {device_limit} configs for subscription {subscription.token[:8]}...")

    # Get device slots
    slots = get_device_slots(db, subscription.id)
    if len(slots) < device_limit:
        logger.warning(
            f"Subscription {subscription.id} has {len(slots)} slots but needs {device_limit}. "
            f"This should not happen - slots should be created when subscription is created/extended."
        )
        # Use available slots only
        device_limit = len(slots)

    # Load config files
    config_files = load_config_files()
    if not config_files:
        logger.error("No config files found!")
        return [f"# Error: No config files in {CONFIGS_DIR}"] * device_limit

    # Parse configs and extract URLs
    all_urls = []
    for filename, content, file_format in config_files:
        if file_format == 'json':
            # Parse JSON and extract URLs
            json_data = parse_json_config(content)
            urls = extract_urls_from_json(json_data)
            all_urls.extend(urls)
            logger.debug(f"Extracted {len(urls)} URLs from JSON config {filename}")
        else:
            # Text format - use as-is
            all_urls.append(content.strip())

    if not all_urls:
        logger.error("No URLs found in config files!")
        return [f"# Error: No URLs in configs"] * device_limit

    # Check if any config has placeholders
    has_any_placeholders = any(has_placeholders(url) for url in all_urls)

    configs = []

    if has_any_placeholders:
        # Template mode: substitute placeholders for each slot
        logger.info(f"Using template mode (placeholders detected)")

        # Use first URL as template (or cycle through if multiple)
        for i, slot in enumerate(slots[:device_limit]):
            # Pick URL (cycle if multiple templates)
            template = all_urls[i % len(all_urls)]

            # Substitute placeholders
            config = substitute_placeholders(
                template,
                uuid=slot.uuid,
                device_id=slot.uuid,  # DEVICE_ID = UUID (can be customized)
                short_id=slot.short_id
            )
            configs.append(config)
            logger.debug(f"Generated config for slot {slot.slot_index} with uuid={slot.uuid[:8]}...")

    else:
        # Static mode: return first N configs (or cycle)
        logger.warning(
            f"Using static mode (no placeholders found). "
            f"Device limit is soft only - no unique IDs per device!"
        )

        for i in range(device_limit):
            # Cycle through available URLs
            config = all_urls[i % len(all_urls)]
            configs.append(config)

    return configs


def is_wireguard_config(configs: List[str]) -> bool:
    """
    Check if configs are WireGuard format (.conf).

    Args:
        configs: List of config strings

    Returns:
        True if WireGuard format detected
    """
    if not configs:
        return False

    # Check first config for WireGuard markers
    first_config = configs[0]
    return '[Interface]' in first_config and '[Peer]' in first_config


def encode_subscription(configs: List[str]) -> bytes:
    """
    Encode configs as subscription content.

    For WireGuard: return plain text
    For v2ray protocols (vless://, ss://, vmess://, trojan://): return base64

    Args:
        configs: List of config strings

    Returns:
        Encoded content (bytes)
    """
    # Join configs with newlines
    content = '\n\n'.join(configs)

    # Check if WireGuard
    if is_wireguard_config(configs):
        logger.debug("Encoding as WireGuard (plain text)")
        return content.encode('utf-8')

    # Otherwise, base64 encode (standard, not url-safe)
    logger.debug("Encoding as base64 (v2ray protocols)")
    encoded = base64.b64encode(content.encode('utf-8'))
    return encoded


def generate_subscription_response(
    db: Session,
    token: str
) -> Tuple[bytes, dict]:
    """
    Generate subscription response for given token.

    Args:
        db: Database session
        token: Subscription token (UUID)

    Returns:
        Tuple of (content_bytes, headers_dict)

    Raises:
        SubscriptionNotFoundError: Subscription not found
        SubscriptionExpiredError: Subscription expired or inactive
    """
    logger.info(f"Generating subscription for token {token[:8]}...")

    # Find subscription
    subscription = db.query(Subscription).filter(Subscription.token == token).first()
    if not subscription:
        logger.warning(f"Subscription not found: {token[:8]}...")
        raise SubscriptionNotFoundError("Subscription not found")

    # Check status and expiry
    now = datetime.utcnow()
    if subscription.status != SubscriptionStatus.ACTIVE:
        logger.warning(f"Subscription {token[:8]}... is not active (status={subscription.status})")
        raise SubscriptionExpiredError("Subscription is not active")

    if subscription.expires_at < now:
        logger.warning(f"Subscription {token[:8]}... has expired (expired_at={subscription.expires_at})")
        raise SubscriptionExpiredError("Subscription has expired")

    # Generate configs
    configs = generate_configs_for_slots(db, subscription)

    # Encode
    content = encode_subscription(configs)

    # Prepare headers
    # CRITICAL: profile-title must support Cyrillic
    profile_title = "Дудоня VPN"

    # Calculate expire timestamp
    expire_ts = int(subscription.expires_at.timestamp())

    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-store",
        "profile-title": profile_title,  # Try direct Cyrillic
        "profile-update-interval": "12",
        "subscription-userinfo": f"upload=0; download=0; total=0; expire={expire_ts}",
        # Fallback for apps that don't support profile-title header
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(profile_title)}"
    }

    logger.info(
        f"Generated subscription for {token[:8]}...: "
        f"{len(configs)} configs, {len(content)} bytes, expires {subscription.expires_at.isoformat()}"
    )

    return content, headers
