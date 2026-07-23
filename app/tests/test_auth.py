from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User

from .conftest import auth_headers


def test_register_requires_authentication(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "new-user@example.com",
            "password": "Str0ngPass!23",
            "full_name": "New User",
            "role": "VIEWER",
        },
    )

    assert response.status_code == 401
    assert response.json()["error_code"] == "UNAUTHORIZED"


def test_register_requires_admin_role(client, analyst_user):
    response = client.post(
        "/auth/register",
        json={
            "email": "new-user@example.com",
            "password": "Str0ngPass!23",
            "full_name": "New User",
            "role": "VIEWER",
        },
        headers=auth_headers(analyst_user),
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"


def test_register_creates_user_as_admin(client, admin_user):
    response = client.post(
        "/auth/register",
        json={
            "email": "new-user@example.com",
            "password": "Str0ngPass!23",
            "full_name": "New User",
            "role": "VIEWER",
        },
        headers=auth_headers(admin_user),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new-user@example.com"
    assert body["full_name"] == "New User"
    assert body["role"] == "VIEWER"
    assert body["is_active"] is True


def test_register_rejects_duplicate_email(client, admin_user):
    payload = {
        "email": "duplicate@example.com",
        "password": "Str0ngPass!23",
        "full_name": "Duplicate User",
        "role": "VIEWER",
    }
    first = client.post("/auth/register", json=payload, headers=auth_headers(admin_user))
    assert first.status_code == 201

    second = client.post("/auth/register", json=payload, headers=auth_headers(admin_user))
    assert second.status_code == 409
    assert second.json()["error_code"] == "EMAIL_ALREADY_REGISTERED"


def test_register_rejects_weak_password(client, admin_user):
    response = client.post(
        "/auth/register",
        json={
            "email": "weak-password@example.com",
            "password": "weak",
            "full_name": "Weak Password",
            "role": "VIEWER",
        },
        headers=auth_headers(admin_user),
    )

    assert response.status_code == 422


def test_login_succeeds_with_correct_credentials(client, db_session):
    user = User(
        email="login-success@example.com",
        password_hash=hash_password("Str0ngPass!23"),
        full_name="Login Success",
        role=UserRole.VIEWER,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/auth/login", json={"email": "login-success@example.com", "password": "Str0ngPass!23"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]
    assert body["expires_in"] > 0


def test_login_rejects_wrong_password(client, db_session):
    user = User(
        email="login-wrong-password@example.com",
        password_hash=hash_password("Str0ngPass!23"),
        full_name="Login Wrong Password",
        role=UserRole.VIEWER,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/auth/login",
        json={"email": "login-wrong-password@example.com", "password": "WrongPass!23"},
    )

    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_CREDENTIALS"


def test_login_rejects_unknown_email(client):
    response = client.post(
        "/auth/login", json={"email": "does-not-exist@example.com", "password": "Str0ngPass!23"}
    )

    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_CREDENTIALS"


def test_login_rejects_inactive_user(client, db_session):
    user = User(
        email="inactive@example.com",
        password_hash=hash_password("Str0ngPass!23"),
        full_name="Inactive User",
        role=UserRole.VIEWER,
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/auth/login", json={"email": "inactive@example.com", "password": "Str0ngPass!23"}
    )

    assert response.status_code == 401
    assert response.json()["error_code"] == "INACTIVE_USER"


def test_protected_endpoint_rejects_missing_token(client):
    response = client.get("/domains")

    assert response.status_code == 401
    assert response.json()["error_code"] == "UNAUTHORIZED"


def test_protected_endpoint_rejects_invalid_token(client):
    response = client.get("/domains", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_TOKEN"
