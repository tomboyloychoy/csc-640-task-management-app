---
marp: true
theme: default
paginate: true
size: 16:9
title: "Tamana Stage 1"
description: "How Stage 1 interprets and demonstrates software quality."
---

# Tamana — Stage 1

## Minimum development before high-level engineering

FastAPI · SQLite · Direct SQL · JWT authentication

---

# The project goal

The project compares two levels of implementation:

1. **Stage 1 — minimum development / low-level engineering**
2. **Stage 2 — proposed high-level software engineering**

Stage 1 demonstrates the core product with visible and understandable mechanisms:

- Direct SQLite queries
- Hand-written validation
- Explicit HTTP route behavior
- JWT authorization
- Acceptance and regression tests

The purpose is to prove what the product must do before improving how it is designed.

---

# Quality problem

A task application is not only a list of tasks.

Future teammates should be able to see:

- What behavior is required
- Which requests are valid
- Who owns the data
- How failures are reported
- How to reproduce verification

Stage 1 makes these decisions visible. Stage 2 would make shared structures more explicit and reusable.

---

# Stage 1 scope

Stage 1 is the minimum working implementation, not the final high-level architecture.

## Implemented

- Registration and login
- JWT-protected APIs
- User profiles
- Task CRUD
- Task filtering and tags
- SQLite persistence
- Administrator user listing
- Static browser demonstration

## Quality baseline

- Direct, parameterized SQL
- Isolated test databases
- Observable HTTP status and response behavior
- A documented test and acceptance process

---

# Product architecture

```text
Browser / API client
        |
        v
FastAPI routes
        |
        v
Validation and JWT authorization
        |
        v
Parameterized SQLite queries
        |
        v
data/tamana.db
```

The backend is in `code/app/main.py`; the static frontend is in `code/frontend/`.
---

# The SQLite model

## `users`

- `id`
- `username`
- `password_hash`
- `display_name`
- `is_admin`
- `created_at`

## `tasks`

- `id`
- `user_id`
- `title`
- `description`
- `tag`
- `due_date`
- `priority`
- `completed`
- `created_at`

---

# CRUD behavior

| Operation | Endpoint | Authorized behavior |
|---|---|---|
| Create | `POST /api/tasks` | Returns `201`; task belongs to current user |
| Read | `GET /api/tasks` | Returns only current user's tasks |
| Update | `PUT /api/tasks/{task_id}` | Returns `200`; other users receive `404` |
| Delete | `DELETE /api/tasks/{task_id}` | Returns `204`; other users receive `404` |


---

# Authentication and authorization

## Public

- `POST /api/auth/register`
- `POST /api/auth/login`

## Authenticated user

- Task endpoints
- Profile read and update
- Tag listing

## Administrator

- `GET /api/admin/users`

Missing, malformed, and expired bearer tokens return `401`. A valid regular user accessing the admin endpoint receives `403`.

---

# The ten API endpoints

| # | Endpoint | Purpose |
|---:|---|---|
| 1 | `GET /api/tasks` | List and filter tasks |
| 2 | `POST /api/tasks` | Create a task |
| 3 | `PUT /api/tasks/{task_id}` | Update a task |
| 4 | `DELETE /api/tasks/{task_id}` | Delete a task |
| 5 | `GET /api/tags` | List available tags |
| 6 | `POST /api/auth/register` | Register a user |
| 7 | `POST /api/auth/login` | Obtain a bearer token |
| 8 | `GET /api/users/me` | Read a profile |
| 9 | `PATCH /api/users/me` | Update a profile |
| 10 | `GET /api/admin/users` | List users as administrator |

---

# Example: create a task

```json
{
  "title": "Prepare project presentation",
  "description": "Review slides",
  "tag": "School",
  "due_date": "2026-12-01",
  "priority": "high"
}
```

Required header:

```text
Authorization: Bearer <access_token>
```

Success: `201 Created`  
Missing or invalid authentication: `401 Unauthorized`

---

# Example: update and delete

Update with `PUT /api/tasks/1`:

```json
{
  "title": "Prepare project presentation",
  "description": "Slides reviewed",
  "tag": "School",
  "due_date": "2026-12-01",
  "priority": "normal",
  "completed": true
}
```

Success: `200 OK`

Delete with `DELETE /api/tasks/1`: `204 No Content`

Missing task or cross-user access: `404 Not Found`

---

# Validation and clear failures

Quality includes predictable failure behavior.

The API reports:

- `401` — missing, malformed, or expired authentication
- `403` — insufficient role
- `404` — missing or inaccessible task
- `409` — duplicate username
- `422` — invalid input

Every error uses a non-empty JSON `detail` message.

Passwords and password hashes are not returned.

---

# What we test

## `tests/test_api.py`

- API schema and documentation
- Database migrations
- Authentication and admin controls
- Task/profile lifecycle
- Invalid input
- Expired tokens and user isolation
- Browser test page availability

## `tests/test_acceptance.py`

- Every endpoint
- Success and relevant failure cases
- Response status and body
- Ownership and persistence behavior

---

# Reproducible verification

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Current result:

```text
20 passed, 0 failed, 1 warning
```

Tests use temporary SQLite databases and do not modify `data/tamana.db`.

Evidence is recorded in `tests/results/latest.txt`.

---

# Browser test page

`tests/test_page.html` provides a manual HTML/JavaScript smoke test.

It:

- Runs from `/test-page`
- Calls all ten endpoints
- Uses a unique test username
- Displays each result as PASS or FAIL
- Shows the HTTP status and JSON/error response

Pytest remains the reproducible automated verification suite.

---

# Defining quality in practice

For this project, quality means:

1. Requirements become observable acceptance criteria.
2. Inputs are validated before storage.
3. SQL uses bound parameters.
4. Ownership is enforced at every task operation.
5. Success and failure responses are consistent.
6. Tests use isolated, reproducible data.
7. Setup and evidence are documented.

Quality is the combination of these practices—not only passing tests.

---

# Stage 2 — proposed

Stage 2 has not been implemented.

The proposed direction is to improve the Stage 1 baseline with higher-level engineering:

- **SQLAlchemy** instead of repeated direct SQL
- **Pydantic** schemas for typed validation and consistent response structures
- A clearer specification workflow and schema-driven development
- Session, migration, transaction, and ORM verification
- Stronger maintainability and repeatability for future changes

These tools may improve structure, but the project would measure their benefits rather than assume them.

---

# Stage 2 safeguards

The Stage 2 proposal would preserve Stage 1 behavior.

- Run the same acceptance requests
- Keep the same status codes and response bodies
- Preserve authentication and task ownership
- Keep an isolated test database
- Compare implementation effort and review findings
- Measure defects and maintainability, not only code appearance

Stage 2 passes only when the low-level baseline behavior is preserved.


---

# Stage 1 conclusion

Stage 1 establishes a working baseline:

- FastAPI and SQLite
- Ten implemented API endpoints
- Authentication and ownership
- Documented validation and errors
- Automated and browser verification
- Reproducible setup

The baseline proves that minimum implementation can already provide real, testable behavior.

**Stage 2 remains a proposal:** we will consider higher-level tools and process improvements only after preserving the proven Stage 1 contract.
