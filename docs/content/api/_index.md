---
title: "API reference"
description: "HTTP API endpoints for the local Tamana FastAPI application."
---

The API is served by the local FastAPI application at `http://127.0.0.1:8000`. The Pages demo is static and does not expose these API routes.

All request and response bodies use JSON. Invalid requests return a JSON object with a `detail` string. See the [task endpoints]({{< relref "api/tasks.md" >}}) and [tag endpoint]({{< relref "api/tags.md" >}}) for parameters and examples.

| Method | Path | Success response |
|---|---|---|
| `GET` | `/api/tasks` | `200 OK`, array of tasks |
| `POST` | `/api/tasks` | `201 Created`, created task |
| `PUT` | `/api/tasks/{task_id}` | `200 OK`, updated task |
| `DELETE` | `/api/tasks/{task_id}` | `204 No Content` |
| `GET` | `/api/tags` | `200 OK`, array of tag names |

Interactive API documentation for the running local app is available at `/docs`; its OpenAPI JSON is at `/openapi.json`.
