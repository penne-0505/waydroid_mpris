---
title: "QA Test Plan: Docs template v1 migration"
status: active
draft_status: n/a
qa_status: planned
risk: High
qa_schema: 2
created_at: 2026-07-22
updated_at: 2026-07-22
references:
  - "_docs/intent/Workflow/docs-template-v1-migration/decision.md"
  - "_docs/plan/Workflow/docs-template-v1-migration/plan.md"
  - "_docs/reference/Workflow/docs-template-v1-migration.md"
related_issues: []
related_prs: []
---

# QA Test Plan: `Docs template v1 migration`

## Source of Intent

- TODO: `Workflow-Chore-19`
- Plan: `_docs/plan/Workflow/docs-template-v1-migration/plan.md`
- Intent: `_docs/intent/Workflow/docs-template-v1-migration/decision.md`

## Quality Goal

U の reusable workflow を取り込みつつ、project behavior と provenance を保持し、
compatibility / strict schema / final diff の各 verdict を証拠から分離して判定する。

## Acceptance Criteria

- AC-001: P/B/U、全 inventory path、resolution、disposition が再現可能である。
- AC-002: U の reusable files と learned validator requirements が統合される。
- AC-003: compatibility と strict schema の verdict、および exact final lock が整合する。
- AC-004: project runtime、Arch setup、ADB helpers、tests/build/install が退行しない。
- AC-005: docs、lint、fixtures、hooks、smoke、paired skills の全 gate が通る。
- AC-006: final raw diff の inventory missing path が 0 件である。

## Decision Review Scope

- DEC-001: selected B/P/U lane と tag peeling が provenance evidence と一致する。
- DEC-002: project runtime と guidance が wholesale replacement されていない。
- DEC-003: strict schema defer を compatibility PASS に含めていない。
- DEC-004: deletion gate と lifecycle exclusion が守られる。
- DEC-005: resolution と disposition が混同されず diff coverage が完全である。
- DEC-006: hook guardrails が absent template-self intent を参照しない。

## Intent-derived Invariants

- INV-001: tag / commit lock consistency。
- INV-002: runtime / helper / packaging / project test path preservation。
- INV-003: lifecycle-self-audit absence。
- INV-004: final raw diff inventory coverage。

## Risk Assessment

- Risk level: High
- Risk rationale: validators、CI、skills、hooks、docs schema と provenance の migration。
- Regression risk: project runtime guidance の消失、legacy docs の誤 reject、under-scoped CI。
- Data safety risk: isolated worktree の Git tracked files のみ。runtime state は変更しない。
- Security / privacy risk: hooks の command / matcher と secret 非出力を review する。
- UX risk: contributor / agent guidance が矛盾すると後続作業が誤る。
- Agent misbehavior risk: branch mixing、blind replacement、premature lock、bulk schema edit、
  template-self history import、global lint disable。

## Test Strategy

- Unit: validator fixtures、hook tests、project Python tests。
- Integration: unscoped / scoped docs wrapper、paired skill diff、service dry-run、Android build。
- E2E: non-invasive ADB resolution / doctor。disruptive restart は対象外。
- Manual QA: root guidance、deletion gate、compatibility / strict split、raw diff review。
- Validator / static check: Deno fmt、all validators、markdownlint、Python compile、shell syntax。
- Diff review: P and final tree、B/U inventory、lock provenance。

## Test Matrix

| ID | Source | Requirement / Optional Invariant | Test Type | Command / File | Expected Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001 | TODO | Three-way inventory | static | inventory generator / reference | no unclassified row | verified |
| AC-002 | TODO | Reusable v1 + learned fixtures | validator | `./scripts/check-docs.sh` | all fixtures pass | verified |
| AC-003 | TODO | Split verdict + lock | review | verification / `git -C ... rev-parse` | exact U | verified |
| AC-004 | TODO | Project preservation | regression | unit, compile, shell, build, helpers | no P regression | verified |
| AC-005 | TODO | Full workflow gates | static | docs, lint, hooks, smoke, paired | all pass | verified |
| AC-006 | TODO | Diff inventory coverage | static | `comm` over path manifests | zero missing | verified |
| INV-001 | intent | Tag / commit match | provenance | upstream `git -C` | U full SHA | verified |
| INV-002 | intent | Runtime paths unchanged | diff | `git diff P -- <paths>` | empty | verified |
| INV-003 | intent | No lifecycle self history | search | `find _docs -path '*lifecycle-self-audit*'` | no output | verified |
| INV-004 | intent | No missing diff paths | static | final reconciliation | zero missing | verified |

## Manual QA Checklist

- [ ] README / QUICKSTART / AGENTS preserve Arch-family and Waydroid commands。
- [ ] resolution is allowed vocabulary; disposition separately records result。
- [ ] no active `jj_workflow` or legacy skill instruction remains。
- [ ] lock was written only after compatibility checks。

## Regression Checklist

- [ ] 38 project unit tests and Python compile pass。
- [ ] shell syntax and generated user service dry-run pass。
- [ ] Android companion build and non-invasive ADB helpers pass or explicit environment residual is recorded。
- [ ] full CI-equivalent markdownlint passes without global suppression。

## High-risk Checklist

- [x] Rollback is isolated branch removal; main / remote stay unchanged。
- [x] Recovery is restoring the clean P worktree / branch state。
- [x] Data safety excludes disruptive Waydroid / service operations。
- [x] Security review covers imported hook commands and secret handling。
- [x] Hooks and imported scripts are reviewed before trust。
- [x] Lock advancement and deletion have explicit gates。

## Out of Scope

- Disruptive live Waydroid restart and authorization transition QA。
- Bulk semantic schema rewrite of historical project docs。
- Push, main update, remote ref update。

## Open Questions

- None。
