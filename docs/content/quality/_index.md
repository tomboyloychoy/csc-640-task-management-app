---
title: "Engineering quality"
description: "Practices for delivering reliable, usable, and maintainable software."
---

Software quality is the degree to which a product reliably meets user needs and remains safe to change. It is a team responsibility: requirements, design, implementation, testing, release, and operations all contribute.

## A practical quality loop

1. **Understand the user and risk.** Identify who depends on the behavior and what harm or cost a failure could cause.
2. **Define acceptance criteria.** State observable outcomes, boundaries, and error behavior before implementation.
3. **Choose a design that supports the criteria.** Make trade-offs explicit and keep complexity proportional to the product's needs.
4. **Verify at multiple levels.** Use focused tests, integration checks, code review, and usability evaluation as appropriate to the risk.
5. **Record evidence and uncertainty.** A passing check supports a specific claim; it does not prove the entire product is defect-free.
6. **Learn and improve.** Use failures, user feedback, and operational signals to prioritize the next change.

## Engineering guidance

- [Quality criteria and product evidence]({{< relref "quality/criteria.md" >}})
- [Verification results and gaps]({{< relref "quality/verification.md" >}})
- [Design decisions]({{< relref "quality/design-decisions.md" >}})
- [Technology evolution: benefits and costs]({{< relref "quality/stages.md" >}})
- [API reference]({{< relref "api/_index.md" >}})

The examples distinguish implemented behavior, verified behavior, and proposed work. Keep these categories separate when adding features or reporting progress.
