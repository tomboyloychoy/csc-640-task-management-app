---
title: "Verification and evidence"
description: "Interpret current test results and prioritize verification gaps."
---

Verification determines whether the implementation meets defined expectations. Evidence is specific to the check, code version, and environment that produced it; a passing test is not a guarantee of overall product quality.

## Observed test result

On 2026-11-06, running `python -m pytest -q` reported **2 passed** and **1 deprecation warning** in the available development environment. The warning concerns Starlette's `TestClient` integration with `httpx`; the run completed successfully, but the dependency warning should be reviewed.

The tests in `tests/test_api.py` use a temporary SQLite database and cover representative task lifecycle operations, custom tags, tag and text search, active/completed filters, selected invalid inputs, literal search wildcard characters, and not-found deletion.

This is evidence for the tested cases only. It does not establish complete API correctness, accessibility, performance, restart persistence, or production readiness. Re-run checks against the version being evaluated; results may differ across code and environments.

## Verification record

For important checks, record:

- **Criterion:** What expected behavior or quality property is being checked?
- **Version and environment:** Which revision, runtime, and relevant configuration?
- **Method:** Test, review, measurement, or user evaluation?
- **Observed result:** What actually happened, including failures and warnings?
- **Conclusion and limits:** What does this evidence support, and what does it not establish?
- **Follow-up:** Which risk or defect should be addressed next?

## Priority verification gaps

- Add boundary tests for maximum field lengths, unsupported priorities, non-object JSON, wrong field types, and non-boolean completion values.
- Test combined status, tag, and text filters, no-match results, and removal of a custom tag after its last task is deleted.
- Verify persistence across separate app lifespans using a temporary file-backed SQLite database.
- Review accessible keyboard flows and screen-reader feedback in the browser app.
- Define representative workload and latency targets before measuring performance.

Do not report a proposed check as completed evidence. When a check fails, preserve the reproduction, connect it to the violated criterion, fix the root cause, and add regression coverage.
