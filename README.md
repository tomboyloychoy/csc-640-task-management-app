# Tamana

Tamana is a task-management app with a Python, FastAPI, and SQLite backend and a static GitHub Pages demo. The local API uses direct, parameterized SQL; the Pages demo stores tasks in the visitor's browser.

## Project stage

The project goal is to demonstrate the difference between a **minimum, low-level implementation** and a **higher-level software engineering implementation**.

This repository contains **Stage 1**, the low-level baseline. It uses FastAPI, SQLite, and direct, parameterized SQL to implement the minimum working product. Stage 1 proves the core behavior and establishes acceptance criteria that later work must preserve.

**Stage 2 is proposed, not implemented.** It is expected to raise the level of engineering by adding abstractions and practices such as SQLAlchemy for persistence, Pydantic for request/response schemas and validation, and a more explicit specification workflow. Stage 2 will be compared with this Stage 1 baseline rather than weakening or replacing it silently.

## Branch workflow

The project uses three main development branches: `main`, `stage-1`, and `stage-2`. Stage 1 development is complete and is currently represented on `main`. Stage 2 work will be developed on `stage-2`; when that development and its verification are complete, it will be merged into `main`. The `stage-1` branch preserves the Stage 1 baseline for reference and comparison.
## Features

- Create, edit, complete, and delete tasks
- Add optional notes, due dates, and priority levels
- Organize tasks with built-in tags (School, Work, House, Personal, and Other) or enter your own
- Filter by status or tag, search task names and notes, and sort the current list
- Keep local app data in a SQLite database at `data/tamana.db`
- Save Pages demo data in browser-local storage (not shared or synced across devices)

## Run locally

Python 3.10 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
python -m uvicorn code.app.main:app --reload --env-file .env
```

Open <http://127.0.0.1:8000>. The database is created automatically when the app starts. `.env` contains local settings and is ignored by Git; use `.env.example` as the shareable template. The local `.env` provisions a development admin account; change its credentials before use outside your local machine. To use the `pytest` suite, install `requirements-dev.txt` and run `python -m pytest`.

## SQLite database, CRUD, and schema

The project uses **SQLite as the permitted database option** instead of MySQL. This section documents the corresponding database requirement: **MySQL CRUD works with documented schema and setup** (satisfied in this project by SQLite option 1).

The local database is stored at `data/tamana.db`. It is created automatically on application startup; no separate database server or manual SQL setup is required.

### Users table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0
        CHECK (is_admin IN (0, 1)),
    created_at TEXT NOT NULL
);
```

The application supports user registration (create), login and profile read (read), and profile display-name updates (update). Password values are hashed and are never returned by API responses.

### Tasks table

```sql
CREATE TABLE tasks (
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
);
```

Task CRUD is implemented through the authenticated API:

- **Create:** `POST /api/tasks`
- **Read:** `GET /api/tasks`
- **Update:** `PUT /api/tasks/{task_id}`
- **Delete:** `DELETE /api/tasks/{task_id}`

Queries use parameterized SQL, and task operations are scoped to the authenticated user. Tests use temporary SQLite databases and do not modify the production database. The schema is initialized by `create_app()` in [code/app/main.py](code/app/main.py).

## API documentation

Open <http://127.0.0.1:8000/docs> for the standard Swagger UI API reference. It shows endpoint details and request examples, but **Try it out** and **Authorize** are disabled so the page is informational only. For the submitted endpoint tutorial, see the [Marp API documentation source](docs/api-documentation.md) and its [PDF export](docs/api-documentation.pdf). Use `python -m pytest -q` or an API client to send requests.

## Test with Postman

With the local app running, use `http://127.0.0.1:8000` as the base URL:

1. Send **POST** `/api/auth/register` with **Body → raw → JSON**:
   ```json
   {"username":"postman_user","password":"Secret123!","display_name":"Postman User"}
   ```
   Use a new username if this one is already registered.
2. Send **POST** `/api/auth/login` with:
   ```json
   {"username":"postman_user","password":"Secret123!"}
   ```
   Copy `access_token` from the response.
3. For a protected request, open **Authorization**, choose **Bearer Token**, and paste the token. Try **GET** `/api/users/me` or **GET** `/api/tasks`.

## GitHub Pages demo

The Pages workflow publishes the static website from `code/frontend/` at the site root and copies the short documentation files from `docs/` under `/docs/`. The public URLs are `https://tomboyloychoy.github.io/csc-640-task-management-app/` and `https://tomboyloychoy.github.io/csc-640-task-management-app/docs/` once Pages is enabled and the deployment workflow completes. The GitHub Pages demo uses browser-local storage because GitHub Pages cannot run FastAPI or SQLite. Use the local instructions above for the Python + SQLite Stage 1 app.

The Marp API tutorial is in [docs/api-documentation.md](docs/api-documentation.md), with the PDF export at [docs/api-documentation.pdf](docs/api-documentation.pdf). It documents all ten endpoints' methods, paths, authentication, inputs, outputs, and success/failure examples. Detailed proposal, architecture, setup, and engineering documentation is maintained in the [Tamana documentation repository](https://github.com/tomboyloychoy/csc-640-tamana-documentation). Project planning and quality evidence are maintained under `plan/`.

## Project layout

- `code/app/main.py` — FastAPI routes, validation, and direct SQLite queries
- `code/frontend/` — responsive browser interface
- `docs/README.md` — documentation index
- `docs/api-documentation.md` — Marp API tutorial for all ten endpoints
- `docs/api-documentation.pdf` — exported PDF tutorial
- `presentation/` — slide deck for project presentation
- `plan/` — quality plan, design decisions, and verification approach
- `tests/acceptance.md` — acceptance contract for all ten APIs
- `tests/test_readme.md` — explanation of test coverage and results
- `tests/test_page.html` — browser-based endpoint smoke test
- `tests/test_api.py` — API, migration, and regression tests
- `tests/test_acceptance.py` — executable acceptance tests
- `tests/results/` — recorded test-run output

### Testing

The `tests/` folder separates reproducible implementation checks from their supporting documentation:

- `test_api.py` covers OpenAPI examples, read-only Swagger UI, SQLite migrations, authentication, task/profile lifecycles, admin controls, invalid input, expired tokens, and cross-user isolation.
- `test_acceptance.py` treats all ten APIs as acceptance cases and checks HTTP status, response shape/content, authorization failures, task ownership, persistence within a test run, and secret redaction.
- `acceptance.md` records the shared success and failure contract and Stage 1 versus Stage 2 expectations.
- `test_readme.md` explains how to run, interpret, and extend the suite.
- `test_page.html` provides an HTML/JavaScript smoke test for running the endpoint checks from a browser and seeing success/error results.
- `results/latest.txt` saves the latest local pytest summary.

Run the Stage 1 suite with:

```powershell
python -m pytest -q
```

Start the app, then open `http://127.0.0.1:8000/test-page` to run the browser endpoint test page.

GitHub Pages can publish static files but cannot run the FastAPI/SQLite backend; deploy the complete app to a Python-capable host to make it available online.

## API and authentication

The local FastAPI app has route implementations for the ten APIs below, including JWT authentication and per-user task filtering. The current pytest suite covers the core registration/login/task lifecycle plus the critical auth edge cases from [tests/acceptance.md](tests/acceptance.md), including expired tokens and cross-user task isolation. The acceptance plan still acts as the broader contract for additional edge-case checks and staged Stage 2 parity.

Registration and login are public endpoints; task and profile routes require an authenticated `UserBearer` token. Registration and login use a unique username (3-30 letters, numbers, or underscores; case-insensitive) and password. Administrators can access the user list through an `AdminBearer` token after provisioning an admin account via `TAMANA_ADMIN_USERNAME` and `TAMANA_ADMIN_PASSWORD`. User accounts and task ownership are stored in SQLite; passwords are bcrypt-hashed and queries use parameterized SQL.

In the local browser app, visitors without a valid session are shown the sign-in/register screen before they can access tasks. After signing in, the app keeps the JWT in browser storage and sends it with protected API requests; signing out clears it. The GitHub Pages demo remains unauthenticated and stores tasks only in browser-local storage.

Generate a strong secret key locally with Python's cryptographically secure `secrets` module:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the output into `.env` as the value of `TAMANA_SECRET_KEY`. Keep it private and out of Git; do not use a website to generate or share it. Changing the key invalidates existing login tokens, so users must sign in again. Set `TAMANA_TOKEN_TTL_MINUTES` as needed. The built-in signing key and fallback admin password are development defaults only; do not use them in a deployed environment. When an older database is upgraded, existing account usernames are derived from the part of the email address before `@`; user IDs and task ownership are preserved. Existing tasks from before authentication may still have no owner and are not automatically assigned to a user.

| # | Method | Path | Route implementation | Authorization |
|---|---|---|---|---|
| 1 | `GET` | `/api/tasks` | Present; Stage 1 acceptance cases tested | `UserBearer` |
| 2 | `POST` | `/api/tasks` | Present; Stage 1 acceptance cases tested | `UserBearer` |
| 3 | `PUT` | `/api/tasks/{task_id}` | Present; Stage 1 acceptance cases tested | `UserBearer` |
| 4 | `DELETE` | `/api/tasks/{task_id}` | Present; Stage 1 acceptance cases tested | `UserBearer` |
| 5 | `GET` | `/api/tags` | Present; Stage 1 acceptance cases tested | `UserBearer` |
| 6 | `POST` | `/api/auth/register` | Present; Stage 1 acceptance cases tested | Public |
| 7 | `POST` | `/api/auth/login` | Present; Stage 1 acceptance cases tested | Public; returns a `UserBearer` JWT |
| 8 | `GET` | `/api/users/me` | Present; Stage 1 acceptance cases tested | `UserBearer` |
| 9 | `PATCH` | `/api/users/me` | Present; Stage 1 acceptance cases tested | `UserBearer` |
| 10 | `GET` | `/api/admin/users` | Present; Stage 1 acceptance cases tested | `AdminBearer` |

The static GitHub Pages demo continues to use browser-local storage and does not run the FastAPI backend. Run `python -m pytest -q tests` to execute the API acceptance and regression tests.

## AI assistance disclosure

OpenAI **GPT-6 Luna**, accessed through the **Copilot SDK in VS Code**, assisted with implementation and documentation work for this project. Assistance included code-change support and drafting or revising the README, API documentation, test documentation, and project presentation. I reviewed the resulting work and ran the test suite; I remain responsible for the submitted implementation and can explain its behavior and tests.
