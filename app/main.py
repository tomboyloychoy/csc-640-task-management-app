from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager, closing
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DEFAULT_TAGS = ("School", "Work", "House", "Personal", "Other")
PRIORITIES = {"low", "normal", "high"}


def create_app(database_path: Path | str | None = None) -> FastAPI:
    db_path = Path(database_path) if database_path else ROOT_DIR / "data" / "tamana.db"

    def connect() -> sqlite3.Connection:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize_database() -> None:
        with closing(connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    tag TEXT NOT NULL DEFAULT 'Personal',
                    due_date TEXT,
                    priority TEXT NOT NULL DEFAULT 'normal'
                        CHECK (priority IN ('low', 'normal', 'high')),
                    completed INTEGER NOT NULL DEFAULT 0
                        CHECK (completed IN (0, 1)),
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        initialize_database()
        yield

    application = FastAPI(title="Tamana", version="1.0.0", lifespan=lifespan)

    async def read_json(request: Request) -> dict[str, Any]:
        try:
            data = await request.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body must be valid JSON.",
            ) from exc
        if not isinstance(data, dict):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Request body must be a JSON object.",
            )
        return data

    def validated_task(data: dict[str, Any]) -> tuple[str, str, str, str | None, str]:
        title = data.get("title")
        if not isinstance(title, str) or not title.strip():
            raise HTTPException(status_code=422, detail="A task title is required.")
        title = title.strip()
        if len(title) > 160:
            raise HTTPException(status_code=422, detail="Task titles must be 160 characters or fewer.")

        description = data.get("description", "")
        if not isinstance(description, str) or len(description) > 1000:
            raise HTTPException(status_code=422, detail="Descriptions must be 1,000 characters or fewer.")

        tag = data.get("tag", "Personal")
        if not isinstance(tag, str):
            raise HTTPException(status_code=422, detail="Tag must be text.")
        tag = tag.strip() or "Personal"
        if len(tag) > 32:
            raise HTTPException(status_code=422, detail="Tags must be 32 characters or fewer.")

        due_date = data.get("due_date") or None
        if due_date is not None:
            if not isinstance(due_date, str):
                raise HTTPException(status_code=422, detail="Due date must be a date.")
            try:
                date.fromisoformat(due_date)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail="Due date must use YYYY-MM-DD format.") from exc

        priority = data.get("priority", "normal")
        if not isinstance(priority, str) or priority not in PRIORITIES:
            raise HTTPException(status_code=422, detail="Priority must be low, normal, or high.")

        return title, description.strip(), tag, due_date, priority

    def task_dict(row: sqlite3.Row) -> dict[str, Any]:
        task = dict(row)
        task["completed"] = bool(task["completed"])
        return task

    @application.get("/api/tasks")
    def list_tasks(
        status_filter: str = "all",
        tag: str | None = None,
        q: str = "",
    ) -> list[dict[str, Any]]:
        if status_filter not in {"all", "active", "completed"}:
            raise HTTPException(status_code=422, detail="Status filter must be all, active, or completed.")

        clauses: list[str] = []
        parameters: list[Any] = []
        if status_filter == "active":
            clauses.append("completed = 0")
        elif status_filter == "completed":
            clauses.append("completed = 1")
        if tag:
            clauses.append("tag = ? COLLATE NOCASE")
            parameters.append(tag)
        if q.strip():
            clauses.append("(title LIKE ? ESCAPE '\\' OR description LIKE ? ESCAPE '\\')")
            escaped_query = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            parameters.extend((f"%{escaped_query}%", f"%{escaped_query}%"))

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with closing(connect()) as connection:
            rows = connection.execute(
                f"""
                SELECT id, title, description, tag, due_date, priority, completed, created_at
                FROM tasks
                {where}
                ORDER BY completed ASC, due_date IS NULL ASC, due_date ASC, created_at DESC
                """,
                parameters,
            ).fetchall()
        return [task_dict(row) for row in rows]

    @application.get("/api/tags")
    def list_tags() -> list[str]:
        with closing(connect()) as connection:
            rows = connection.execute(
                "SELECT DISTINCT tag FROM tasks ORDER BY tag COLLATE NOCASE"
            ).fetchall()
        tags = list(DEFAULT_TAGS)
        known = {value.casefold() for value in tags}
        for row in rows:
            value = row["tag"]
            if value.casefold() not in known:
                tags.append(value)
                known.add(value.casefold())
        return tags

    @application.post("/api/tasks", status_code=status.HTTP_201_CREATED)
    async def create_task(request: Request) -> dict[str, Any]:
        title, description, tag, due_date, priority = validated_task(await read_json(request))
        created_at = datetime.now(timezone.utc).isoformat()
        with closing(connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO tasks (title, description, tag, due_date, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (title, description, tag, due_date, priority, created_at),
            )
            connection.commit()
            row = connection.execute(
                "SELECT id, title, description, tag, due_date, priority, completed, created_at FROM tasks WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        return task_dict(row)

    @application.put("/api/tasks/{task_id}")
    async def update_task(task_id: int, request: Request) -> dict[str, Any]:
        data = await read_json(request)
        title, description, tag, due_date, priority = validated_task(data)
        completed = data.get("completed", False)
        if not isinstance(completed, bool):
            raise HTTPException(status_code=422, detail="Completed must be true or false.")

        with closing(connect()) as connection:
            cursor = connection.execute(
                """
                UPDATE tasks
                SET title = ?, description = ?, tag = ?, due_date = ?, priority = ?, completed = ?
                WHERE id = ?
                """,
                (title, description, tag, due_date, priority, int(completed), task_id),
            )
            connection.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Task not found.")
            row = connection.execute(
                "SELECT id, title, description, tag, due_date, priority, completed, created_at FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return task_dict(row)

    @application.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_task(task_id: int) -> None:
        with closing(connect()) as connection:
            cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            connection.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found.")

    application.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return application


app = create_app()
