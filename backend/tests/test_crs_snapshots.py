"""Tests: inputs_hash, recompute_crs writes computed_from_participation_id and stable inputs_hash."""
import json
import hashlib

import pytest

from app.services.crs import compute_inputs, compute_inputs_hash, recompute_crs


def test_compute_inputs_hash_deterministic():
    inputs = {"a": 1, "b": 2, "c": [3, 4]}
    h1 = compute_inputs_hash(inputs)
    h2 = compute_inputs_hash(inputs)
    assert h1 == h2
    assert len(h1) == 64


def test_compute_inputs_hash_sorted_keys():
    h1 = compute_inputs_hash({"b": 1, "a": 2})
    h2 = compute_inputs_hash({"a": 2, "b": 1})
    assert h1 == h2


def test_compute_inputs_hash_sha256():
    payload = json.dumps({"x": 1}, sort_keys=True).encode("utf-8")
    expected = hashlib.sha256(payload).hexdigest()
    assert compute_inputs_hash({"x": 1}) == expected


class TestRecomputeCrsSnapshot:
    """DB-dependent: recompute_crs sets computed_from_participation_id and stable inputs_hash."""

    @pytest.fixture
    def session(self):
        from app.db.session import SessionLocal
        session = SessionLocal()
        try:
            yield session
        finally:
            session.rollback()
            session.close()

    def test_recompute_crs_writes_inputs_hash_and_anchor(self, session):
        from app.models.driver import Driver
        driver = session.query(Driver).first()
        if not driver:
            pytest.skip("no drivers")
        discipline = driver.primary_discipline or "gt"
        rec = recompute_crs(session, driver.id, discipline, trigger_participation_id=None)
        assert rec.inputs_hash is not None
        assert rec.inputs_hash != ""
        assert rec.algo_version == "crs_v1"
        assert rec.computed_from_participation_id is None

    def test_recompute_crs_stable_inputs_hash_same_data(self, session):
        from app.models.driver import Driver
        driver = session.query(Driver).first()
        if not driver:
            pytest.skip("no drivers")
        discipline = driver.primary_discipline or "gt"
        rec1 = recompute_crs(session, driver.id, discipline, None)
        rec2 = recompute_crs(session, driver.id, discipline, None)
        assert rec1.inputs_hash == rec2.inputs_hash
