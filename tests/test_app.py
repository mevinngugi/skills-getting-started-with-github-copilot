import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    # Snapshot activities before the test and restore afterwards to keep tests isolated
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_get_activities():
    res = client.get("/activities")
    assert res.status_code == 200
    data = res.json()
    # basic expectation: known activity exists
    assert "Chess Club" in data


def test_signup_and_unregister_flow():
    activity = "Chess Club"
    email = "test_user@example.com"

    # make sure test email is not present
    assert email not in activities[activity]["participants"]

    # sign up
    res = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert res.status_code == 200
    assert "Signed up" in res.json().get("message", "")
    assert email in activities[activity]["participants"]

    # duplicate sign up should fail
    res_dup = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert res_dup.status_code == 400

    # unregister
    res_un = client.delete(f"/activities/{activity}/unregister", params={"email": email})
    assert res_un.status_code == 200
    assert email not in activities[activity]["participants"]


def test_unregister_nonexistent_participant():
    activity = "Chess Club"
    email = "ghost@example.com"

    # ensure not present
    if email in activities[activity]["participants"]:
        activities[activity]["participants"].remove(email)

    res = client.delete(f"/activities/{activity}/unregister", params={"email": email})
    assert res.status_code == 404


def test_activity_not_found():
    email = "x@example.com"
    # signup to nonexistent
    res_signup = client.post("/activities/NoSuchActivity/signup", params={"email": email})
    assert res_signup.status_code == 404

    # unregister from nonexistent
    res_un = client.delete("/activities/NoSuchActivity/unregister", params={"email": email})
    assert res_un.status_code == 404
