"""Вход в кабинет, проверка токена и ролей."""
from datetime import timedelta

import pytest

from core.models import UserRole

from .conftest import API, PASSWORD, Factory


def login(client, username, password=PASSWORD):
    return client.post(f"{API}/auth/login", json={"username": username, "password": password})


def test_login_returns_token_and_profile(client, student):
    response = login(client, "student1")

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 1800
    assert body["user"]["username"] == "student1"
    assert body["user"]["full_name"] == "Иванов Иван Иванович"
    assert body["user"]["group_id"] is None
    assert "hashed_password" not in body["user"]

    me = client.get(f"{API}/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["id"] == student.id


def test_wrong_password_and_unknown_user_give_same_error(client, student):
    wrong_password = login(client, "student1", "not-my-password")
    unknown_user = login(client, "nobody")

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json() == {"detail": "Неверный логин или пароль"}


def test_blocked_student_cannot_login(client, factory):
    factory.user(username="blocked", is_active=False)

    response = login(client, "blocked")

    assert response.status_code == 403
    assert response.json() == {"detail": "Учётная запись заблокирована"}


def test_teacher_cannot_login_to_student_portal(client, factory):
    factory.user(UserRole.TEACHER, username="teacher1")

    response = login(client, "teacher1")

    assert response.status_code == 403
    assert response.json() == {"detail": "Вход в кабинет доступен только студентам"}


def test_login_without_password_returns_422(client):
    response = client.post(f"{API}/auth/login", json={"username": "student1"})
    assert response.status_code == 422


@pytest.mark.parametrize("path", [
    "/me", "/dashboard", "/courses", "/schedule", "/grades", "/attendance",
    "/announcements", "/certificates", "/submissions", "/staff/certificates",
])
def test_endpoints_require_token(client, path):
    response = client.get(f"{API}{path}")

    assert response.status_code == 401
    assert response.json() == {"detail": "Требуется авторизация"}


def test_invalid_token_is_rejected(client, student):
    response = client.get(f"{API}/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401


def test_expired_token_is_rejected(client, student):
    headers = Factory.headers(student, expires_delta=timedelta(seconds=-1))
    assert client.get(f"{API}/me", headers=headers).status_code == 401


def test_token_of_blocked_user_is_rejected(client, db, student, auth):
    student.is_active = False
    db.commit()

    assert client.get(f"{API}/me", headers=auth).status_code == 401


def test_teacher_token_on_student_endpoint_is_forbidden(client, teacher):
    response = client.get(f"{API}/grades", headers=Factory.headers(teacher))

    assert response.status_code == 403
    assert response.json() == {"detail": "Доступ только для студентов"}


def test_student_token_on_staff_endpoint_is_forbidden(client, auth):
    response = client.get(f"{API}/staff/certificates", headers=auth)

    assert response.status_code == 403
    assert response.json() == {"detail": "Недостаточно прав"}
