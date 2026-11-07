---
marp: true
theme: default
paginate: true
size: 16:9
title: Tamana API Acceptance Tests
description: Shared acceptance criteria for all ten planned APIs across Stage 1 and Stage 2.
---

# Tamana API Acceptance Tests

## One contract for both stages

- **Stage 1:** FastAPI + SQLite
- **Stage 2:** SQLAlchemy + Pydantic
- Run the same feature requests, setup, status/content assertions, and authorization cases against both stages.
- Only app startup and test-database configuration may differ.
- This presentation specifies acceptance; it does not describe current implementation status.

---

## Test rules and assumptions

- Use an empty, isolated test database; never use production data or `data/tamana.db`.
- Register ordinary users through the API. Provision an admin only through a documented test fixture/bootstrap.
- Use unique emails or reset the database per run. Create tasks through the API.
- Every test checks HTTP status **and** response body/content. Any failure exits nonzero.
- `UserBearer` = valid user JWT; `AdminBearer` = valid administrator JWT.
- Protected routes: test valid, missing, malformed, and expired tokens.
- Admin routes: also test a valid non-admin token.

---

## API-shape assumptions to confirm

The README does not define account fields, profile fields, token lifetime, or admin provisioning. For repeatable acceptance tests, assume:

- Registration/login fields: `email`, `password`; editable profile: `display_name`.
- Register `201`; login and profile read/update `200`.
- Invalid input `422`; duplicate registration `409`.
- Invalid credentials or missing/invalid/expired token `401`.
- Authenticated non-admin accessing admin route `403`.
- Errors return JSON with a non-empty `detail`.
- Successful task/user responses assert required values and exclude passwords/hashes.

---

## Run and compare

```powershell
python -m pytest -q tests
```

- Run the same executable suite against each stage and a fresh test database.
- Record command, commit/revision, database setup, expected vs. actual status/body, and pass/fail counts.
- A stage passes only when every required case is implemented and passes.
- Do not weaken assertions to hide a failure.
- The current test suite is not yet a complete executable implementation of all cases in this acceptance plan.

---

## 1 — `GET /api/tasks` · `UserBearer`

| Case | Setup / request | Expected |
|---|---|---|
| List success | A registers/logs in; creates active `Research` task `Finish quality report` and one completed task; A lists tasks. | `200`; array contains both A tasks with IDs, titles, tags, completion states. |
| Filter/search | A requests `status_filter=active`, `tag=research`, `q=quality`. | `200`; array contains only the matching active task. |
| Empty result | A searches for a nonexistent title fragment. | `200`; `[]`. |
| Invalid filter | A sends `status_filter=unknown`. | `422`; JSON `detail`. |
| Missing / invalid token | Request without auth; then malformed token; then expired token. | Each `401`; JSON `detail`. |
| Isolation | B lists tasks after A's tasks exist, using B's valid token. | `200`; no A-owned task appears. |

---

## 2 — `POST /api/tasks` · `UserBearer`

| Case | Request | Expected |
|---|---|---|
| Success | A submits `{"title":"Finish quality report","description":"Review results","tag":"Research","due_date":"2026-11-12","priority":"high"}`. | `201`; generated ID, submitted values, `completed: false`; owned by A. |
| Invalid data | With valid token, submit blank title; separately malformed due date and unsupported priority. | Each `422`; JSON `detail`; no invalid task is created. |
| Missing token | Submit otherwise valid task without auth. | `401`; JSON `detail`; no task is created. |
| Invalid/expired token | Submit with malformed token, then expired token. | Each `401`; JSON `detail`; no task is created. |

---

## 3 — `PUT /api/tasks/{task_id}` · `UserBearer`

| Case | Request | Expected |
|---|---|---|
| Success | A updates own task title to `Submit quality report` and sets `completed: true`; list again. | `200`; same ID, updated values persist. |
| Invalid data | A updates with blank title or invalid priority. | `422`; JSON `detail`; original task unchanged. |
| Missing task | A updates nonexistent ID. | `404`; JSON `detail`. |
| Other user's task | B attempts to update A's task ID. | `404`; JSON `detail`; A's task unchanged and not disclosed. |
| Missing / invalid token | Attempt valid update with no token; then malformed and expired tokens. | Each `401`; JSON `detail`. |

---

## 4 — `DELETE /api/tasks/{task_id}` · `UserBearer`

| Case | Request | Expected |
|---|---|---|
| Success | A deletes own task with valid token; list tasks again. | `204`; empty body; deleted task absent. |
| Missing task | A deletes nonexistent ID. | `404`; JSON `detail`. |
| Other user's task | B attempts to delete A's task. | `404`; JSON `detail`; task remains available to A. |
| Missing / invalid token | Attempt deletion without token; then malformed and expired tokens. | Each `401`; JSON `detail`; task remains. |

---

## 5 — `GET /api/tags` · `UserBearer`

| Case | Request | Expected |
|---|---|---|
| Success | A creates tasks with built-in tags and custom `Research`, then lists tags. | `200`; array includes `School`, `Work`, `House`, `Personal`, `Other`, `Research`. |
| Remove unused custom tag | A deletes the last A-owned task tagged `Research`, then lists tags. | `200`; `Research` is absent. |
| Missing / invalid token | Request without token; then malformed and expired tokens. | Each `401`; JSON `detail`. |

---

## 6 — `POST /api/auth/register` · public

| Case | Request | Expected |
|---|---|---|
| Success | Submit unique valid `email`, `password`, `display_name`. | `201`; account ID/email/display name; no plaintext password or hash. |
| Invalid input | Submit malformed email or missing/blank password. | `422`; JSON `detail`; no account created. |
| Duplicate account | Register the same email twice. | Second request `409`; JSON `detail`; only one account exists. |

---

## 7 — `POST /api/auth/login` · public

| Case | Request | Expected |
|---|---|---|
| Success | Submit credentials for a registered account. | `200`; non-empty signed user token usable as `UserBearer`; no password/hash. |
| Wrong password | Registered email with incorrect password. | `401`; JSON `detail`; no token. |
| Unknown account | Credentials for unregistered email. | `401`; JSON `detail`; no token. |
| Missing credentials | Omit email or password. | `422`; JSON `detail`. |

---

## 8 — `GET /api/users/me` · `UserBearer`

| Case | Request | Expected |
|---|---|---|
| Success | A registers/logs in and reads profile with A's valid token. | `200`; A's ID/email/display name; no password/hash. |
| Missing token | Request without authorization. | `401`; JSON `detail`. |
| Invalid/expired token | Request with malformed token, then expired token. | Each `401`; JSON `detail`. |

---

## 9 — `PATCH /api/users/me` · `UserBearer`

| Case | Request | Expected |
|---|---|---|
| Success | A patches `{"display_name":"A Updated"}`, then reads profile. | `200`; updated display name persists; A's ID/email remain; no password/hash. |
| Invalid input | A submits invalid or blank display name. | `422`; JSON `detail`; profile unchanged. |
| Missing token | Submit valid update without authorization. | `401`; JSON `detail`; profile unchanged. |
| Invalid/expired token | Submit with malformed token, then expired token. | Each `401`; JSON `detail`; profile unchanged. |

---

## 10 — `GET /api/admin/users` · `AdminBearer`

| Case | Request | Expected |
|---|---|---|
| Success | Provision test admin; register a regular user; admin lists users with valid admin token. | `200`; array includes regular user's ID/email; no password/hash fields. |
| Missing token | Request without authorization. | `401`; JSON `detail`. |
| Invalid/expired token | Request with malformed token, then expired token. | Each `401`; JSON `detail`. |
| Insufficient role | Request with valid regular user's token. | `403`; JSON `detail`; no user list returned. |

---

## End-to-end workflow

1. Register user A and log in; use the returned token to read and update A's profile.
2. With A's token, create, list, update, complete, and delete a task; verify each response and final state.
3. List tags and verify custom-tag inclusion/removal.
4. Register and log in user B; verify B cannot read, update, or delete A's task by ID.
5. Verify missing-token requests to every protected endpoint are rejected.
6. Assert every step's status and body using the cases in this acceptance suite.

---

## Results record

Record revision, exact command, test database setup, expected vs. actual status/body, and pass/fail counts for each stage.

| Stage | Expected | Actual |
|---|---|---|
| Stage 1 — FastAPI + SQLite | Every planned case passes. | Not recorded for the complete planned-feature contract. |
| Stage 2 — SQLAlchemy/Pydantic | Every case passes with the same requests and expected feature responses as Stage 1. | Not run. |

**A failure must be fixed in the implementation. Never weaken or remove an acceptance assertion to make a run pass.**
