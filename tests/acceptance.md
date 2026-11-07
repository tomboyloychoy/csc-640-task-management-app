# Tamana acceptance tests

## Acceptance target

These are the acceptance tests for all ten APIs in the README plan. Run this same feature contract against Stage 1 and Stage 2: use the same request data, status codes, response content, authorization cases, and test assertions. Only application startup and test-database configuration may differ. The tests are feature acceptance criteria, not a description of current implementation status.

Stage 1 is the FastAPI + SQLite implementation. Stage 2 is SQLAlchemy/Pydantic implementation. `UserBearer` means a valid user JWT; `AdminBearer` means a valid administrator JWT. Protected routes must be checked with valid, missing, and invalid/expired tokens. Admin routes must additionally reject a valid non-admin user's token.

## Test setup and execution

Use an isolated, empty database for each run. Seed test accounts through registration, except the administrator account, which must be provisioned by a documented test-only fixture/bootstrap mechanism. Do not rely on production data or `data/tamana.db`. Use unique email addresses or reset the database between runs. Create task records through the API. The same test suite must call each stage's application and assert both HTTP status and JSON/body content; any failed assertion must make the test command exit nonzero.

For reproducable tests, this acceptance contract assumes `email` and `password` for registration/login, `display_name` as an editable profile field, registration returns `201`, login/profile reads/updates return `200`, invalid fields return `422`, duplicate registration returns `409`, invalid credentials or missing/invalid/expired tokens return `401`, and authenticated non-admin access returns `403`. 

Run the same suite against each stage, configured to target that stage's app and fresh test database:

```powershell
python -m pytest -q tests
```
## Planned API cases

In the tables, each failure row means each listed request is a separate assertion. Error responses must be JSON objects containing a non-empty `detail`. Successful task/user responses must assert the specified fields and values, not only the status.

### 1. `GET /api/tasks` — `UserBearer`

| Case | Setup and request | Expected |
|---|---|---|
| Success | Register and log in as user A. Create two tasks as A: one active tagged `Research` with title `Finish quality report`, and one completed task. `GET /api/tasks` with A's bearer token. | `200`; JSON array contains both A-owned tasks with their IDs, titles, tags, and completion states. |
| Filter/search success | As A, request tasks with `status_filter=active`, `tag=research`, and `q=quality`. | `200`; JSON array contains only the matching active task. |
| Empty result | As A, search for a title fragment that does not exist. | `200`; JSON `[]`. |
| Missing token | Request without `Authorization`. | `401`; JSON `detail`. |
| Invalid/expired token | Request with a malformed token, then with an expired token. | Each returns `401`; JSON `detail`. |
| Invalid filter | Request using `status_filter=unknown` with A's valid token. | `422`; JSON `detail`. |
| User isolation | Register/log in as user B, then list tasks using B's valid token after A's tasks exist. | `200`; JSON array does not contain any A-owned task. |

### 2. `POST /api/tasks` — `UserBearer`

| Case | Setup and request | Expected |
|---|---|---|
| Success | Register/log in as user A. Submit `{"title":"Finish quality report","description":"Review results","tag":"Research","due_date":"2026-11-12","priority":"high"}` with A's valid token. | `201`; JSON task has a generated ID, submitted values, and `completed: false`; task is owned by A. |
| Invalid data | With a valid token, submit a blank title; separately submit malformed `due_date` and unsupported priority. | Each returns `422`; JSON `detail`; no invalid task is created. |
| Missing token | Submit an otherwise valid task without `Authorization`. | `401`; JSON `detail`; no task is created. |
| Invalid/expired token | Submit an otherwise valid task with a malformed token, then an expired token. | Each returns `401`; JSON `detail`; no task is created. |

### 3. `PUT /api/tasks/{task_id}` — `UserBearer`

| Case | Setup and request | Expected |
|---|---|---|
| Success | A creates a task. A sends updated task fields with title `Submit quality report` and `completed: true` to its ID. | `200`; response has the same ID and reflects the updated title and completion state. A subsequent list confirms the persisted update. |
| Invalid data | With A's valid token, update the task with a blank title or invalid priority. | `422`; JSON `detail`; original task remains unchanged. |
| Missing task | With A's valid token, update a nonexistent ID. | `404`; JSON `detail`. |
| Other user's task | B attempts to update A's task ID with B's valid token. | `404`; JSON `detail`; A's task remains unchanged. Do not reveal another user's task. |
| Missing token | Attempt a valid update without `Authorization`. | `401`; JSON `detail`. |
| Invalid/expired token | Attempt a valid update with a malformed token, then an expired token. | Each returns `401`; JSON `detail`. |

### 4. `DELETE /api/tasks/{task_id}` — `UserBearer`

| Case | Setup and request | Expected |
|---|---|---|
| Success | A creates a task and deletes its ID with A's valid token. | `204`; empty response body; subsequent task listing does not contain the task. |
| Missing task | Delete a nonexistent ID with A's valid token. | `404`; JSON `detail`. |
| Other user's task | B attempts to delete A's task ID using B's valid token. | `404`; JSON `detail`; A's task remains available to A. |
| Missing token | Attempt deletion without `Authorization`. | `401`; JSON `detail`; task remains. |
| Invalid/expired token | Attempt deletion with a malformed token, then an expired token. | Each returns `401`; JSON `detail`; task remains. |

### 5. `GET /api/tags` — `UserBearer`

| Case | Setup and request | Expected |
|---|---|---|
| Success | A requests tags with a valid token after creating tasks with built-in tags and custom tag `Research`. | `200`; JSON array includes `School`, `Work`, `House`, `Personal`, `Other`, and `Research`. |
| Custom tag removal | A deletes the last A-owned task using `Research`, then requests tags again. | `200`; response no longer includes `Research`. |
| Missing token | Request without `Authorization`. | `401`; JSON `detail`. |
| Invalid/expired token | Request with a malformed token, then with an expired token. | Each returns `401`; JSON `detail`. |

### 6. `POST /api/auth/register` — public

| Case | Request | Expected |
|---|---|---|
| Success | Submit a unique valid `email`, `password`, and `display_name`. | `201`; JSON contains the account ID, email, and display name; it does not expose the plaintext password or password hash. |
| Invalid input | Submit a malformed email or a missing/blank password. | `422`; JSON `detail`; account is not created. |
| Duplicate account | Register the same email twice. | Second request returns `409`; JSON `detail`; there is only one account for that email. |

### 7. `POST /api/auth/login` — public

| Case | Request | Expected |
|---|---|---|
| Success | Submit the credentials for an account created through registration. | `200`; JSON contains a non-empty signed user access token usable as `UserBearer`; response does not expose the password/hash. |
| Wrong password | Submit a registered email with an incorrect password. | `401`; JSON `detail`; no access token is returned. |
| Unknown account | Submit credentials for an unregistered email. | `401`; JSON `detail`; no access token is returned. |
| Missing credentials | Omit email or password. | `422`; JSON `detail`. |

### 8. `GET /api/users/me` — `UserBearer`

| Case | Setup and request | Expected |
|---|---|---|
| Success | Register/log in as A and request the endpoint using A's valid token. | `200`; JSON contains A's ID, email, and display name; no password/hash fields. |
| Missing token | Request without `Authorization`. | `401`; JSON `detail`. |
| Invalid/expired token | Request with a malformed token, then an expired token. | Each returns `401`; JSON `detail`. |

### 9. `PATCH /api/users/me` — `UserBearer`

| Case | Setup and request | Expected |
|---|---|---|
| Success | A sends `{"display_name":"A Updated"}` with A's valid token, then reads `/api/users/me`. | `200`; response and subsequent read contain `display_name: "A Updated"` and A's ID/email; no password/hash fields. |
| Invalid input | With a valid token, submit an invalid or blank display name. | `422`; JSON `detail`; profile remains unchanged. |
| Missing token | Submit a valid profile update without `Authorization`. | `401`; JSON `detail`; profile remains unchanged. |
| Invalid/expired token | Submit a valid update with a malformed token, then an expired token. | Each returns `401`; JSON `detail`; profile remains unchanged. |

### 10. `GET /api/admin/users` — `AdminBearer`

| Case | Setup and request | Expected |
|---|---|---|
| Success | Provision an admin account using the documented test fixture, create at least one regular user via registration, and request with the admin's valid token. | `200`; JSON array includes the regular user's ID/email and excludes all password/hash fields. |
| Missing token | Request without `Authorization`. | `401`; JSON `detail`. |
| Invalid/expired token | Request with a malformed token, then an expired token. | Each returns `401`; JSON `detail`. |
| Insufficient role | Request with a valid regular user's `UserBearer` token. | `403`; JSON `detail`; user list is not returned. |

## End-to-end workflow

Run this workflow as an additional acceptance check: register user A, log in, use the returned token to read and update A's profile, create/list/update/complete/delete A's task, and list tags. Verify each step's status and response content against the cases above. Register and log in user B; verify B cannot read, update, or delete A's task by ID. Verify an unauthenticated request to each protected route is rejected.

## Results record

Run all cases above using the same acceptance suite for each stage. Record expected and actual status/body assertions, total passed/failed counts, command, commit/revision, and test database setup. A stage is not a pass if any required case is skipped or missing.

| Stage | Command and revision | Expected | Actual |
|---|---|---|---|
| Stage 1 — FastAPI + SQLite | Record when the complete suite is implemented and run. | Every case above passes. |  |
| Stage 2 — SQLAlchemy/Pydantic | Record when Stage 2 and the same complete suite are available. | Every case above passes | |

