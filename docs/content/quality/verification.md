---
title: "Verification results"
description: "Starter template for documenting test evidence and remaining gaps."
---

> **Observed snapshot:** On 2026-11-06, `python -m pytest -q` reported **2 passed** and **1 deprecation warning** in the available environment. The warning came from Starlette's `TestClient` integration with `httpx`. Re-run the tests before relying on this result for a later version.

## What the current tests cover

The API tests exercise a task lifecycle, custom tags, tag and text search, active/completed filtering, selected invalid inputs, literal search wildcards, and not-found deletion.

This is evidence for those tested paths only. It does not show that the entire app is defect-free or establish accessibility, performance, restart persistence, or production readiness.

## Record a verification result

Use this template when adding evidence:

```text
Criterion:
Environment / version:
Verification method:
Command or test:
Observed result:
Pass, fail, or inconclusive:
Known limitations:
Follow-up:
```

## Future work

<!-- TODO: Add new test results, explain what they establish, and list important untested risks. Do not report a proposed test as a completed result. -->
