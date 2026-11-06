---
title: "Quality criteria and product evidence"
description: "Turn product needs into measurable acceptance criteria."
---

Quality criteria make product expectations clear enough to guide implementation and verification. A useful criterion states an observable outcome, its conditions and limits, and how the team will collect evidence.

## Initial criteria for Tamana

These criteria are an initial working baseline. The evidence column distinguishes tested behavior from gaps; update it as verification work is completed.

| Concern | Acceptance criterion | Verification approach | Current evidence |
|---|---|---|---|
| Functional correctness | A valid task can be created, listed, edited, completed, and deleted; API responses reflect each change. | API lifecycle integration tests using an isolated database. | The existing tests cover representative create/update/complete/delete flows. |
| Input validation | Invalid titles, dates, priorities, filters, and field types receive a clear client error without corrupting stored data. | Boundary and invalid-input tests for each field. | Blank title, invalid date, and unknown status filter are covered; more boundaries and types remain untested. |
| Data integrity | User-supplied values do not change SQL query structure, and supported search characters are treated literally. | Parameter-binding review plus adversarial input tests. | Queries use bound SQL parameters; literal `%` and `_` search is tested. |
| Data persistence | Backend tasks remain available after the server restarts. | File-backed database integration test across separate app lifespans. | Not established by the current test suite. |
| Usability and accessibility | Core task actions can be completed using a keyboard and expose meaningful names and state to assistive technology. | Keyboard walkthrough, accessibility tooling, and manual assistive-technology review. | Not established by the API tests. |
| Maintainability | A new contributor can install, run, and verify the app using the project documentation. | Onboarding walkthrough in a clean environment. | Setup instructions exist; a clean-environment walkthrough has not been recorded. |

## Make a criterion testable

“Users can organize tasks” is too broad. Make the expectation observable:

1. A task may have a custom tag up to 32 characters.
2. Filtering by a tag is case-insensitive.
3. The tag list includes built-in tags and custom tags used by existing tasks.
4. Removing the last task with a custom tag removes that tag from the task-derived list.

The implementation and tests provide evidence for the first three behaviors, but the removal behavior should have a dedicated test. This difference matters: code inspection and test results support related, but distinct, claims.

## Team review prompts

For each new requirement, ask:

- Who is affected if this behavior fails?
- What should happen at the boundary and on invalid input?
- Which test or review would reveal a defect?
- What uncertainty remains after the check passes?
