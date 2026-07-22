---
title: Docs template v1 migration plan
status: active
draft_status: n/a
created_at: 2026-07-22
updated_at: 2026-07-22
references:
  - "_docs/intent/Workflow/docs-template-v1-migration/decision.md"
  - "_docs/qa/Workflow/docs-template-v1-migration/test-plan.md"
  - "_docs/reference/Workflow/docs-template-v1-migration.md"
related_issues: []
related_prs: []
---

# Docs template v1 migration plan

## Overview

`waydroid_mpris` が legacy template B から取り込んだ docs workflow を、
upstream tag `v1.0.0` の full commit U へ provenance-locked migration する。
P 固有の Arch-family setup、Waydroid runtime、ADB target-safe helper、CI の
runtime job は保持し、template lifecycle history は downstream へ移さない。

## Scope

- B to U と B to P の全 path を二軸分類し、resolution と final disposition を
  inventory に記録する。
- U の validators、fixtures、standards、templates、paired skills、hooks、CI を
  reusable distribution として pathwise に統合する。
- correct document type の `intent_schema` / `qa_schema`、unknown-field warning、
  duplicate frontmatter key rejection を fixture で固定する。
- compatibility migration と strict schema adoption を別々に検証する。
- final diff と inventory / migration-created manifest の全件対応を確認する。

## Non-Goals

- U より後の moving branch tip や unmerged branch を provenance lane に混ぜない。
- U の `lifecycle-self-audit` plan / intent / QA history を project docs にしない。
- 既存の project intent / QA を意味変更なしに一括 schema conversion しない。
- Waydroid / ADB / installed user service を停止する disruptive live QA は行わない。
- `main`、remote refs、他 repository、active checkout を更新しない。

## Requirements

- **Functional**: `./scripts/check-docs.sh` が intent validator と hook tests を含み、
  scoped CI は cutoff P と `DD_SCOPE_DIFF_FILTER=ACMR` を使う。
- **Functional**: final `docs-template.lock.json` は source、tag `v1.0.0`、
  peeled full SHA U を記録する。
- **Non-Functional**: project runtime / packaging / helper / test filesは P と
  byte-identicalに保つ。
- **Non-Functional**: resolution は `apply`, `merge`, `keep`, `remove`, `defer`
  だけを用い、結果状態は別の disposition 列に記録する。

## Pre-implementation audit

- Evidence: P and B have identical blobs for the old validators and paired
  skills, while U adds intent validation, lifecycle hooks, and schema-2 rules。
- Disconfirming explanation checked: P might already contain equivalent local
  behavior under different paths. The three-way blob inventory and missing
  U-only paths do not support that explanation。
- Non-local effects: validator callers, CI scope, referenced docs, paired skill
  trees, hook operations, and runtime regression checks are separate QA gates。
- Durable solution: adopt the U workflow and fixtures rather than patching only
  current errors. Legacy compatibility lasts through this U migration and is
  not a permanent schema promise; strict conversion must be reviewed before a
  future template release removes legacy acceptance。
- Residual before implementation: local Quickstart anchors and historical
  workflow references may require project-specific merge or defer decisions。

## Tasks

1. P/B/U、dirty manifest、baseline validator/test result を凍結する。
2. 全 path inventory と削除 gate を確定する。
3. migration contract を Plan / Intent / QA / TODO に記録する。
4. U validators と fixtures を compatibility mode で取り込み、legacy docs を確認する。
5. standards、paired skills、hooks、CI、root guidance を pathwise に統合する。
6. strict schema target を判定し、lock を最後に書く。
7. docs / hooks / paired / project regression / raw diff reconciliation を実行する。

## QA Plan

- QA document: `_docs/qa/Workflow/docs-template-v1-migration/test-plan.md`
- Risk level: High
- Validator / static: unscoped / scoped docs、fixtures、hooks、smoke、markdownlint。
- Regression: Python unit/compile、shell syntax、service dry-run、Android build と
  non-invasive ADB helper checks。
- Diff review: DEC-001 through DEC-005 と P の project boundary を照合する。
- Recovery: isolated branch を破棄すれば P に戻る。main / remote は未変更に保つ。

## Deployment / Rollout

isolated worktree で単一 commit を作成する。push、main update、remote ref update は
行わない。compatibility PASS 後に lock を最終 write とし、その後は verification
以外の migration content を変更しない。
