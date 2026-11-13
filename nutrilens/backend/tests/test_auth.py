import pytest
from fastapi.testclient import TestClient
from app.core.security import verify_password, get_password_hash


def test_password_hashing():
    raw_pwd = "SuperSecretPassword123!"
    hashed = get_password_hash(raw_pwd)

    assert hashed != raw_pwd
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_register_user_success(client: TestClient):
    payload = {
        "email": "sarah.connor@example.com",
        "password": "SecurePassword123!",
        "full_name": "Sarah Connor",
        "age": 29,
        "dietary_preference": "Vegetarian",
        "allergies": ["Peanuts", "Tree Nuts"],
        "dietary_restrictions": ["Low-Sodium"],
        "nutrition_goals": ["Heart Health", "Clean Eating"],
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "sarah.connor@example.com"
    assert data["user"]["full_name"] == "Sarah Connor"
    assert data["user"]["age"] == 29
    assert data["user"]["profile"]["dietary_preference"] == "Vegetarian"
    assert "Peanuts" in data["user"]["profile"]["allergies"]
    assert "Low-Sodium" in data["user"]["profile"]["dietary_restrictions"]
    assert "Heart Health" in data["user"]["profile"]["nutrition_goals"]


def test_register_duplicate_email(client: TestClient):
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "Original User",
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with exact same email should fail
    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_register_validation_error(client: TestClient):
    # Missing required password and invalid email
    payload = {
        "email": "not-an-email",
        "full_name": "",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422


def test_login_success(client: TestClient):
    register_payload = {
        "email": "login.test@example.com",
        "password": "MySecretPassword99!",
        "full_name": "Login Tester",
    }
    client.post("/api/auth/register", json=register_payload)

    login_payload = {
        "email": "login.test@example.com",
        "password": "MySecretPassword99!",
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login.test@example.com"


def test_login_invalid_password(client: TestClient):
    register_payload = {
        "email": "wrongpwd@example.com",
        "password": "CorrectPassword123!",
        "full_name": "Test User",
    }
    client.post("/api/auth/register", json=register_payload)

    response = client.post(
        "/api/auth/login",
        json={"email": "wrongpwd@example.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    response = client.post(
        "/api/auth/login",
        json={"email": "ghost@example.com", "password": "AnyPassword123!"},
    )
    assert response.status_code == 401


def test_get_current_user_me(client: TestClient):
    reg = client.post(
        "/api/auth/register",
        json={
            "email": "current.me@example.com",
            "password": "Password123!",
            "full_name": "Current User",
            "dietary_preference": "Vegan",
        },
    )
    token = reg.json()["access_token"]

    # Call with Bearer header
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == "current.me@example.com"
    assert user_data["full_name"] == "Current User"
    assert user_data["profile"]["dietary_preference"] == "Vegan"


def test_get_current_user_unauthorized(client: TestClient):
    # No token provided
    res1 = client.get("/api/auth/me")
    assert res1.status_code == 401

    # Invalid token provided
    res2 = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert res2.status_code == 401


def test_update_user_profile(client: TestClient):
    reg = client.post(
        "/api/auth/register",
        json={
            "email": "update.profile@example.com",
            "password": "Password123!",
            "full_name": "Initial Name",
            "age": 25,
            "dietary_preference": "Omnivore",
            "allergies": [],
            "dietary_restrictions": [],
            "nutrition_goals": [],
        },
    )
    token = reg.json()["access_token"]

    # Update profile fields via PUT /api/auth/profile
    update_payload = {
        "full_name": "Updated Name",
        "age": 26,
        "dietary_preference": "Pescatarian",
        "allergies": ["Shellfish", "Dairy"],
        "dietary_restrictions": ["Low-Sugar"],
        "nutrition_goals": ["High Protein", "Weight Loss"],
    }
    update_res = client.put(
        "/api/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json=update_payload,
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["full_name"] == "Updated Name"
    assert updated_data["age"] == 26
    assert updated_data["profile"]["dietary_preference"] == "Pescatarian"
    assert "Shellfish" in updated_data["profile"]["allergies"]
    assert "Low-Sugar" in updated_data["profile"]["dietary_restrictions"]
    assert "High Protein" in updated_data["profile"]["nutrition_goals"]

    # Verify persistent state via GET /api/auth/me
    me_res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["profile"]["dietary_preference"] == "Pescatarian"


def test_logout(client: TestClient):
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert "Successfully logged out" in response.json()["message"]


def test_versioned_auth_endpoints(client: TestClient):
    # Verify /api/v1/auth/register works identically
    payload = {
        "email": "v1.user@example.com",
        "password": "Password123!",
        "full_name": "V1 User",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    token = res.json()["access_token"]

    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "v1.user@example.com"
