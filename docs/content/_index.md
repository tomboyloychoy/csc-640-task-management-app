---
title: "Engineering quality at Tamana"
description: "Practical guidance for defining quality, verifying behavior, and making sustainable engineering decisions."
---

This guide helps team members build and maintain Tamana as a dependable task-management product. Quality is not a final checklist: it starts with user needs, shapes architecture and implementation, and is verified with evidence throughout development.

## Engineering practices

- [Quality criteria]({{< relref "quality/criteria.md" >}}): define measurable expectations for product behavior and quality attributes.
- [Verification and evidence]({{< relref "quality/verification.md" >}}): understand current test coverage, observed results, and remaining risks.
- [Design decisions]({{< relref "quality/design-decisions.md" >}}): document rationale, alternatives, consequences, and revisit triggers.
- [Technology evolution]({{< relref "quality/stages.md" >}}): assess the current direct-SQL baseline and the proposed SQLAlchemy/Pydantic direction.

## Product and implementation

The local backend uses Python, FastAPI, and SQLite with direct SQL. The [API reference]({{< relref "api/_index.md" >}}) describes implemented routes; [getting started]({{< relref "getting-started.md" >}}) explains how to run the product and its tests.

The GitHub Pages version is a static demo that stores tasks in each visitor's browser. It does not connect to the local FastAPI API or share data between visitors. Verification results must identify which version and environment they apply to.
