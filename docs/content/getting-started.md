---
title: "Getting started"
description: "Run Tamana and reproduce the current API test results."
---

## Requirements

- Python 3.10 or newer
- pip

## Run locally

From the repository root, create and activate a virtual environment, install dependencies, and start the API:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) for the application. The database is created automatically at `data/tamana.db` when the server starts.

The local API is available at `http://127.0.0.1:8000/api`. FastAPI's interactive OpenAPI UI is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) while the local server is running.

## Run tests

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

The checked-in API tests use a temporary SQLite database, so they do not depend on or modify `data/tamana.db`. To reproduce the current test evidence from the repository root, run `python -m pytest -q`. Read the output as evidence about only the cases exercised—not as proof that all quality criteria are met.

## GitHub Pages demo

The Pages build hosts the static browser app and this Hugo learning guide. 
