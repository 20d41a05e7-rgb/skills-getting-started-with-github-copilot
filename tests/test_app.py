import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def reset_activities():
    # snapshot participants before the test and restore afterwards to keep tests isolated
    original = {k: v["participants"][:] for k, v in activities.items()}
    yield
    for name, participants in original.items():
        activities[name]["participants"] = participants[:]


def test_get_activities(client):
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_and_unregister_flow(client):
    activity = "Chess Club"
    test_email = "tester@mergington.edu"

    # Ensure the test email is not registered yet
    assert test_email not in activities[activity]["participants"]

    # Sign up
    resp = client.post(f"/activities/{activity}/signup?email={test_email}")
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")
    assert test_email in activities[activity]["participants"]

    # Duplicate signup should be rejected
    resp_dup = client.post(f"/activities/{activity}/signup?email={test_email}")
    assert resp_dup.status_code == 400

    # Unregister the participant
    resp_unreg = client.delete(f"/activities/{activity}/unregister?email={test_email}")
    assert resp_unreg.status_code == 200
    assert test_email not in activities[activity]["participants"]

    # Trying to unregister again should fail
    resp_unreg2 = client.delete(f"/activities/{activity}/unregister?email={test_email}")
    assert resp_unreg2.status_code == 400


def test_activity_not_found(client):
    resp = client.post("/activities/Nonexistent/signup?email=foo@bar.com")
    assert resp.status_code == 404
