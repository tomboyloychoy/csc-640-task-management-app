---
title: "Technology evolution: benefits and costs"
description: "Evaluate the current direct-SQL baseline and proposed higher-level tools."
---

The current implementation uses direct SQL. SQLAlchemy, Pydantic, and OpenSpec are proposed future tools, not implemented or evaluated in this repository. The comparison below describes likely trade-offs, not measured outcomes.

## Current and proposed approaches

| Concern | Current: FastAPI + direct SQL + SQLite | Proposed: SQLAlchemy + Pydantic + OpenSpec |
|---|---|---|
| Learning and visibility | SQL, schema, and queries are explicit; contributors need to keep validation, row mapping, and query conventions consistent. | Models and typed schemas can establish shared structure; contributors must learn ORM sessions, schema boundaries, and the specification workflow. |
| Validation | Hand-written rules keep the baseline simple, but consistency and boundary coverage are the team's responsibility. | Pydantic can centralize typed request/response validation and error reporting; complex or duplicated schemas add maintenance cost. |
| Persistence | Direct SQL gives query-level control and SQLite has low local setup cost; repeated mapping and evolving relationships may increase complexity. | SQLAlchemy can organize persistence, relationships, and transactions; it introduces abstraction, session lifecycle concerns, and ORM-specific failure modes. |
| Change planning | Small changes can be implemented with little process overhead; requirement detail may be implicit unless documented. | OpenSpec could make change intent and acceptance criteria explicit; the team must maintain the added specification artifacts and review process. |
| Verification | Tests exercise direct database calls with a temporary SQLite database. | The ORM does not replace tests; fixtures must verify session isolation, transactions, generated queries, and API compatibility. |

## How to evaluate the proposal

To determine whether the proposed tools improve this product:

1. Select the same representative change for both approaches, such as adding a validated task field and a corresponding filter.
2. Define identical acceptance criteria, API compatibility expectations, and boundary tests.
3. Record implementation and review effort, defects found, test coverage, and contributor experience.
4. Compare the resulting code and observed test outcomes; distinguish measurements from opinions and predictions.
5. Keep the current approach if added abstraction and process do not justify their cost.

## Migration safeguards

Before adopting the proposed stack, define how existing API behavior and SQLite data will be preserved, how migrations will be tested, and how database sessions will be isolated in tests. Verify generated SQL for important query paths. Treat each tool as an aid to consistent practice—not as a substitute for clear requirements, review, or evidence.
