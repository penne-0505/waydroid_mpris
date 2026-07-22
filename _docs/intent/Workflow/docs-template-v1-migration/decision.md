---
title: Docs template v1 migration decisions
status: active
draft_status: n/a
intent_schema: 2
created_at: 2026-07-22
updated_at: 2026-07-22
references:
  - "_docs/plan/Workflow/docs-template-v1-migration/plan.md"
  - "_docs/qa/Workflow/docs-template-v1-migration/test-plan.md"
  - "_docs/reference/Workflow/docs-template-v1-migration.md"
related_issues: []
related_prs: []
---

# Docs template v1 migration decisions

## Context

この repository は pre-v1 の template B を基に project 固有の runtime、docs、CI、
workflow records を追加している。U を wholesale copy すると project guidance を失い、
P を基準に差分だけ追うと upstream provenance と削除意図を取り落とす。

## Decisions

### DEC-001: Freeze one provenance lane

- **What**: B、clean cutoff P、annotated tag を peel した U full SHA の三者だけを比較する。
- **Why**: moving tip や別 branch を混ぜると、何を採用した migration か再現できない。
- **Change freedom**: 同じ三者 tree を再現できる限り、inventory 生成手段は変更できる。

### DEC-002: Merge by ownership and preserve project behavior

- **What**: reusable template filesは pathwise に apply / merge し、Waydroid runtime、
  Arch-family setup、ADB target-safe helpers、project README guidance を保持する。
- **Why**: project の公開可能性は Arch-family での再現性と fail-closed ADB 選択に
  依存し、template 更新がその契約を変更してはならない。
- **Change freedom**: project contract が残る限り、root docs と CI の構成は変更できる。

### DEC-003: Separate compatibility from strict schema adoption

- **What**: U validators の legacy-compatible mode を先に通し、新規 migration docs は
  schema 2 を使う。既存 docs の一括 schema conversion は別 verdict とする。
- **Why**: provenance 更新と semantic document rewrite を同時に行うと、回帰原因と
  rationale change を分離できない。
- **Change freedom**: compatibility を保つ限り、strict conversion の順序と単位は
  follow-up で決められる。

### DEC-004: Constrain deletion and exclude template-self history

- **What**: remove は B=P exact、project refs なし、post-cutoff changes なし、U で
  absent/replaced、owner-authorized の全条件を満たす path に限る。U の lifecycle
  self-audit docs は import しない。
- **Why**: upstream deletion は project record の削除権限ではなく、履歴の混入も
  downstream の active guidance を曖昧にする。
- **Change freedom**: 条件を満たさない path は keep / defer / superseded history として
  安全に残せる。

### DEC-005: Make inventory closure mechanically complete

- **What**: resolution vocabulary と final disposition を分離し、initial union に加え
  migration-created pathsを manifest 化して final raw diff の missing path を 0 にする。
- **Why**: migration 中に生まれた lock、QA、local lint/fixture fixes が inventory 外だと、
  最終 diff の説明責任が欠ける。
- **Change freedom**: path 集合の比較が完全なら、表や検査 command の形式は変更できる。

### DEC-006: Adopt bounded workflow guardrails without template-self records

- **What**: U の lifecycle hook behavior を採用し、短い prompt audit、write audit、
  closure evidence check を project migration intent へ直接 anchor する。
- **Why**: template-self lifecycle history を import せずに hook の非自明な prompting
  境界を保守でき、存在しない upstream intent への active code reference を避けられる。
- **Change freedom**: evidence、scope、closure の三境界を保つ限り、hook event、文言、
  matcher、実装構造は変更できる。

## Consequences / Impact

- docs workflow と CI は更新されるが runtime implementation は変更しない。
- strict schema adoption を defer する場合も compatibility PASS と混同しない。
- exact lock は compatibility verification 後にだけ作成する。

## Quality Implications

- branch mixing、blind replacement、premature lock、bulk schema rewrite を review で拒否する。
- paired skill tree、hook behavior、scope behavior、project regression を独立に確認する。
- full markdownlint は既存 baseline 失敗を局所修正し、global rule disable は行わない。

## Intent-derived Invariants

- INV-001 (from DEC-001): final lock の tag と commit は同じ upstream tree を指す。
- INV-002 (from DEC-002): runtime、helper、packaging、project test paths は P と同一である。
- INV-003 (from DEC-004): lifecycle-self-audit docs は final tree に存在しない。
- INV-004 (from DEC-005): final raw diff に inventory / artifact manifest 未掲載 path がない。

## Enforced in (optional)

- DEC-001: `docs-template.lock.json` と migration verification の provenance commands。
- DEC-002 / INV-002: P との path hash / diff review と project regression commands。
- DEC-003: migration verification の compatibility / strict schema verdict。
- DEC-004 / INV-003: inventory disposition と final path search。
- DEC-005 / INV-004: final diff reconciliation command。
- DEC-006: `scripts/agent-workflow-hook.mjs` と hook fixture / smoke tests。

## Rollback / Follow-ups

isolated branch を破棄すれば P へ復帰できる。strict schema conversion を defer した場合は、
project docs の意味を個別 review できる別 task として扱う。
