from fastapi.testclient import TestClient

from app.main import create_app


def test_task_lifecycle_and_custom_tags(tmp_path):
    app = create_app(tmp_path / "test.db")
    with TestClient(app) as client:
        created = client.post(
            "/api/tasks",
            json={
                "title": "Finish the quality report",
                "description": "Review the test results",
                "tag": "Research",
                "due_date": "2026-11-12",
                "priority": "high",
            },
        )
        assert created.status_code == 201
        task = created.json()
        assert task["completed"] is False
        assert task["tag"] == "Research"

        assert "Research" in client.get("/api/tags").json()
        assert client.get("/api/tasks", params={"tag": "research"}).json()[0]["id"] == task["id"]
        assert client.get("/api/tasks", params={"q": "quality"}).json()[0]["id"] == task["id"]

        updated = client.put(
            f"/api/tasks/{task['id']}",
            json={**task, "title": "Submit the quality report", "completed": True},
        )
        assert updated.status_code == 200
        assert updated.json()["completed"] is True
        assert client.get("/api/tasks", params={"status_filter": "active"}).json() == []
        assert len(client.get("/api/tasks", params={"status_filter": "completed"}).json()) == 1

        assert client.delete(f"/api/tasks/{task['id']}").status_code == 204
        assert client.delete(f"/api/tasks/{task['id']}").status_code == 404


def test_task_validation_and_parameterized_search(tmp_path):
    app = create_app(tmp_path / "test.db")
    with TestClient(app) as client:
        assert client.post("/api/tasks", json={"title": "  "}).status_code == 422
        assert client.post("/api/tasks", json={"title": "Bad date", "due_date": "tomorrow"}).status_code == 422

        task = client.post("/api/tasks", json={"title": "50%_complete"}).json()
        assert client.get("/api/tasks", params={"q": "%_"}).json() == [task]
        assert client.get("/api/tasks", params={"status_filter": "unknown"}).status_code == 422
