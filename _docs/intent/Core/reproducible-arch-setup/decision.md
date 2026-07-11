---
title: "Intent: Reproducible Arch setup boundary"
status: active
draft_status: n/a
created_at: 2026-07-11
updated_at: 2026-07-11
references:
  - "_docs/plan/Core/reproducible-arch-setup/plan.md"
  - "_docs/qa/Core/reproducible-arch-setup/test-plan.md"
related_issues: []
related_prs: []
---

# Intent: Reproducible Arch setup boundary

## Context

bridge MVP は実環境で動作しているが、host native dependencies、Android SDK discovery、ADB install target、成功判定が maintainer environment に依存している。今回の公開境界は community contribution infrastructure ではなく、Arch 系の第三者が source checkout から挙動を再現できることである。

## Decision

- 対応環境は Arch 系 Linux とし、中級者が Android SDK / Waydroid を自分で導入できる前提を置く。
- repo は SDK の自動導入ではなく、environment-first discovery、限定的 fallback、tool preflight、actionable error を提供する。
- installed latest platform / build-tools を既定とし、検証済み version を文書化し、environment override で固定可能にする。
- ADB target は explicit `--device`、Waydroid auto-discovery の順で決定し、曖昧または非 ready なら fail closed する。
- debug signing mismatch は app / data / permission を自動削除せず、手動 recovery を案内する。
- CI は live Waydroid を再現せず、host tests / static checks と可能な build boundary を扱い、live E2E は manual verification に残す。

## Alternatives

- SDK / JDK を script が自動導入する案は、AUR helper、license、system ownership を repo が引き受けるため不採用。
- platform / build-tools を一版へ hard pin する案は、bit-identical artifact を今回の目標にしないため不採用。override と known-good record で安定性を確保する。
- install で任意の ready ADB device を選ぶ案は、別端末への誤導入を起こすため不採用。
- signature mismatch 時に自動 uninstall する案は、notification-listener permission と app state を破壊するため不採用。

## Rationale

再現性に必要なのは環境構築の全面自動化ではなく、前提の明示、deterministic target selection、失敗原因の観測可能性、検証済み境界である。Arch 系へ対象を絞ることでnative dependency名を具体化しつつ、Android SDK自体の管理は利用者へ残す。

## Consequences / Impact

- Arch 系利用者は README から必要 package / SDK components と成功条件を確認できる。
- scripts は既存 overrides を保ちつつ、個人 path を持たなくなる。
- install / settings CLI に `--device` が加わり、auto-discovery failure は明示的な停止になる。
- CI時間は増えるが、runtime regression がdocs CIを通過する状態を解消する。

## Quality Implications

- SDK root / selected versions / missing tools が診断可能でなければならない。
- target ambiguity や unauthorized / offline state は安全側へ停止しなければならない。
- destructive recovery を便利機能として追加してはならない。
- docs は検証済み環境と未検証範囲を混同してはならない。

## Intent-derived Invariants

- INV-001: Android build は maintainer 固有の absolute path を既定値に持たない。
- INV-002: SDK / platform / build-tools の明示 override は一般配置の自動探索より優先される。
- INV-003: install / settings helpers は Waydroid target を一意に決定できない場合、別 ADB device を選ばず停止する。
- INV-004: signature mismatch recovery は既存 companion を自動 uninstall しない。
- INV-005: SDK / JDK / Android Studio の導入、license受諾、release signing は利用者の明示操作として残る。
- INV-006: live Waydroid を持たない automated checks と、live manual verification の証拠を分離する。

## Enforced in

- INV-001 / INV-002: Android build helper tests と build script preflight。
- INV-003: ADB target resolver tests と install / settings helper integration tests。
- INV-004: install failure handling test と operator documentation。
- INV-005 / INV-006: Plan Non-Goals、README、QA matrix、workflow diff review。

## Rollback / Follow-ups

scripts / docs / workflow changesのみを戻せる。rollback は installed companion、notification-listener permission、user serviceを変更しない。
