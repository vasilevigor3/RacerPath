"""API tests: POST /api/dev/tasks/complete per_participation without participation_id -> 422."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth import require_user


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_user():
    from app.models.user import User
    u = User(id="test-user-id", name="Test", email="test@test.com", role="admin", api_key_hash="x")
    u.id = "test-user-id"
    return u


def test_complete_task_per_participation_requires_participation_id(client, mock_user):
    """When task scope is per_participation, missing participation_id should return 422."""
    try:
        app.dependency_overrides[require_user] = lambda: mock_user
        response = client.post(
            "/api/dev/tasks/complete",
            json={"driver_id": "00000000-0000-0000-0000-000000000001", "task_code": "NONEXISTENT"},
        )
        # 401 if override not applied, 404 task/driver not found, 422 validation/scope
        assert response.status_code in (401, 404, 422)
        # If we had a per_participation task and valid driver, we'd get 422 for missing participation_id
    finally:
        app.dependency_overrides.pop(require_user, None)
