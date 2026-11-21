# Tamana Test Folder

The test folder contains the acceptance contract, two executable Python test scripts, browser smoke-test assets, and saved pytest results.

## `test_api.py`

This script contains FastAPI and SQLite regression tests that cover:

- OpenAPI request examples and read-only Swagger UI behavior.
- Availability of the browser endpoint test page.
- Migration from the legacy task schema to task ownership fields.
- Migration from legacy email-based accounts to username-based accounts while preserving task IDs.
- Registration, login, profile updates, task creation/update/completion/deletion, tag listing, and filters.
- Missing or malformed authentication and administrator/regular-user authorization.
- Invalid usernames, passwords, duplicate accounts, and blank profile names.
- Expired-token rejection and isolation of one user's tasks from another user.

## `test_acceptance.py`

This script contains the executable acceptance suite for every endpoint. It uses a fresh SQLite database for each pytest fixture and verifies status codes, response bodies, persistence, and authorization behavior.

Coverage includes:

- **Task collection:** list, status/tag/text filters, empty results, invalid filters, missing and expired tokens, and user isolation.
- **Create/update/delete tasks:** valid payloads, blank titles, invalid dates/priorities, missing resources, cross-user access, and token failures.
- **Tags:** built-in tags, custom tags, and removal after the last tagged task is deleted.
- **Registration:** safe responses, username/password validation, and case-insensitive duplicate detection.
- **Login:** valid tokens, wrong passwords, unknown users, and missing credentials.
- **Profile:** profile reads and updates, secret-field redaction, invalid names, and token failures.
- **Admin users:** administrator success, missing/malformed/expired tokens, secret redaction, and regular-user rejection.

## Acceptance requirements

Each endpoint is covered by success assertions and relevant failure assertions. Tests use isolated SQLite databases, never production `data/tamana.db`, and assert JSON or empty-response details as appropriate. The suite provides reproducible setup and expected status/body behavior.

The browser test page at [test_page.html](test_page.html), available through `/test-page` while the local app is running, calls all ten API endpoints and displays success/error results. It is a smoke test for manual verification, while pytest remains the reproducible pass/fail suite.

## Running the tests

From the repository root:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

For the browser page:

```powershell
python -m uvicorn code.app.main:app --reload --env-file .env
```

Then open `http://127.0.0.1:8000/test-page`.

## Saved results

`results/latest.txt` records the latest local pytest command and pass/fail summary. Test evidence should include the revision, command, database setup, actual output, and any warnings. A failure must be fixed in the implementation or the test must be corrected only when it does not weaken the acceptance contract.
