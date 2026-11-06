---
title: "Tamana documentation"
description: "Project and API documentation for Tamana."
---

Tamana is a task-management app with a Python, FastAPI, and SQLite Stage 1 backend. The backend uses direct SQL queries; it does not use an ORM or Pydantic request models.

## Documentation

- [Getting started]({{< relref "getting-started" >}}): run the app locally and explore its API.
- [API reference]({{< relref "api/_index.md" >}}): endpoint overview, task schema, and response conventions.

## Hosting note

The GitHub Pages website is a static demo. It stores tasks in each visitor's browser and does not connect to the Python API or share data with other visitors. Run the FastAPI app locally to use the SQLite-backed API.
