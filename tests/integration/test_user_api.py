"""Integration tests for user registration and login."""

from app.models.user import User


def sample_user():
    """Provide valid registration data."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.integration@example.com",
        "username": "johnintegration",
        "password": "SecurePass123",
    }


def test_register_user_success(client, db_session):
    """Registration saves a user with a hashed password."""

    payload = sample_user()

    response = client.post(
        "/users/register",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert "password" not in data
    assert "password_hash" not in data

    stored_user = db_session.query(User).filter_by(
        username=payload["username"]
    ).one()

    assert stored_user.password_hash != payload["password"]
    assert stored_user.verify_password(payload["password"])


def test_login_user_success(client, db_session):
    """Correct credentials return a valid JWT."""

    payload = sample_user()

    registration = client.post(
        "/users/register",
        json=payload,
    )
    assert registration.status_code == 201

    response = client.post(
        "/users/login",
        json={
            "username": payload["username"],
            "password": payload["password"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["username"] == payload["username"]

    # Verify the actual JWT against the existing User model.
    token_user_id = User.verify_token(data["access_token"])

    assert str(token_user_id) == data["user"]["id"]

    stored_user = db_session.query(User).filter_by(
        username=payload["username"]
    ).one()

    db_session.refresh(stored_user)
    assert stored_user.last_login is not None


def test_login_wrong_password(client):
    """Incorrect passwords are rejected."""

    payload = sample_user()
    client.post("/users/register", json=payload)

    response = client.post(
        "/users/login",
        json={
            "username": payload["username"],
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401
    assert "error" in response.json()


def test_duplicate_registration(client):
    """A duplicate username/email returns 409."""

    payload = sample_user()

    first = client.post("/users/register", json=payload)
    second = client.post("/users/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_invalid_registration(client):
    """Weak passwords are rejected by Pydantic."""

    payload = sample_user()
    payload["password"] = "weak"

    response = client.post(
        "/users/register",
        json=payload,
    )

    assert response.status_code == 400
    assert "error" in response.json()


def test_login_nonexistent_user(client):
    """An unknown user cannot log in."""

    response = client.post(
        "/users/login",
        json={
            "username": "unknownuser",
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401


def test_login_with_email(client):
    """The existing User.authenticate accepts email or username."""

    payload = sample_user()

    registration = client.post(
        "/users/register",
        json=payload,
    )
    assert registration.status_code == 201

    response = client.post(
        "/users/login",
        json={
            "username": payload["email"],
            "password": payload["password"],
        },
    )

    assert response.status_code == 200
    assert response.json()["user"]["email"] == payload["email"]
