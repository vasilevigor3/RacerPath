"""API tests for multi-driver (Variant C): one user, multiple drivers per discipline."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_drivers_me_list_returns_all_my_drivers(client, multi_driver_user_and_drivers):
    """GET /api/drivers/me returns list of all drivers (careers) for the authenticated user."""
    _user, drivers, api_key = multi_driver_user_and_drivers
    r = client.get("/api/drivers/me", headers={"X-API-Key": api_key})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 2
    ids = {d["id"] for d in data}
    assert ids == {drivers[0].id, drivers[1].id}
    disciplines = {d["primary_discipline"] for d in data}
    assert disciplines == {"gt", "formula"}


def test_drivers_me_requires_auth(client):
    """GET /api/drivers/me without API key returns 401."""
    r = client.get("/api/drivers/me")
    assert r.status_code == 401


def test_drivers_me_post_same_discipline_returns_400(client, multi_driver_user_and_drivers):
    """POST /api/drivers/me with a discipline we already have returns 400."""
    _user, _drivers, api_key = multi_driver_user_and_drivers
    r = client.post(
        "/api/drivers/me",
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
        json={
            "name": "Another GT",
            "primary_discipline": "gt",
            "sim_games": ["Assetto Corsa Competizione"],
        },
    )
    assert r.status_code == 400
    assert "already have a driver" in (r.json().get("detail") or "").lower()


def test_drivers_me_post_new_discipline_returns_201(client, multi_driver_user_and_drivers):
    """POST /api/drivers/me with a new discipline creates a third driver (career)."""
    _user, drivers, api_key = multi_driver_user_and_drivers
    r = client.post(
        "/api/drivers/me",
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
        json={
            "name": "Rally Driver",
            "primary_discipline": "rally",
            "sim_games": ["RBR"],
        },
    )
    assert r.status_code in (200, 201)
    data = r.json()
    assert data["primary_discipline"] == "rally"
    assert data["name"] == "Rally Driver"
    new_id = data["id"]
    # List now has 3 drivers
    r2 = client.get("/api/drivers/me", headers={"X-API-Key": api_key})
    assert r2.status_code == 200
    list_data = r2.json()
    assert len(list_data) == 3
    assert new_id in {d["id"] for d in list_data}
    # Cleanup: delete the driver we created (so fixture teardown doesn't fail on constraint)
    from app.db.session import SessionLocal
    from app.models.driver import Driver
    session = SessionLocal()
    try:
        session.query(Driver).filter(Driver.id == new_id).delete()
        session.commit()
    finally:
        session.close()


def test_profile_me_with_driver_id_returns_200(client, multi_driver_user_and_drivers):
    """GET /api/profile/me?driver_id=<my_driver> returns profile for that career."""
    _user, drivers, api_key = multi_driver_user_and_drivers
    driver_id = drivers[0].id
    r = client.get(f"/api/profile/me?driver_id={driver_id}", headers={"X-API-Key": api_key})
    assert r.status_code == 200
    data = r.json()
    assert "profile_completion_percent" in data


def test_profile_me_without_driver_id_uses_first_driver(client, multi_driver_user_and_drivers):
    """GET /api/profile/me without driver_id uses first driver (backward compat)."""
    r = client.get("/api/profile/me", headers={"X-API-Key": multi_driver_user_and_drivers[2]})
    assert r.status_code == 200


def test_penalties_with_my_driver_id_returns_200(client, multi_driver_user_and_drivers):
    """GET /api/penalties?driver_id=<my_driver> returns list (may be empty)."""
    _user, drivers, api_key = multi_driver_user_and_drivers
    r = client.get(f"/api/penalties?driver_id={drivers[0].id}", headers={"X-API-Key": api_key})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_penalties_with_other_users_driver_returns_403(
    client, multi_driver_user_and_drivers, other_user_and_driver
):
    """GET /api/penalties?driver_id=<other_users_driver> with my key returns 403."""
    _user, _drivers, api_key = multi_driver_user_and_drivers
    _other_user, other_driver, _other_key = other_user_and_driver
    r = client.get(
        f"/api/penalties?driver_id={other_driver.id}",
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 403


def test_incidents_with_my_driver_id_returns_200(client, multi_driver_user_and_drivers):
    """GET /api/incidents?driver_id=<my_driver> returns list."""
    _user, drivers, api_key = multi_driver_user_and_drivers
    r = client.get(f"/api/incidents?driver_id={drivers[1].id}", headers={"X-API-Key": api_key})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_incidents_with_other_users_driver_returns_403(
    client, multi_driver_user_and_drivers, other_user_and_driver
):
    """GET /api/incidents?driver_id=<other_users_driver> with my key returns 403."""
    _user, _drivers, api_key = multi_driver_user_and_drivers
    _other_user, other_driver, _other_key = other_user_and_driver
    r = client.get(
        f"/api/incidents?driver_id={other_driver.id}",
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 403


def test_tasks_completions_with_my_driver_id_returns_200(client, multi_driver_user_and_drivers):
    """GET /api/tasks/completions?driver_id=<my_driver> returns list."""
    _user, drivers, api_key = multi_driver_user_and_drivers
    r = client.get(
        f"/api/tasks/completions?driver_id={drivers[0].id}",
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_tasks_completions_with_other_users_driver_returns_403(
    client, multi_driver_user_and_drivers, other_user_and_driver
):
    """GET /api/tasks/completions?driver_id=<other_users_driver> with my key returns 403."""
    _user, _drivers, api_key = multi_driver_user_and_drivers
    _other_user, other_driver, _other_key = other_user_and_driver
    r = client.get(
        f"/api/tasks/completions?driver_id={other_driver.id}",
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 403


def test_get_driver_by_id_own_returns_200(client, multi_driver_user_and_drivers):
    """GET /api/drivers/<id> for own driver returns 200."""
    _user, drivers, api_key = multi_driver_user_and_drivers
    r = client.get(f"/api/drivers/{drivers[0].id}", headers={"X-API-Key": api_key})
    assert r.status_code == 200
    assert r.json()["id"] == drivers[0].id


def test_get_driver_by_id_other_users_returns_403(
    client, multi_driver_user_and_drivers, other_user_and_driver
):
    """GET /api/drivers/<id> for another user's driver with my key returns 403."""
    _user, _drivers, api_key = multi_driver_user_and_drivers
    _other_user, other_driver, _other_key = other_user_and_driver
    r = client.get(f"/api/drivers/{other_driver.id}", headers={"X-API-Key": api_key})
    assert r.status_code == 403


def test_patch_driver_own_returns_200(client, multi_driver_user_and_drivers):
    """PATCH /api/drivers/<id> for own driver updates and returns 200."""
    _user, drivers, api_key = multi_driver_user_and_drivers
    r = client.patch(
        f"/api/drivers/{drivers[0].id}",
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
        json={"name": "Updated GT Name"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Updated GT Name"
    # Restore for other tests / teardown
    client.patch(
        f"/api/drivers/{drivers[0].id}",
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
        json={"name": "Test GT Driver"},
    )


def test_patch_driver_other_users_returns_403(
    client, multi_driver_user_and_drivers, other_user_and_driver
):
    """PATCH /api/drivers/<id> for another user's driver returns 403."""
    _user, _drivers, api_key = multi_driver_user_and_drivers
    _other_user, other_driver, _other_key = other_user_and_driver
    r = client.patch(
        f"/api/drivers/{other_driver.id}",
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
        json={"name": "Hacked"},
    )
    assert r.status_code == 403


def test_penalties_count_with_my_driver_returns_200(client, multi_driver_user_and_drivers):
    """GET /api/penalties/count?driver_id=<my_driver> returns 200 with total."""
    _user, drivers, api_key = multi_driver_user_and_drivers
    r = client.get(
        f"/api/penalties/count?driver_id={drivers[0].id}",
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 200
    data = r.json()
    assert "total" in data


def test_incidents_count_with_my_driver_returns_200(client, multi_driver_user_and_drivers):
    """GET /api/incidents/count?driver_id=<my_driver> returns 200 with total."""
    _user, drivers, api_key = multi_driver_user_and_drivers
    r = client.get(
        f"/api/incidents/count?driver_id={drivers[0].id}",
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 200
    assert "total" in r.json()


def test_participations_with_my_driver_id_returns_200(client, multi_driver_user_and_drivers):
    """GET /api/participations?driver_id=<my_driver> returns list."""
    _user, drivers, api_key = multi_driver_user_and_drivers
    r = client.get(
        f"/api/participations?driver_id={drivers[0].id}",
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_participations_with_other_users_driver_returns_403(
    client, multi_driver_user_and_drivers, other_user_and_driver
):
    """GET /api/participations?driver_id=<other_users_driver> with my key returns 403."""
    _user, _drivers, api_key = multi_driver_user_and_drivers
    _other_user, other_driver, _other_key = other_user_and_driver
    r = client.get(
        f"/api/participations?driver_id={other_driver.id}",
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 403


def test_delete_driver_own_returns_204(client, multi_driver_user_and_drivers):
    """DELETE /api/drivers/<id> for own driver removes it and returns 204."""
    _user, drivers, api_key = multi_driver_user_and_drivers
    to_delete_id = drivers[1].id
    r = client.delete(f"/api/drivers/{to_delete_id}", headers={"X-API-Key": api_key})
    assert r.status_code == 204
    list_r = client.get("/api/drivers/me", headers={"X-API-Key": api_key})
    assert list_r.status_code == 200
    remaining = list_r.json()
    assert len(remaining) == 1
    assert remaining[0]["id"] == drivers[0].id


def test_delete_driver_other_users_returns_403(
    client, multi_driver_user_and_drivers, other_user_and_driver
):
    """DELETE /api/drivers/<id> for another user's driver returns 403."""
    _user, _drivers, api_key = multi_driver_user_and_drivers
    _other_user, other_driver, _other_key = other_user_and_driver
    r = client.delete(f"/api/drivers/{other_driver.id}", headers={"X-API-Key": api_key})
    assert r.status_code == 403
