---
title: Fixture QA verification v3 missing transferable principles
qa_schema: 3
status: active
draft_status: n/a
qa_status: verified
risk: Medium
created_at: 2026-08-04
updated_at: 2026-08-04
references:
  - "_docs/qa/Workflow/reflection-missing/test-plan.md"
  - "_docs/intent/Workflow/reflection-missing/decision.md"
related_issues: []
related_prs: []
fixture_path: "_docs/qa/Workflow/reflection-missing/verification.md"
---

# Fixture QA verification v3 missing transferable principles

## Summary

The fixture is intentionally invalid: qa_schema 3 without a Transferable
Principles section.

## Verification Verdict

Verdict: PASS

## Commands Run

| Command / Test | Result | Notes |
| --- | --- | --- |
| `deno run --allow-read scripts/validate-qa.ts --fixture _meta/validator-fixtures/qa/invalid/v3-missing-transferable-principles.md` | FAIL | Missing reflection section must be rejected. |

## Automated Test Results

- AC-001: Represented by fixture execution.

## Manual QA Results

- Reflection review was silently skipped, which this fixture reproduces.

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
