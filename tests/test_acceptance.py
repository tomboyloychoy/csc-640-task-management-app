import sqlite3
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from code.app.main import SECRET_KEY, create_app


def _register(client, username):
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "Secret123!", "display_name": username.title()},
    )
    assert response.status_code == 201
    return response.json()


def _login(client, username, password="Secret123!"):
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token
    return {"Authorization": f"Bearer {token}"}


def _expired_headers(user_id):
    token = jwt.encode(
        {"sub": str(user_id), "exp": datetime.now(timezone.utc) - timedelta(minutes=5)},
        SECRET_KEY,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def _assert_detail(response, status_code):
    assert response.status_code == status_code
    assert isinstance(response.json().get("detail"), str)
    assert response.json()["detail"].strip()


def _create_task(client, headers, **values):
    response = client.post(
        "/api/tasks",
        headers=headers,
        json={"title": "Finish quality report", **values},
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def api(tmp_path):
    with TestClient(create_app(tmp_path / "acceptance.db")) as client:
        yield client


def test_acceptance_list_tasks_filters_empty_invalid_auth_and_isolation(api):
    alice = _register(api, "alice")
    alice_headers = _login(api, "alice")
    active = _create_task(
        api,
        alice_headers,
        description="Review quality results",
        tag="Research",
    )
    completed = _create_task(api, alice_headers, title="Completed task", tag="Work")
    update = api.put(
        f"/api/tasks/{completed['id']}",
        headers=alice_headers,
        json={**completed, "completed": True},
    )
    assert update.status_code == 200
    assert update.json()["completed"] is True

    listed = api.get("/api/tasks", headers=alice_headers)
    assert listed.status_code == 200
    assert {task["id"] for task in listed.json()} == {active["id"], completed["id"]}
    assert all({"id", "title", "tag", "completed"} <= task.keys() for task in listed.json())
    filtered = api.get(
        "/api/tasks",
        headers=alice_headers,
        params={"status_filter": "active", "tag": "research", "q": "quality"},
    )
    assert filtered.status_code == 200
    assert [task["id"] for task in filtered.json()] == [active["id"]]
    empty = api.get("/api/tasks", headers=alice_headers, params={"q": "no matching task"})
    assert empty.status_code == 200
    assert empty.json() == []
    _assert_detail(
        api.get("/api/tasks", headers=alice_headers, params={"status_filter": "unknown"}),
        422,
    )

    _assert_detail(api.get("/api/tasks"), 401)
    _assert_detail(api.get("/api/tasks", headers={"Authorization": "Bearer malformed"}), 401)
    _assert_detail(api.get("/api/tasks", headers=_expired_headers(alice["id"])), 401)

    _register(api, "bob")
    bob_tasks = api.get("/api/tasks", headers=_login(api, "bob"))
    assert bob_tasks.status_code == 200
    assert bob_tasks.json() == []


@pytest.mark.parametrize(
    "invalid_task",
    [
        {"title": " "},
        {"title": "Valid title", "due_date": "2026-99-99"},
        {"title": "Valid title", "priority": "urgent"},
    ],
)
def test_acceptance_create_task_validation_and_auth(api, invalid_task):
    user = _register(api, "creator")
    headers = _login(api, "creator")
    bad = api.post("/api/tasks", headers=headers, json=invalid_task)
    _assert_detail(bad, 422)
    assert api.get("/api/tasks", headers=headers).json() == []

    valid_payload = {
        "title": "Finish quality report",
        "description": "Review results",
        "tag": "Research",
        "due_date": "2026-11-12",
        "priority": "high",
    }
    created = api.post("/api/tasks", headers=headers, json=valid_payload)
    assert created.status_code == 201
    task = created.json()
    assert {key: task[key] for key in valid_payload} == valid_payload
    assert task["id"] and task["completed"] is False
    assert task["user_id"] == user["id"]

    _assert_detail(api.post("/api/tasks", json=valid_payload), 401)
    _assert_detail(
        api.post("/api/tasks", headers={"Authorization": "Bearer malformed"}, json=valid_payload),
        401,
    )
    _assert_detail(
        api.post("/api/tasks", headers=_expired_headers(user["id"]), json=valid_payload),
        401,
    )
    assert len(api.get("/api/tasks", headers=headers).json()) == 1


def test_acceptance_update_task_validation_ownership_and_auth(api):
    alice = _register(api, "alice")
    bob = _register(api, "bob")
    alice_headers = _login(api, "alice")
    bob_headers = _login(api, "bob")
    task = _create_task(api, alice_headers, description="Original")

    updated = api.put(
        f"/api/tasks/{task['id']}",
        headers=alice_headers,
        json={**task, "title": "Submit quality report", "completed": True},
    )
    assert updated.status_code == 200
    assert updated.json()["id"] == task["id"]
    assert updated.json()["title"] == "Submit quality report"
    assert updated.json()["completed"] is True

    for invalid in (
        {**updated.json(), "title": " "},
        {**updated.json(), "priority": "urgent"},
    ):
        _assert_detail(api.put(f"/api/tasks/{task['id']}", headers=alice_headers, json=invalid), 422)
        unchanged = api.get("/api/tasks", headers=alice_headers).json()[0]
        assert unchanged == updated.json()

    _assert_detail(api.put("/api/tasks/99999", headers=alice_headers, json=task), 404)
    _assert_detail(api.put(f"/api/tasks/{task['id']}", headers=bob_headers, json=task), 404)
    assert api.get("/api/tasks", headers=alice_headers).json()[0] == updated.json()
    _assert_detail(api.put(f"/api/tasks/{task['id']}", json=task), 401)
    _assert_detail(
        api.put(
            f"/api/tasks/{task['id']}",
            headers={"Authorization": "Bearer malformed"},
            json=task,
        ),
        401,
    )
    _assert_detail(
        api.put(f"/api/tasks/{task['id']}", headers=_expired_headers(alice["id"]), json=task),
        401,
    )


def test_acceptance_delete_task_success_missing_other_user_and_auth(api):
    alice = _register(api, "alice")
    _register(api, "bob")
    alice_headers = _login(api, "alice")
    bob_headers = _login(api, "bob")
    task = _create_task(api, alice_headers)

    _assert_detail(api.delete("/api/tasks/99999", headers=alice_headers), 404)
    _assert_detail(api.delete(f"/api/tasks/{task['id']}", headers=bob_headers), 404)
    assert api.get("/api/tasks", headers=alice_headers).json()[0]["id"] == task["id"]

    _assert_detail(api.delete(f"/api/tasks/{task['id']}"), 401)
    _assert_detail(
        api.delete(
            f"/api/tasks/{task['id']}",
            headers={"Authorization": "Bearer malformed"},
        ),
        401,
    )
    _assert_detail(
        api.delete(f"/api/tasks/{task['id']}", headers=_expired_headers(alice["id"])),
        401,
    )
    deleted = api.delete(f"/api/tasks/{task['id']}", headers=alice_headers)
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert api.get("/api/tasks", headers=alice_headers).json() == []


def test_acceptance_tags_include_defaults_and_remove_unused_custom_tag(api):
    user = _register(api, "taguser")
    headers = _login(api, "taguser")
    task = _create_task(api, headers, tag="Research")
    tags = api.get("/api/tags", headers=headers)
    assert tags.status_code == 200
    assert set(("School", "Work", "House", "Personal", "Other", "Research")) <= set(tags.json())

    deleted = api.delete(f"/api/tasks/{task['id']}", headers=headers)
    assert deleted.status_code == 204
    after_delete = api.get("/api/tags", headers=headers)
    assert after_delete.status_code == 200
    assert "Research" not in after_delete.json()

    _assert_detail(api.get("/api/tags"), 401)
    _assert_detail(api.get("/api/tags", headers={"Authorization": "Bearer malformed"}), 401)
    _assert_detail(api.get("/api/tags", headers=_expired_headers(user["id"])), 401)


def test_acceptance_registration_validation_duplicate_and_safe_response(api, tmp_path):
    response = api.post(
        "/api/auth/register",
        json={"username": "register_user", "password": "Secret123!", "display_name": "Register"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["username"] == "register_user"
    assert body["display_name"] == "Register"
    assert "password" not in body and "password_hash" not in body

    for payload in (
        {"username": "invalid-name", "password": "Secret123!"},
        {"username": "another_user"},
        {"username": "another_user", "password": " "},
    ):
        _assert_detail(api.post("/api/auth/register", json=payload), 422)

    duplicate = api.post(
        "/api/auth/register",
        json={"username": "REGISTER_USER", "password": "Secret123!", "display_name": "Duplicate"},
    )
    _assert_detail(duplicate, 409)
    with sqlite3.connect(tmp_path / "acceptance.db") as connection:
        user_count = connection.execute(
            "SELECT COUNT(*) FROM users WHERE username = ? COLLATE NOCASE",
            ("register_user",),
        ).fetchone()[0]
    assert user_count == 1


def test_acceptance_login_valid_invalid_and_missing_credentials(api):
    _register(api, "loginuser")
    logged_in = api.post(
        "/api/auth/login",
        json={"username": "loginuser", "password": "Secret123!"},
    )
    assert logged_in.status_code == 200
    token = logged_in.json()["access_token"]
    assert token
    assert logged_in.json()["token_type"].lower() == "bearer"
    profile = api.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["username"] == "loginuser"
    assert "password" not in profile.json() and "password_hash" not in profile.json()

    _assert_detail(
        api.post("/api/auth/login", json={"username": "loginuser", "password": "Incorrect123!"}),
        401,
    )
    _assert_detail(
        api.post("/api/auth/login", json={"username": "missinguser", "password": "Secret123!"}),
        401,
    )
    _assert_detail(api.post("/api/auth/login", json={"password": "Secret123!"}), 422)
    _assert_detail(api.post("/api/auth/login", json={"username": "loginuser"}), 422)


def test_acceptance_profile_read_and_update_validation_and_auth(api):
    user = _register(api, "profileuser")
    headers = _login(api, "profileuser")
    profile = api.get("/api/users/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["id"] == user["id"]
    assert profile.json()["username"] == "profileuser"
    assert profile.json()["display_name"] == "Profileuser"
    assert "password" not in profile.json() and "password_hash" not in profile.json()

    _assert_detail(api.get("/api/users/me"), 401)
    _assert_detail(api.get("/api/users/me", headers={"Authorization": "Bearer malformed"}), 401)
    _assert_detail(api.get("/api/users/me", headers=_expired_headers(user["id"])), 401)

    for payload in ({"display_name": " "}, {"display_name": 5}):
        _assert_detail(api.patch("/api/users/me", headers=headers, json=payload), 422)
        unchanged = api.get("/api/users/me", headers=headers).json()
        assert unchanged["display_name"] == "Profileuser"

    patched = api.patch("/api/users/me", headers=headers, json={"display_name": "A Updated"})
    assert patched.status_code == 200
    assert patched.json()["display_name"] == "A Updated"
    assert patched.json()["id"] == user["id"]
    assert patched.json()["username"] == "profileuser"
    assert api.get("/api/users/me", headers=headers).json() == patched.json()
    _assert_detail(api.patch("/api/users/me", json={"display_name": "Valid"}), 401)
    _assert_detail(
        api.patch(
            "/api/users/me",
            headers={"Authorization": "Bearer malformed"},
            json={"display_name": "Valid"},
        ),
        401,
    )
    _assert_detail(
        api.patch(
            "/api/users/me",
            headers=_expired_headers(user["id"]),
            json={"display_name": "Valid"},
        ),
        401,
    )
    assert api.get("/api/users/me", headers=headers).json()["display_name"] == "A Updated"


def test_acceptance_admin_users_requires_admin_and_redacts_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("TAMANA_ADMIN_USERNAME", "testadmin")
    monkeypatch.setenv("TAMANA_ADMIN_PASSWORD", "AdminSecret123!")
    with TestClient(create_app(tmp_path / "admin-acceptance.db")) as client:
        regular = _register(client, "regular")
        admin_headers = _login(client, "testadmin", "AdminSecret123!")
        users = client.get("/api/admin/users", headers=admin_headers)
        assert users.status_code == 200
        assert any(
            item["id"] == regular["id"] and item["username"] == "regular"
            for item in users.json()
        )
        assert all("password" not in item and "password_hash" not in item for item in users.json())

        _assert_detail(client.get("/api/admin/users"), 401)
        _assert_detail(
            client.get("/api/admin/users", headers={"Authorization": "Bearer malformed"}),
            401,
        )
        _assert_detail(
            client.get("/api/admin/users", headers=_expired_headers(regular["id"])),
            401,
        )
        _assert_detail(client.get("/api/admin/users", headers=_login(client, "regular")), 403)
