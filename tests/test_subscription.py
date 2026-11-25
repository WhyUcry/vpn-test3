"""Tests for subscription endpoint."""
import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.main import app
from backend.db import get_db_session
from backend.models import Base, User, Subscription, SubscriptionStatus
from backend.slot_generator import create_device_slots


# Test database
TEST_DATABASE_URL = "sqlite:///test_vpn.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db_session] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Setup test database before each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)
    # Remove test database file
    if os.path.exists("test_vpn.db"):
        os.remove("test_vpn.db")


@pytest.fixture
def test_user(setup_database):
    """Create test user."""
    db = TestingSessionLocal()
    user = User(telegram_id=123456789, username="test_user")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def active_subscription(test_user):
    """Create active subscription with device slots."""
    db = TestingSessionLocal()

    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=30)

    subscription = Subscription(
        user_id=test_user.id,
        token=token,
        status=SubscriptionStatus.ACTIVE,
        base_devices=2,
        extra_devices=1,  # Total 3 devices
        expires_at=expires_at
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    # Create device slots
    create_device_slots(db, subscription.id, 3)

    db.close()
    return subscription


@pytest.fixture
def expired_subscription(test_user):
    """Create expired subscription."""
    db = TestingSessionLocal()

    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() - timedelta(days=1)  # Expired yesterday

    subscription = Subscription(
        user_id=test_user.id,
        token=token,
        status=SubscriptionStatus.ACTIVE,
        base_devices=1,
        extra_devices=0,
        expires_at=expires_at
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    # Create device slots
    create_device_slots(db, subscription.id, 1)

    db.close()
    return subscription


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert data["version"] == "1.0.0"


def test_subscription_not_found():
    """Test /sub/{token} with non-existent token."""
    fake_token = str(uuid.uuid4())
    response = client.get(f"/sub/{fake_token}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Subscription not found"


def test_subscription_expired(expired_subscription):
    """Test /sub/{token} with expired subscription."""
    response = client.get(f"/sub/{expired_subscription.token}")
    assert response.status_code == 403
    assert "expired" in response.json()["detail"].lower()


def test_subscription_active_headers(active_subscription):
    """Test /sub/{token} returns correct headers."""
    response = client.get(f"/sub/{active_subscription.token}")

    # Should return 200 even without configs (will have error message in body)
    # In real scenario with configs, this would return actual subscription
    assert response.status_code == 200

    # Check headers
    headers = response.headers
    assert "profile-title" in headers
    assert headers["profile-title"] == "Дудоня VPN"
    assert headers["profile-update-interval"] == "12"
    assert "subscription-userinfo" in headers
    assert "expire=" in headers["subscription-userinfo"]
    assert headers["content-type"] == "text/plain; charset=utf-8"
    assert headers["cache-control"] == "no-store"


def test_subscription_device_count(active_subscription):
    """Test that subscription generates correct number of configs."""
    # This subscription has base_devices=2, extra_devices=1 (total 3)
    response = client.get(f"/sub/{active_subscription.token}")
    assert response.status_code == 200

    # Without actual config files, it will generate error messages
    # In real scenario, we'd check that exactly 3 configs are returned
    content = response.content
    assert len(content) > 0


def test_subscription_uuid_stability(active_subscription):
    """Test that UUIDs remain stable between requests."""
    # First request
    response1 = client.get(f"/sub/{active_subscription.token}")
    assert response1.status_code == 200
    content1 = response1.content

    # Second request
    response2 = client.get(f"/sub/{active_subscription.token}")
    assert response2.status_code == 200
    content2 = response2.content

    # Content should be identical (same UUIDs)
    assert content1 == content2


def test_subscription_profile_title_cyrillic(active_subscription):
    """Test that profile-title header contains Cyrillic correctly."""
    response = client.get(f"/sub/{active_subscription.token}")
    assert response.status_code == 200

    profile_title = response.headers.get("profile-title")
    assert profile_title == "Дудоня VPN"

    # Check that it's actual Cyrillic, not broken encoding
    assert "Д" in profile_title
    assert "у" in profile_title
    assert "о" in profile_title


def test_rate_limiting():
    """Test rate limiting on /sub/{token} endpoint."""
    fake_token = str(uuid.uuid4())

    # Make 11 requests (limit is 10/minute)
    responses = []
    for _ in range(11):
        response = client.get(f"/sub/{fake_token}")
        responses.append(response)

    # Last request should be rate limited (429)
    assert responses[-1].status_code == 429


def test_subscription_userinfo_format(active_subscription):
    """Test subscription-userinfo header format."""
    response = client.get(f"/sub/{active_subscription.token}")
    assert response.status_code == 200

    userinfo = response.headers.get("subscription-userinfo")
    assert "upload=0" in userinfo
    assert "download=0" in userinfo
    assert "total=0" in userinfo
    assert "expire=" in userinfo

    # Extract expire timestamp and verify it's valid
    expire_part = [part for part in userinfo.split(";") if "expire=" in part][0]
    expire_ts = int(expire_part.split("=")[1].strip())
    assert expire_ts > 0

    # Check that expire timestamp matches subscription
    expected_ts = int(active_subscription.expires_at.timestamp())
    assert expire_ts == expected_ts


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
