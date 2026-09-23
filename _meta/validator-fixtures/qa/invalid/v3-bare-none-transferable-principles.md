---
title: Fixture QA verification v3 with bare none reflection
qa_schema: 3
status: active
draft_status: n/a
qa_status: verified
risk: Medium
created_at: 2026-08-04
updated_at: 2026-08-04
references:
  - "_docs/qa/Workflow/reflection-bare-none/test-plan.md"
  - "_docs/intent/Workflow/reflection-bare-none/decision.md"
related_issues: []
related_prs: []
fixture_path: "_docs/qa/Workflow/reflection-bare-none/verification.md"
---

# Fixture QA verification v3 with bare none reflection

## Summary

The fixture is intentionally invalid: the Transferable Principles section
contains a bare None without a reason, which cannot be distinguished from a
silent skip.

## Verification Verdict

Verdict: PASS

## Commands Run

| Command / Test | Result | Notes |
| --- | --- | --- |
| `deno run --allow-read scripts/validate-qa.ts --fixture _meta/validator-fixtures/qa/invalid/v3-bare-none-transferable-principles.md` | FAIL | Bare None must be rejected. |

## Automated Test Results

- AC-001: Represented by fixture execution.

## Manual QA Results

- Reflection was answered mechanically, which this fixture reproduces.

## Acceptance Criteria Coverage

- AC-001: Covered by validator fixture execution.

## Decision Conformance

- DEC-001: The fixture preserves the why-first QA structure.

## Invariant Coverage

None

## Deferred / Not Covered

- None

## Residual Risks

None

## Follow-up TODOs

- None

## Transferable Principles

None
