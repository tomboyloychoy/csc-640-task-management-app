from __future__ import annotations

import os
import re
import sqlite3
from contextlib import asynccontextmanager, closing
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from jwt import ExpiredSignatureError, InvalidTokenError

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DEFAULT_TAGS = ("School", "Work", "House", "Personal", "Other")
PRIORITIES = {"low", "normal", "high"}
SECRET_KEY = os.getenv("TAMANA_SECRET_KEY", "tamana-dev-secret-key")
ALGORITHM = "HS256"
TOKEN_TTL_MINUTES = int(os.getenv("TAMANA_TOKEN_TTL_MINUTES", "1440"))
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
security = HTTPBearer(auto_error=False)


def create_app(database_path: Path | str | None = None) -> FastAPI:
    db_path = Path(database_path) if database_path else ROOT_DIR / "data" / "tamana.db"

    def connect() -> sqlite3.Connection:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize_database() -> None:
        with closing(connect()) as connection:
            user_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(users)")
            }
            if not user_columns:
                create_users_table(connection, "users")
            elif "username" not in user_columns:
                migrate_users_to_username(connection)

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    tag TEXT NOT NULL DEFAULT 'Personal',
                    due_date TEXT,
                    priority TEXT NOT NULL DEFAULT 'normal'
                        CHECK (priority IN ('low', 'normal', 'high')),
                    completed INTEGER NOT NULL DEFAULT 0
                        CHECK (completed IN (0, 1)),
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
                """
            )
            existing_columns = [
                row[1] for row in connection.execute("PRAGMA table_info(tasks)").fetchall()
            ]
            if "user_id" not in existing_columns:
                connection.execute(
                    "ALTER TABLE tasks ADD COLUMN user_id INTEGER REFERENCES users(id)"
                )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)"
            )
            connection.commit()
            ensure_admin_account(connection)

    def create_users_table(connection: sqlite3.Connection, table_name: str) -> None:
        connection.execute(
            f"""
            CREATE TABLE {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0
                    CHECK (is_admin IN (0, 1)),
                created_at TEXT NOT NULL
            )
            """
        )

    def migrate_users_to_username(connection: sqlite3.Connection) -> None:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("BEGIN IMMEDIATE")
        create_users_table(connection, "users_username_migration")
        used_usernames: set[str] = set()
        old_users = connection.execute(
            "SELECT id, email, password_hash, display_name, is_admin, created_at FROM users ORDER BY id"
        ).fetchall()
        for user in old_users:
            username = username_from_legacy_email(user["email"], used_usernames)
            connection.execute(
                """
                INSERT INTO users_username_migration
                    (id, username, password_hash, display_name, is_admin, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user["id"],
                    username,
                    user["password_hash"],
                    user["display_name"],
                    user["is_admin"],
                    user["created_at"],
                ),
            )
        connection.execute("DROP TABLE users")
        connection.execute("ALTER TABLE users_username_migration RENAME TO users")
        connection.commit()

    def username_from_legacy_email(email: str, used_usernames: set[str]) -> str:
        local_part = email.split("@", 1)[0].lower()
        base = re.sub(r"[^a-z0-9_]", "_", local_part).strip("_")
        if len(base) < 3:
            base = f"{base}user"
        base = base[:30]
        username = base
        suffix = 2
        while username.casefold() in used_usernames:
            suffix_text = f"_{suffix}"
            username = f"{base[:30 - len(suffix_text)]}{suffix_text}"
            suffix += 1
        used_usernames.add(username.casefold())
        return username

    def ensure_admin_account(connection: sqlite3.Connection) -> None:
        admin_username = os.getenv("TAMANA_ADMIN_USERNAME")
        if not admin_username:
            legacy_admin_email = os.getenv("TAMANA_ADMIN_EMAIL")
            if legacy_admin_email:
                admin_username = legacy_admin_email.split("@", 1)[0]
        if not admin_username:
            return
        admin_username = admin_username.strip().lower()
        if not USERNAME_RE.fullmatch(admin_username):
            raise ValueError("TAMANA_ADMIN_USERNAME must be 3-30 letters, numbers, or underscores.")
        admin_password = os.getenv("TAMANA_ADMIN_PASSWORD", "admin123")
        existing = connection.execute(
            "SELECT id FROM users WHERE username = ?",
            (admin_username,),
        ).fetchone()
        if existing is None:
            connection.execute(
                """
                INSERT INTO users (username, password_hash, display_name, is_admin, created_at)
                VALUES (?, ?, ?, 1, ?)
                """,
                (
                    admin_username,
                    bcrypt.hashpw(admin_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
                    os.getenv("TAMANA_ADMIN_DISPLAY_NAME", "Administrator"),
                    datetime.now(timezone.utc).isoformat(),
                ),
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

    def create_access_token(user_id: int) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TTL_MINUTES)
        payload = {"sub": str(user_id), "exp": expires_at}
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def decode_access_token(token: str) -> int:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except ExpiredSignatureError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired.") from exc
        except InvalidTokenError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.") from exc

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
        try:
            return int(user_id)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.") from exc

    def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> sqlite3.Row:
        if credentials is None or not credentials.scheme.lower() == "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

        user_id = decode_access_token(credentials.credentials)
        with closing(connect()) as connection:
            user = connection.execute(
                "SELECT id, username, display_name, is_admin, password_hash FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
        return user

    def get_admin_user(current_user: sqlite3.Row = Depends(get_current_user)) -> sqlite3.Row:
        if not current_user["is_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
        return current_user

    def user_response(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "username": row["username"],
            "display_name": row["display_name"],
        }

    def validated_username(value: Any) -> str:
        if not isinstance(value, str) or not USERNAME_RE.fullmatch(value.strip()):
            raise HTTPException(
                status_code=422,
                detail="Username must be 3-30 characters using only letters, numbers, or underscores.",
            )
        return value.strip().lower()

    def validated_password(value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise HTTPException(status_code=422, detail="A password is required.")
        if len(value) < 8:
            raise HTTPException(status_code=422, detail="Passwords must be at least 8 characters long.")
        return value

    def validated_display_name(value: Any) -> str:
        if not isinstance(value, str):
            raise HTTPException(status_code=422, detail="Display name must be text.")
        display_name = value.strip()
        if not display_name:
            raise HTTPException(status_code=422, detail="Display name cannot be blank.")
        if len(display_name) > 80:
            raise HTTPException(status_code=422, detail="Display names must be 80 characters or fewer.")
        return display_name

    @application.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
    async def register_user(request: Request) -> dict[str, Any]:
        data = await read_json(request)
        username = validated_username(data.get("username"))
        password = validated_password(data.get("password"))
        display_name = validated_display_name(data.get("display_name", username))

        with closing(connect()) as connection:
            existing = connection.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if existing is not None:
                raise HTTPException(status_code=409, detail="That username is already taken.")

            cursor = connection.execute(
                """
                INSERT INTO users (username, password_hash, display_name, is_admin, created_at)
                VALUES (?, ?, ?, 0, ?)
                """,
                (
                    username,
                    bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
                    display_name,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            connection.commit()
            user = connection.execute(
                "SELECT id, username, display_name, is_admin, password_hash FROM users WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()

        return user_response(user)

    @application.post("/api/auth/login")
    async def login_user(request: Request) -> dict[str, Any]:
        data = await read_json(request)
        username = validated_username(data.get("username"))
        password = validated_password(data.get("password"))

        with closing(connect()) as connection:
            user = connection.execute(
                "SELECT id, username, display_name, password_hash, is_admin FROM users WHERE username = ?",
                (username,),
            ).fetchone()

        if user is None or not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            raise HTTPException(status_code=401, detail="Invalid username or password.")

        token = create_access_token(user["id"])
        return {"access_token": token, "token_type": "bearer"}

    @application.get("/api/users/me")
    def read_user(current_user: sqlite3.Row = Depends(get_current_user)) -> dict[str, Any]:
        return user_response(current_user)

    @application.patch("/api/users/me")
    async def update_user(request: Request, current_user: sqlite3.Row = Depends(get_current_user)) -> dict[str, Any]:
        data = await read_json(request)
        display_name = validated_display_name(data.get("display_name"))

        with closing(connect()) as connection:
            connection.execute(
                "UPDATE users SET display_name = ? WHERE id = ?",
                (display_name, current_user["id"]),
            )
            connection.commit()
            user = connection.execute(
                "SELECT id, username, display_name, is_admin, password_hash FROM users WHERE id = ?",
                (current_user["id"],),
            ).fetchone()
        return user_response(user)

    @application.get("/api/admin/users")
    def list_users(current_user: sqlite3.Row = Depends(get_admin_user)) -> list[dict[str, Any]]:
        with closing(connect()) as connection:
            rows = connection.execute(
                "SELECT id, username, display_name, is_admin, password_hash FROM users ORDER BY id ASC"
            ).fetchall()
        return [user_response(row) for row in rows]

    @application.get("/api/tasks")
    def list_tasks(
        current_user: sqlite3.Row = Depends(get_current_user),
        status_filter: str = "all",
        tag: str | None = None,
        q: str = "",
    ) -> list[dict[str, Any]]:
        if status_filter not in {"all", "active", "completed"}:
            raise HTTPException(status_code=422, detail="Status filter must be all, active, or completed.")

        clauses: list[str] = ["user_id = ?"]
        parameters: list[Any] = [current_user["id"]]
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
                SELECT id, user_id, title, description, tag, due_date, priority, completed, created_at
                FROM tasks
                {where}
                ORDER BY completed ASC, due_date IS NULL ASC, due_date ASC, created_at DESC
                """,
                parameters,
            ).fetchall()
        return [task_dict(row) for row in rows]

    @application.get("/api/tags")
    def list_tags(current_user: sqlite3.Row = Depends(get_current_user)) -> list[str]:
        with closing(connect()) as connection:
            rows = connection.execute(
                "SELECT DISTINCT tag FROM tasks WHERE user_id = ? ORDER BY tag COLLATE NOCASE",
                (current_user["id"],),
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
    async def create_task(request: Request, current_user: sqlite3.Row = Depends(get_current_user)) -> dict[str, Any]:
        title, description, tag, due_date, priority = validated_task(await read_json(request))
        created_at = datetime.now(timezone.utc).isoformat()
        with closing(connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO tasks (user_id, title, description, tag, due_date, priority, completed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (current_user["id"], title, description, tag, due_date, priority, created_at),
            )
            connection.commit()
            row = connection.execute(
                "SELECT id, user_id, title, description, tag, due_date, priority, completed, created_at FROM tasks WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        return task_dict(row)

    @application.put("/api/tasks/{task_id}")
    async def update_task(
        task_id: int,
        request: Request,
        current_user: sqlite3.Row = Depends(get_current_user),
    ) -> dict[str, Any]:
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
                WHERE id = ? AND user_id = ?
                """,
                (title, description, tag, due_date, priority, int(completed), task_id, current_user["id"]),
            )
            connection.commit()
            if cursor.rowcount == 0:
                existing = connection.execute(
                    "SELECT id FROM tasks WHERE id = ?",
                    (task_id,),
                ).fetchone()
                if existing is None:
                    raise HTTPException(status_code=404, detail="Task not found.")
                raise HTTPException(status_code=404, detail="Task not found.")
            row = connection.execute(
                "SELECT id, user_id, title, description, tag, due_date, priority, completed, created_at FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return task_dict(row)

    @application.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_task(task_id: int, current_user: sqlite3.Row = Depends(get_current_user)) -> None:
        with closing(connect()) as connection:
            cursor = connection.execute(
                "DELETE FROM tasks WHERE id = ? AND user_id = ?",
                (task_id, current_user["id"]),
            )
            connection.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found.")

    application.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return application


app = create_app()
