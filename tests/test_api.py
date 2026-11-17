import sqlite3
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi.testclient import TestClient

from app.main import create_app


def _token(client, email, password):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_auth_and_task_lifecycle(tmp_path):
    db_path = tmp_path / "test.db"
    app = create_app(db_path)
    with TestClient(app) as client:
        register = client.post(
            "/api/auth/register",
            json={"email": "alice@example.com", "password": "secret123", "display_name": "Alice"},
        )
        assert register.status_code == 201
        user = register.json()
        assert user["email"] == "alice@example.com"
        assert "password" not in user
        assert user["display_name"] == "Alice"

        token = _token(client, "alice@example.com", "secret123")
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/api/users/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["email"] == "alice@example.com"

        task = client.post(
            "/api/tasks",
            headers=headers,
            json={
                "title": "Finish the quality report",
                "description": "Review the test results",
                "tag": "Research",
                "due_date": "2026-11-12",
                "priority": "high",
            },
        )
        assert task.status_code == 201
        created = task.json()
        assert created["completed"] is False
        assert created["tag"] == "Research"
        assert created["user_id"] == me.json()["id"]

        assert "Research" in client.get("/api/tags", headers=headers).json()
        assert client.get("/api/tasks", headers=headers, params={"tag": "research"}).json()[0]["id"] == created["id"]
        assert client.get("/api/tasks", headers=headers, params={"q": "quality"}).json()[0]["id"] == created["id"]

        updated = client.put(
            f"/api/tasks/{created['id']}",
            headers=headers,
            json={**created, "title": "Submit the quality report", "completed": True},
        )
        assert updated.status_code == 200
        assert updated.json()["completed"] is True
        assert client.get("/api/tasks", headers=headers, params={"status_filter": "active"}).json() == []
        assert len(client.get("/api/tasks", headers=headers, params={"status_filter": "completed"}).json()) == 1

        patched = client.patch("/api/users/me", headers=headers, json={"display_name": "Alice Updated"})
        assert patched.status_code == 200
        assert patched.json()["display_name"] == "Alice Updated"

        assert client.delete(f"/api/tasks/{created['id']}", headers=headers).status_code == 204
        assert client.delete(f"/api/tasks/{created['id']}", headers=headers).status_code == 404


def test_authentication_and_admin_controls(tmp_path):
    db_path = tmp_path / "test.db"
    app = create_app(db_path)
    with TestClient(app) as client:
        client.post("/api/auth/register", json={"email": "alice@example.com", "password": "secret123", "display_name": "Alice"})
        client.post("/api/auth/register", json={"email": "bob@example.com", "password": "secret123", "display_name": "Bob"})

        alice_token = _token(client, "alice@example.com", "secret123")
        bob_token = _token(client, "bob@example.com", "secret123")
        alice_headers = {"Authorization": f"Bearer {alice_token}"}
        bob_headers = {"Authorization": f"Bearer {bob_token}"}

        assert client.get("/api/tasks", headers=alice_headers).status_code == 200
        assert client.get("/api/tasks", headers={}).status_code == 401
        assert client.get("/api/tasks", headers={"Authorization": "Bearer not-a-valid-token"}).status_code == 401

        with sqlite3.connect(db_path) as connection:
            connection.execute(
                "INSERT INTO users (email, password_hash, display_name, is_admin, created_at) VALUES (?, ?, ?, 1, ?)",
                (
                    "admin@example.com",
                    bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8"),
                    "Administrator",
                    "2026-11-15T00:00:00+00:00",
                ),
            )
            connection.commit()

        admin_token = _token(client, "admin@example.com", "admin123")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        assert client.get("/api/admin/users", headers=admin_headers).status_code == 200
        assert client.get("/api/admin/users", headers=alice_headers).status_code == 403

        user_list = client.get("/api/admin/users", headers=admin_headers).json()
        assert any(entry["email"] == "alice@example.com" for entry in user_list)
        assert all("password" not in entry for entry in user_list)


def test_invalid_inputs_are_rejected(tmp_path):
    app = create_app(tmp_path / "test.db")
    with TestClient(app) as client:
        assert client.post("/api/auth/register", json={"email": "bad-email", "password": "secret123"}).status_code == 422
        assert client.post("/api/auth/register", json={"email": "valid@example.com", "password": "short"}).status_code == 422

        register = client.post("/api/auth/register", json={"email": "first@example.com", "password": "secret123", "display_name": "First"})
        assert register.status_code == 201
        duplicate = client.post("/api/auth/register", json={"email": "first@example.com", "password": "secret123", "display_name": "First"})
        assert duplicate.status_code == 409

        login = client.post("/api/auth/login", json={"email": "first@example.com", "password": "wrongpass"})
        assert login.status_code == 401

        token = _token(client, "first@example.com", "secret123")
        headers = {"Authorization": f"Bearer {token}"}
        invalid_patch = client.patch("/api/users/me", headers=headers, json={"display_name": " "})
        assert invalid_patch.status_code == 422


def test_expired_tokens_and_user_isolation(tmp_path):
    app = create_app(tmp_path / "test.db")
    with TestClient(app) as client:
        client.post(
            "/api/auth/register",
            json={"email": "alice@example.com", "password": "secret123", "display_name": "Alice"},
        )
        client.post(
            "/api/auth/register",
            json={"email": "bob@example.com", "password": "secret123", "display_name": "Bob"},
        )

        expired_token = jwt.encode(
            {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=5)},
            "tamana-dev-secret-key",
            algorithm="HS256",
        )
        expired_headers = {"Authorization": f"Bearer {expired_token}"}

        assert client.get("/api/tasks", headers=expired_headers).status_code == 401
        assert client.get("/api/users/me", headers=expired_headers).status_code == 401
        assert client.post(
            "/api/tasks",
            headers=expired_headers,
            json={"title": "Should not create", "tag": "Work", "priority": "normal"},
        ).status_code == 401

        alice_token = _token(client, "alice@example.com", "secret123")
        bob_token = _token(client, "bob@example.com", "secret123")
        alice_headers = {"Authorization": f"Bearer {alice_token}"}
        bob_headers = {"Authorization": f"Bearer {bob_token}"}

        created = client.post(
            "/api/tasks",
            headers=alice_headers,
            json={
                "title": "Finish the quality report",
                "description": "Review the test results",
                "tag": "Research",
                "due_date": "2026-11-12",
                "priority": "high",
            },
        )
        assert created.status_code == 201
        task_id = created.json()["id"]

        assert client.get("/api/tasks", headers=bob_headers).json() == []
        assert client.put(
            f"/api/tasks/{task_id}",
            headers=bob_headers,
            json={"title": "Hacked task", "description": "Nope", "tag": "Other", "priority": "low"},
        ).status_code == 404
        assert client.delete(f"/api/tasks/{task_id}", headers=bob_headers).status_code == 404

        alice_after = client.get("/api/tasks", headers=alice_headers).json()
        assert len(alice_after) == 1
        assert alice_after[0]["id"] == task_id
