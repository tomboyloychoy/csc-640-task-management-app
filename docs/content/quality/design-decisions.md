---
title: "Design decisions"
description: "Document rationale, alternatives, consequences, and verification."
---

Good design documentation explains why a choice fits a product need, what alternatives were considered, what the choice costs, and which evidence would prompt a change. A framework or language does not guarantee quality by itself.

## Current baseline: FastAPI and direct SQL

The backend uses Python, FastAPI, SQLite, and parameterized SQL. SQLite avoids a separate database service for local development; direct SQL keeps queries and constraints visible while the data model is small.

**Benefits:** Low setup overhead, explicit query behavior, and the ability to isolate tests with a temporary database.

**Costs and risks:** Validation, SQL, row mapping, and route logic need consistent conventions. As relationships and features grow, repeated persistence code and schema changes may become harder to maintain.

**Evidence:** The implementation uses bound parameters for SQL values and SQLite constraints for priority and completion. Current tests cover selected CRUD, filtering, and invalid input paths, but not migrations, restart persistence, or all boundary cases.

**Revisit when:** Persistence concerns spread across routes, the schema gains relationships, migrations are needed, or multiple database backends become a requirement.

## Decision record format

For future architectural or product decisions, capture:

1. **Context:** The user need, quality criterion, and constraints.
2. **Options:** Plausible alternatives, including keeping the current approach.
3. **Decision and rationale:** Why the chosen option best fits the current context.
4. **Consequences:** Benefits, costs, risks, and operational implications.
5. **Verification:** Evidence needed to confirm the expected outcome.
6. **Revisit trigger:** Conditions that would justify changing the decision.
