---
marp: true
theme: default
paginate: true
size: 16:9
title: "Tamana Stage 1 API Documentation"
description: "Inputs, outputs, authentication, and success/failure examples for all Stage 1 endpoints."
---

# Tamana Stage 1 API

## Endpoint tutorial

Stage 1 · FastAPI · SQLite · Direct SQL

Base URL: `http://127.0.0.1:8000`

All examples use JSON where a request body is required.

---

# API conventions

- Protected routes expect `Authorization: Bearer <JWT>`.
- User tokens are returned by login.
- Admin routes require a token for an administrator account.
- Error responses use `{"detail":"..."}`.
- Passwords and password hashes are never returned.
- All ten endpoints below are implemented in Stage 1.

---

# Endpoint map

| Method and path | Authentication |
|---|---|
| `GET /api/tasks` | User |
| `POST /api/tasks` | User |
| `PUT /api/tasks/{task_id}` | User |
| `DELETE /api/tasks/{task_id}` | User |
| `GET /api/tags` | User |
| `POST /api/auth/register` | Public |
| `POST /api/auth/login` | Public |
| `GET /api/users/me` | User |
| `PATCH /api/users/me` | User |
| `GET /api/admin/users` | Admin |

---

# 1. List tasks

## `GET /api/tasks`

**Authentication:** user bearer token.

**Inputs:** optional query parameters:

- `status_filter`: `all` (default), `active`, or `completed`
- `tag`: case-insensitive tag filter
- `q`: searches task title and description

**Success `200`:** array of current user's task objects.

```json
[
  {
    "id": 12,
    "user_id": 4,
    "title": "Review report",
    "description": "Check results",
    "tag": "School",
    "due_date": null,
    "priority": "normal",
    "completed": false,
    "created_at": "2026-11-21T18:00:00+00:00"
  }
]
```

---

# 1. List tasks — failure examples

Invalid filter:

```http
GET /api/tasks?status_filter=paused
Authorization: Bearer <user-jwt>
```

**Response `422`:**

```json
{"detail":"Status filter must be all, active, or completed."}
```

Missing token: **`401`** with `{"detail":"Not authenticated."}`.

Another user's tasks are excluded; their list can return **`200 []`**.

---

# 2. Create task

## `POST /api/tasks`

**Authentication:** user bearer token.

**Input:** JSON object. `title` is required. Optional fields: `description`, `tag`, `due_date`, `priority`. Defaults: empty description, `Personal` tag, no due date, `normal` priority, and incomplete.

```json
{
  "title": "Prepare report",
  "description": "Review results",
  "tag": "School",
  "due_date": "2026-12-01",
  "priority": "high"
}
```

**Success `201`:** created task object:

```json
{
  "id": 12,
  "user_id": 4,
  "title": "Prepare report",
  "description": "Review results",
  "tag": "School",
  "due_date": "2026-12-01",
  "priority": "high",
  "completed": false,
  "created_at": "2026-11-21T18:00:00+00:00"
}
```

---

# 2. Create task — failure examples

Invalid title:

```json
{"title":" "}
```

**Response `422`:**

```json
{"detail":"A task title is required."}
```

Invalid date or priority also returns **`422`** with a non-empty `detail`.

Without a token, a valid body returns **`401`** and no task is created.

---

# 3. Update task

## `PUT /api/tasks/{task_id}`

**Authentication:** user bearer token; task must belong to that user.

**Input:** integer `task_id` in the path and JSON fields `title`, `description`, `tag`, `due_date`, `priority`, and optional boolean `completed`. Update defaults follow the create-task defaults; omitted `completed` becomes `false`.

```json
{
  "title": "Prepare report",
  "description": "Reviewed",
  "tag": "School",
  "due_date": "2026-12-01",
  "priority": "normal",
  "completed": true
}
```

**Success `200`:** updated task object with the same task ID:

```json
{
  "id": 12,
  "user_id": 4,
  "title": "Prepare report",
  "description": "Reviewed",
  "tag": "School",
  "due_date": "2026-12-01",
  "priority": "normal",
  "completed": true,
  "created_at": "2026-11-21T18:00:00+00:00"
}
```

---

# 3. Update task — failure examples

Blank-title request:

```http
PUT /api/tasks/12
Authorization: Bearer <user-jwt>
Content-Type: application/json

{"title":" "}
```

Returns **`422`**:

```json
{"detail":"A task title is required."}
```

Valid-body request for an unknown or other user's task returns **`404`**:

```json
{"detail":"Task not found."}
```

Missing/invalid token returns **`401`**.

---

# 4. Delete task

## `DELETE /api/tasks/{task_id}`

**Authentication:** user bearer token; task must belong to that user.

**Input:** integer `task_id` in the path. No request body.

```http
DELETE /api/tasks/12
Authorization: Bearer <user-jwt>
```

**Success `204 No Content`:** empty response body; task is removed.

---

# 4. Delete task — failure examples

Unknown task:

```http
DELETE /api/tasks/99999
Authorization: Bearer <user-jwt>
```

**Response `404`:**

```json
{"detail":"Task not found."}
```

Deleting another user's task also returns **`404`** and leaves it available to its owner. Missing/invalid token returns **`401`**.

---

# 5. List tags

## `GET /api/tags`

**Authentication:** user bearer token.

**Inputs:** no path, query, or body parameters.

**Success `200`:** JSON array of built-in tags plus custom tags currently used by this user.

```json
["School", "Work", "House", "Personal", "Other", "Research"]
```

Custom tags are derived from the user's tasks. Removing the last task with a custom tag removes it from the returned list.

---

# 5. List tags — failure example

Request without authentication:

```http
GET /api/tags
```

**Response `401`:**

```json
{"detail":"Not authenticated."}
```

Malformed or expired bearer tokens also return **`401`**.

---

# 6. Register user

## `POST /api/auth/register`

**Authentication:** public.

**Inputs:** JSON fields:

- `username`: 3–30 letters, numbers, or underscores; case-insensitive
- `password`: at least 8 characters
- `display_name`: optional; defaults to username; maximum 80 characters

```json
{
  "username": "student01",
  "password": "Secret123!",
  "display_name": "Student"
}
```

**Success `201`:** `{"id":5,"username":"student01","display_name":"Student"}`.

---

# 6. Register user — failure examples

Duplicate registration request (username comparison is case-insensitive):

```json
{"username":"STUDENT01","password":"Secret123!","display_name":"Student"}
```

Response **`409`**:

```json
{"detail":"That username is already taken."}
```

Invalid username or missing/short password: **`422`**

```json
{"detail":"Username must be 3-30 characters using only letters, numbers, or underscores."}
```

The response never contains `password` or `password_hash`.

---

# 7. Log in

## `POST /api/auth/login`

**Authentication:** public.

**Inputs:** JSON object with `username` and `password`, following registration validation.

```json
{"username":"student01","password":"Secret123!"}
```

**Success `200`:**

```json
{"access_token":"<signed-jwt>","token_type":"bearer"}
```

Use the returned token to access protected endpoints.

---

# 7. Log in — failure examples

Wrong-password request:

```json
{"username":"student01","password":"WrongPassword123"}
```

Response **`401`**:

```json
{"detail":"Invalid username or password."}
```

Missing fields or invalid username/password format returns **`422`**.

No token is returned on failure.

---

# 8. Read current profile

## `GET /api/users/me`

**Authentication:** user bearer token.

**Inputs:** no path, query, or body parameters.

**Success `200`:**

```json
{"id":5,"username":"student01","display_name":"Student"}
```

The profile is based on the authenticated token. No password or password hash is included.

---

# 8. Read profile — failure example

Request with no token:

```http
GET /api/users/me
```

**Response `401`:**

```json
{"detail":"Not authenticated."}
```

Malformed, expired, or invalidated tokens also return **`401`**.

---

# 9. Update current profile

## `PATCH /api/users/me`

**Authentication:** user bearer token.

**Input:** JSON object with `display_name` (text, non-blank, maximum 80 characters).

```json
{"display_name":"Student Updated"}
```

**Success `200`:**

```json
{"id":5,"username":"student01","display_name":"Student Updated"}
```

---

# 9. Update profile — failure examples

Blank display name:

```json
{"display_name":" "}
```

**Response `422`:**

```json
{"detail":"Display name cannot be blank."}
```

Wrong type or more than 80 characters also returns **`422`**. Missing/invalid token returns **`401`**; the profile remains unchanged.

---

# 10. List users as admin

## `GET /api/admin/users`

**Authentication:** administrator bearer token.

**Inputs:** no path, query, or body parameters.

**Success `200`:** users ordered by ID; each object contains only safe profile fields.

```json
[
  {"id":1,"username":"admin","display_name":"Administrator"},
  {"id":5,"username":"student01","display_name":"Student"}
]
```

Admin credentials are provisioned through local environment settings.

---

# 10. Admin users — failure examples

Request without a token returns **`401`**:

```http
GET /api/admin/users
```

```json
{"detail":"Not authenticated."}
```

A valid regular-user token: **`403`**

```json
{"detail":"Admin access required."}
```

Malformed or expired token: **`401`**. Password data is never included.

---

# Common response codes

| Code | Meaning |
|---|---|
| `200` | Request succeeded |
| `201` | User or task created |
| `204` | Task deleted; no body |
| `401` | Missing/invalid token or invalid credentials |
| `403` | User lacks administrator role |
| `404` | Task missing or not owned by caller |
| `409` | Username already exists |
| `422` | Invalid or incomplete input |

---

# Running and exporting

Run the app from the repository root:

```powershell
python -m uvicorn code.app.main:app --reload --env-file .env
```

Export the PDF from the repository root with Marp CLI:

```powershell
marp docs/api-documentation.md --pdf --output docs/api-documentation.pdf
```

The Marp source is this file; `docs/api-documentation.pdf` is the matching presentation export.
