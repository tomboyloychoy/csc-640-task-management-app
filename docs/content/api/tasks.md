---
title: "Tasks"
description: "List, create, update, and delete tasks."
---

Base URL for local development: `http://127.0.0.1:8000`.

## Task object

Task responses contain these fields:

| Field | Type | Description |
|---|---|---|
| `id` | integer | Database-generated task identifier. |
| `title` | string | Required, non-empty after trimming; maximum 160 characters. |
| `description` | string | Optional note; defaults to `""`; maximum 1,000 characters. |
| `tag` | string | Defaults to `"Personal"`; maximum 32 characters. Built-in tags are School, Work, House, Personal, and Other. |
| `due_date` | string or `null` | Optional ISO date in `YYYY-MM-DD` format. |
| `priority` | string | `low`, `normal`, or `high`; defaults to `normal`. |
| `completed` | boolean | Whether the task is complete; defaults to `false` on creation. |
| `created_at` | string | Creation timestamp in UTC ISO 8601 format. |

## List tasks

`GET /api/tasks`

Optional query parameters:

| Parameter | Default | Description |
|---|---|---|
| `status_filter` | `all` | One of `all`, `active`, or `completed`. |
| `tag` | none | Filter by exact tag, case-insensitively. |
| `q` | empty | Search title and description. |

```sh
curl "http://127.0.0.1:8000/api/tasks?status_filter=active&tag=School&q=exam"
```

Returns an array of task objects. The default order is incomplete tasks first, then tasks with earlier due dates, with tasks that have no due date last.

## Create a task

`POST /api/tasks`

Required JSON field: `title`. All other fields are optional.

```sh
curl -X POST "http://127.0.0.1:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Prepare project presentation",
    "description": "Review the slides and practice",
    "tag": "School",
    "due_date": "2026-11-20",
    "priority": "high"
  }'
```

Returns the created task with status `201 Created`.

## Update a task

`PUT /api/tasks/{task_id}`

Send the task fields to update. `title` is required. Omitted `description`, `tag`, `due_date`, and `priority` use their defaults; omitted `completed` is set to `false`.

```sh
curl -X PUT "http://127.0.0.1:8000/api/tasks/1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Prepare project presentation",
    "description": "Slides reviewed",
    "tag": "School",
    "due_date": "2026-11-20",
    "priority": "normal",
    "completed": true
  }'
```

Returns the updated task with status `200 OK`.

## Delete a task

`DELETE /api/tasks/{task_id}`

```sh
curl -i -X DELETE "http://127.0.0.1:8000/api/tasks/1"
```

Returns `204 No Content` on success.

## Errors

| Status | Meaning |
|---|---|
| `400 Bad Request` | The request body is not valid JSON. |
| `404 Not Found` | The task ID does not exist (update or delete). |
| `422 Unprocessable Entity` | Invalid field value, invalid filter, or request body is not a JSON object. |

Error responses have the form `{"detail": "..."}`.
