# Tamana

Tamana is a task-management app with a Python, FastAPI, and SQLite backend and a static GitHub Pages demo. The local API uses direct, parameterized SQL; the Pages demo stores tasks in the visitor's browser.

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
python -m uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. The database is created automatically when the app starts. To use the `pytest` suite, install `requirements-dev.txt` and run `python -m pytest`.

## GitHub Pages demo

The Pages workflow publishes the static website from `frontend/` at the site root and the Hugo documentation from `docs/` under `/docs/`. The public URLs are `https://tomboyloychoy.github.io/csc-640-task-management-app/` and `https://tomboyloychoy.github.io/csc-640-task-management-app/docs/` once Pages is enabled and the deployment workflow completes. The GitHub Pages demo uses browser-local storage because GitHub Pages cannot run FastAPI or SQLite. Use the local instructions above for the Python + SQLite Stage 1 app.

The Hugo site provides engineering guidance for defining quality criteria, gathering verification evidence, documenting design decisions, and evaluating the planned evolution from direct SQL to SQLAlchemy and Pydantic. It uses Tamana as a practical example and distinguishes implemented behavior from proposed work. Source pages are maintained under `docs/content/`.

## Project layout

- `app/main.py` — FastAPI routes, validation, and direct SQLite queries
- `frontend/` — responsive browser interface
- `docs/` — Hugo project and API documentation
- `tests/` — API and persistence behavior tests

GitHub Pages can publish static files but cannot run the FastAPI/SQLite backend; deploy the complete app to a Python-capable host to make it available online.

## API and authentication

The local FastAPI app has route implementations for the ten APIs below, including JWT authentication and per-user task filtering. The current pytest suite covers the core registration/login/task lifecycle plus the critical auth edge cases from [tests/acceptance.md](tests/acceptance.md), including expired tokens and cross-user task isolation. The acceptance plan still acts as the broader contract for additional edge-case checks and staged Stage 2 parity.

Registration and login are public endpoints; task and profile routes require an authenticated `UserBearer` token. Administrators can access the user list through an `AdminBearer` token after provisioning an admin account via `TAMANA_ADMIN_EMAIL` and `TAMANA_ADMIN_PASSWORD`. User accounts and task ownership are stored in SQLite; passwords are bcrypt-hashed and queries use parameterized SQL.

Configure `TAMANA_SECRET_KEY` to a strong, private value and set `TAMANA_TOKEN_TTL_MINUTES` for the deployment. The built-in signing key and fallback admin password are development defaults only; do not use them in a deployed environment. Existing tasks in a database created before authentication may have no owner and are not automatically assigned to a user.

| # | Method | Path | Route implementation | Authorization |
|---|---|---|---|---|
| 1 | `GET` | `/api/tasks` | Present; acceptance coverage incomplete | `UserBearer` |
| 2 | `POST` | `/api/tasks` | Present; acceptance coverage incomplete | `UserBearer` |
| 3 | `PUT` | `/api/tasks/{task_id}` | Present; acceptance coverage incomplete | `UserBearer` |
| 4 | `DELETE` | `/api/tasks/{task_id}` | Present; acceptance coverage incomplete | `UserBearer` |
| 5 | `GET` | `/api/tags` | Present; acceptance coverage incomplete | `UserBearer` |
| 6 | `POST` | `/api/auth/register` | Present; acceptance coverage incomplete | Public |
| 7 | `POST` | `/api/auth/login` | Present; acceptance coverage incomplete | Public; returns a `UserBearer` JWT |
| 8 | `GET` | `/api/users/me` | Present; acceptance coverage incomplete | `UserBearer` |
| 9 | `PATCH` | `/api/users/me` | Present; acceptance coverage incomplete | `UserBearer` |
| 10 | `GET` | `/api/admin/users` | Present; acceptance coverage incomplete | `AdminBearer` |

The static GitHub Pages demo continues to use browser-local storage and does not run the FastAPI backend. Run `python -m pytest -q` for the current automated tests; completing the cases in `tests/acceptance.md` and addressing any failures remains part of finishing the API work.
