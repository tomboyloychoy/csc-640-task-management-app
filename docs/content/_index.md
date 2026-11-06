---
title: "Learn software quality with Tamana"
description: "A practical guide to quality criteria, evidence, verification, design decisions, and technology trade-offs."
---

This site is a learning guide for future team members who are new to building quality software. It uses Tamana—a task-management application—as a concrete case study. Instead of treating quality as a checklist at the end, follow how requirements become testable criteria, design choices, implementation evidence, and verification.

## Learn the quality practice

- [Quality criteria]({{< relref "quality/criteria.md" >}}): turn user needs into observable, testable expectations.
- [Verification and evidence]({{< relref "quality/verification.md" >}}): see what the current tests establish—and what remains unverified.
- [Design decisions]({{< relref "quality/design-decisions.md" >}}): understand the reasoning and trade-offs behind Stage 1.
- [Stage comparison]({{< relref "quality/stages.md" >}}): compare direct SQL with the planned SQLAlchemy and Pydantic approach.

## Use the product as evidence

Tamana's Stage 1 backend uses Python, FastAPI, and SQLite with direct SQL queries. The [API reference]({{< relref "api/_index.md" >}}) describes its actual routes; [getting started]({{< relref "getting-started.md" >}}) explains how to run the app and reproduce the tests.

The GitHub Pages version is a static demo that stores tasks in each visitor's browser. It does not connect to the local FastAPI API or share data between visitors. Be clear about which version an observation or test applies to.
