"""Driver repository tests: list_for_user, get_by_user_id_and_discipline, unique (user_id, discipline)."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.models.driver import Driver
from app.models.user import User
from app.repositories.driver import DriverRepository
from app.services.auth import hash_key


TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_API_KEY = "test-multi-driver-api-key-please-change-in-prod"


@pytest.fixture
def session_with_user_and_two_drivers(db_session):
    """One user, two drivers (gt, formula). Teardown: delete drivers then user."""
    from app.models.audit_log import AuditLog
    from app.models.user_profile import UserProfile

    db_session.query(AuditLog).filter(AuditLog.actor_user_id == TEST_USER_ID).delete()
    db_session.query(UserProfile).filter(UserProfile.user_id == TEST_USER_ID).delete()
    db_session.query(Driver).filter(Driver.user_id == TEST_USER_ID).delete()
    db_session.query(User).filter(User.id == TEST_USER_ID).delete()
    db_session.commit()

    user = User(
        id=TEST_USER_ID,
        name="Repo Test",
        email="repo-multi-driver@racerpath.test",
        password_hash=None,
        role="driver",
        api_key_hash=hash_key(TEST_API_KEY),
        active=True,
    )
    db_session.add(user)
    db_session.flush()
    d1 = Driver(
        name="D1",
        primary_discipline="gt",
        sim_games=["ACC"],
        user_id=TEST_USER_ID,
        tier="E0",
    )
    d2 = Driver(
        name="D2",
        primary_discipline="formula",
        sim_games=["iRacing"],
        user_id=TEST_USER_ID,
        tier="E0",
    )
    db_session.add(d1)
    db_session.add(d2)
    db_session.commit()
    db_session.refresh(d1)
    db_session.refresh(d2)
    try:
        yield db_session
    finally:
        db_session.query(Driver).filter(Driver.user_id == TEST_USER_ID).delete()
        db_session.query(User).filter(User.id == TEST_USER_ID).delete()
        db_session.commit()


def test_list_for_user_returns_all_drivers(session_with_user_and_two_drivers):
    """list_for_user(user_id) returns all drivers for that user."""
    repo = DriverRepository(session_with_user_and_two_drivers)
    drivers = repo.list_for_user(TEST_USER_ID)
    assert len(drivers) == 2
    disciplines = {d.primary_discipline for d in drivers}
    assert disciplines == {"gt", "formula"}


def test_get_by_user_id_returns_one_driver(session_with_user_and_two_drivers):
    """get_by_user_id returns one driver (e.g. most recent)."""
    repo = DriverRepository(session_with_user_and_two_drivers)
    driver = repo.get_by_user_id(TEST_USER_ID)
    assert driver is not None
    assert driver.user_id == TEST_USER_ID


def test_get_by_user_id_and_discipline(session_with_user_and_two_drivers):
    """get_by_user_id_and_discipline returns the correct driver."""
    repo = DriverRepository(session_with_user_and_two_drivers)
    d_gt = repo.get_by_user_id_and_discipline(TEST_USER_ID, "gt")
    d_formula = repo.get_by_user_id_and_discipline(TEST_USER_ID, "formula")
    assert d_gt is not None and d_gt.primary_discipline == "gt"
    assert d_formula is not None and d_formula.primary_discipline == "formula"
    assert d_gt.id != d_formula.id
    assert repo.get_by_user_id_and_discipline(TEST_USER_ID, "rally") is None


def test_unique_user_discipline_constraint(db_session):
    """Adding a second driver with same (user_id, primary_discipline) raises IntegrityError."""
    from app.models.audit_log import AuditLog
    from app.models.user_profile import UserProfile

    uid = "00000000-0000-0000-0000-000000000099"
    db_session.query(AuditLog).filter(AuditLog.actor_user_id == uid).delete()
    db_session.query(UserProfile).filter(UserProfile.user_id == uid).delete()
    db_session.query(Driver).filter(Driver.user_id == uid).delete()
    db_session.query(User).filter(User.id == uid).delete()
    db_session.commit()

    user = User(
        id=uid,
        name="Constraint Test",
        email="constraint-multi@racerpath.test",
        password_hash=None,
        role="driver",
        api_key_hash=hash_key("key-constraint-test"),
        active=True,
    )
    db_session.add(user)
    db_session.flush()
    d1 = Driver(
        name="First",
        primary_discipline="karting",
        sim_games=["ACC"],
        user_id=uid,
        tier="E0",
    )
    db_session.add(d1)
    db_session.commit()
    db_session.refresh(d1)

    d2 = Driver(
        name="Second",
        primary_discipline="karting",
        sim_games=["iRacing"],
        user_id=uid,
        tier="E0",
    )
    db_session.add(d2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    db_session.query(Driver).filter(Driver.user_id == uid).delete()
    db_session.query(User).filter(User.id == uid).delete()
    db_session.commit()
