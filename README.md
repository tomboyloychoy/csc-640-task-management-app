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
