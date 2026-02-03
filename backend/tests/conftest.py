"""Pytest fixtures for multi-driver (Variant C) and API tests."""
import pytest

from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.driver import Driver
from app.models.user import User
from app.models.user_profile import UserProfile
from app.services.auth import hash_key


# Fixed API key for test user so tests can send X-API-Key header.
TEST_API_KEY = "test-multi-driver-api-key-please-change-in-prod"
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_USER_EMAIL = "multi-driver-test@racerpath.test"


@pytest.fixture
def db_session():
    """Provide a DB session; rollback after test so no commit persists (optional)."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def multi_driver_user_and_drivers(db_session):
    """
    Create one user with two drivers (gt, formula). Yield (user, [driver_gt, driver_formula], api_key).
    Removes drivers and user in teardown. Cleans any existing test user/drivers first.
    """
    # Clean leftover from previous runs (order: FKs first)
    db_session.query(AuditLog).filter(AuditLog.actor_user_id == TEST_USER_ID).delete()
    db_session.query(UserProfile).filter(UserProfile.user_id == TEST_USER_ID).delete()
    db_session.query(Driver).filter(Driver.user_id == TEST_USER_ID).delete()
    db_session.query(User).filter(User.id == TEST_USER_ID).delete()
    db_session.commit()

    user = User(
        id=TEST_USER_ID,
        name="Multi Driver Test",
        email=TEST_USER_EMAIL,
        password_hash=None,
        role="driver",
        api_key_hash=hash_key(TEST_API_KEY),
        active=True,
    )
    db_session.add(user)
    db_session.flush()  # ensure user is inserted before drivers (FK)
    driver_gt = Driver(
        name="Test GT Driver",
        primary_discipline="gt",
        sim_games=["Assetto Corsa Competizione"],
        user_id=TEST_USER_ID,
        tier="E0",
    )
    driver_formula = Driver(
        name="Test Formula Driver",
        primary_discipline="formula",
        sim_games=["iRacing"],
        user_id=TEST_USER_ID,
        tier="E0",
    )
    db_session.add(driver_gt)
    db_session.add(driver_formula)
    db_session.commit()
    db_session.refresh(driver_gt)
    db_session.refresh(driver_formula)
    db_session.refresh(user)
    try:
        yield user, [driver_gt, driver_formula], TEST_API_KEY
    finally:
        db_session.query(AuditLog).filter(AuditLog.actor_user_id == TEST_USER_ID).delete()
        db_session.query(UserProfile).filter(UserProfile.user_id == TEST_USER_ID).delete()
        db_session.query(Driver).filter(Driver.user_id == TEST_USER_ID).delete()
        db_session.query(User).filter(User.id == TEST_USER_ID).delete()
        db_session.commit()


@pytest.fixture
def other_user_and_driver(db_session):
    """Create another user with one driver (for 403 tests). Yield (user, driver, api_key)."""
    from app.services.auth import hash_key as _hash

    other_id = "00000000-0000-0000-0000-000000000002"
    db_session.query(AuditLog).filter(AuditLog.actor_user_id == other_id).delete()
    db_session.query(UserProfile).filter(UserProfile.user_id == other_id).delete()
    db_session.query(Driver).filter(Driver.user_id == other_id).delete()
    db_session.query(User).filter(User.id == other_id).delete()
    db_session.commit()
    other_key = "other-user-api-key-multi-driver-test"
    user = User(
        id=other_id,
        name="Other User",
        email="other-multi-driver-test@racerpath.test",
        password_hash=None,
        role="driver",
        api_key_hash=_hash(other_key),
        active=True,
    )
    db_session.add(user)
    db_session.flush()
    driver = Driver(
        name="Other Driver",
        primary_discipline="rally",
        sim_games=["RBR"],
        user_id=other_id,
        tier="E0",
    )
    db_session.add(driver)
    db_session.commit()
    db_session.refresh(driver)
    db_session.refresh(user)
    try:
        yield user, driver, other_key
    finally:
        db_session.query(AuditLog).filter(AuditLog.actor_user_id == other_id).delete()
        db_session.query(UserProfile).filter(UserProfile.user_id == other_id).delete()
        db_session.query(Driver).filter(Driver.user_id == other_id).delete()
        db_session.query(User).filter(User.id == other_id).delete()
        db_session.commit()
