from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app, reset_activities


@pytest.fixture(autouse=True)
def reset_activity_state():
    reset_activities()
    yield
    reset_activities()


@pytest.fixture
def client():
    return TestClient(app)


def activity_path(activity_name: str) -> str:
    return quote(activity_name, safe="")


def test_root_redirects_to_static_index(client: TestClient):
    # Arrange

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_seeded_data(client: TestClient):
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200

    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_trimmed_email_to_activity(client: TestClient):
    # Arrange
    email = "  newstudent@mergington.edu  "
    signup_url = f"/activities/{activity_path('Chess Club')}/signup"

    # Act
    response = client.post(
        signup_url,
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up newstudent@mergington.edu for Chess Club"
    }
    assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_email_case_insensitively(client: TestClient):
    # Arrange
    email = "  Emma@Mergington.edu "
    signup_url = f"/activities/{activity_path('Programming Class')}/signup"

    # Act
    response = client.post(
        signup_url,
        params={"email": email},
    )

    # Assert
    assert response.status_code == 409
    assert response.json() == {"detail": "Participant is already registered"}


def test_signup_returns_404_for_unknown_activity(client: TestClient):
    # Arrange
    signup_url = f"/activities/{activity_path('Robotics Club')}/signup"

    # Act
    response = client.post(
        signup_url,
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_existing_participant(client: TestClient):
    # Arrange
    participant_email = "james@mergington.edu"
    unregister_url = f"/activities/{activity_path('Basketball Team')}/participants"

    # Act
    response = client.delete(
        unregister_url,
        params={"email": participant_email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": "Removed james@mergington.edu from Basketball Team"
    }
    assert "james@mergington.edu" not in activities["Basketball Team"]["participants"]


def test_unregister_returns_404_for_unknown_activity(client: TestClient):
    # Arrange
    unregister_url = f"/activities/{activity_path('Robotics Club')}/participants"

    # Act
    response = client.delete(
        unregister_url,
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_404_for_missing_participant(client: TestClient):
    # Arrange
    unregister_url = f"/activities/{activity_path('Chess Club')}/participants"

    # Act
    response = client.delete(
        unregister_url,
        params={"email": "student@mergington.edu"},
    )

     # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found"}