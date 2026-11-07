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

## API Work Progress

This plan includes the information about 10 APIs that this application would have. `UserBearer` and `AdminBearer` are the two proposed JWT bearer authorization profiles. Registration and login are public. Admin access would require an admin role.

| # | Method | Path | Endpoint status | Authorization |
|---|---|---|---|---|
| 1 | `GET` | `/api/tasks` | IMPLEMENTED | `UserBearer` — TO-BE-IMPLEMENTED |
| 2 | `POST` | `/api/tasks` | IMPLEMENTED | `UserBearer` — TO-BE-IMPLEMENTED |
| 3 | `PUT` | `/api/tasks/{task_id}` | IMPLEMENTED | `UserBearer` — TO-BE-IMPLEMENTED |
| 4 | `DELETE` | `/api/tasks/{task_id}` | IMPLEMENTED | `UserBearer` — TO-BE-IMPLEMENTED |
| 5 | `GET` | `/api/tags` | IMPLEMENTED | `UserBearer` — TO-BE-IMPLEMENTED |
| 6 | `POST` | `/api/auth/register` | TO-BE-IMPLEMENTED | Public |
| 7 | `POST` | `/api/auth/login` | TO-BE-IMPLEMENTED | Public; returns a `UserBearer` JWT |
| 8 | `GET` | `/api/users/me` | TO-BE-IMPLEMENTED | `UserBearer` |
| 9 | `PATCH` | `/api/users/me` | TO-BE-IMPLEMENTED | `UserBearer` |
| 10 | `GET` | `/api/admin/users` | TO-BE-IMPLEMENTED | `AdminBearer` |

`IMPLEMENTED` describes the existing endpoint functionality only: the current task and tag routes are unauthenticated. Adding JWT authentication, user accounts, and per-user task ownership remains **TO-BE-IMPLEMENTED**. Token lifetime, signing-key configuration, and admin-account provisioning still need design decisions.
