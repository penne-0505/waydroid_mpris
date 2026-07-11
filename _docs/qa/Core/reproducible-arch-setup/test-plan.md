---
title: "QA Test Plan: Reproducible Arch setup"
status: active
draft_status: n/a
qa_status: planned
risk: Medium
created_at: 2026-07-11
updated_at: 2026-07-11
references:
  - "_docs/intent/Core/reproducible-arch-setup/decision.md"
  - "_docs/plan/Core/reproducible-arch-setup/plan.md"
  - "_docs/qa/Core/reproducible-arch-setup/verification.md"
related_issues: []
related_prs: []
---

# QA Test Plan: Reproducible Arch setup

## Source of Intent

- TODO: `Core-Enhance-18`
- Plan: `_docs/plan/Core/reproducible-arch-setup/plan.md`
- Intent: `_docs/intent/Core/reproducible-arch-setup/decision.md`

## Quality Goal

Arch 系の新規 checkout で、利用者が既存 SDK と Waydroid を安全に結び付け、失敗時も不足前提または必要な operator action を特定できる。

## Acceptance Criteria

- AC-001: Arch 系依存、対応範囲、known-good toolchain、成功判定が利用者文書にある。
- AC-002: SDK解決とpreflightが個人pathなしで動作し、選択結果と不足toolを示す。
- AC-003: install / settingsがexplicit target / auto-discovery / fail-closedを実装する。
- AC-004: signature mismatchがnon-destructive guidanceになる。
- AC-005: CIがhost unit / compile / shell / service checksを実行する。
- AC-006: automated / live manual verification boundaryが記録される。

## Intent-derived Invariants

- INV-001: maintainer固有absolute pathを既定に持たない。
- INV-002: explicit SDK / tool version overridesがauto-discoveryより優先される。
- INV-003: target ambiguity / non-ready stateで別deviceへfallbackしない。
- INV-004: signature mismatchでautomatic uninstallしない。
- INV-005: SDK導入・license受諾・release signingを自動化しない。
- INV-006: automated evidenceとlive evidenceを混同しない。

## Risk Assessment

- Risk level: Medium
- Risk rationale: build / install workflow、ADB device selection、CIを変更する。
- Regression risk: 既存maintainer環境でbuild / installできなくなる可能性。
- Data safety risk: 誤target installまたはautomatic uninstallによるapp state / permission loss。
- Security / privacy risk: debug keyを追跡せず、secretをdocs / logへ含めない。
- UX risk: SDK探索失敗やnative dependency不足の案内が不十分になる可能性。
- Agent misbehavior risk: CI変更を理由にlive disruptive QAやSDK自動導入へscopeを拡張する可能性。

## Test Strategy

- Unit: SDK candidate precedence、version selection、missing tool、ADB target precedence / state mapping。
- Integration: shell helperをfake SDK / fake adbで実行し、exit / output / command targetを確認する。
- E2E: current Arch + Waydroidでbuild / install / settings / doctorをmanual確認する。
- Manual QA: signature mismatch guidanceはdestructive setupを作らず、known stderr mappingとdiff reviewで確認する。
- Validator / static check: unit suite、Python compile、shell syntax、workflow syntax review、docs validators。
- Diff review: SDK auto-install / license acceptance / automatic uninstall / release keyが追加されていないことを確認する。

## Test Matrix

| ID | Source | Requirement / Invariant | Test Type | Command / File | Expected Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001 | TODO | Arch dependencies / known-good / success criteria | docs review | README / Quickstart / usage guide | prerequisites and expected output are explicit | verified |
| AC-002 | TODO | portable SDK discovery and preflight | unit + integration | SDK helper tests; `./scripts/build-android-probe.sh` | no personal path; selected versions printed; build passes | verified |
| AC-003 | TODO | safe ADB target selection | unit + integration + manual | resolver tests; install/settings scripts | explicit/auto target works; ambiguity fails | verified |
| AC-004 | TODO | non-destructive signature mismatch | integration + diff review | install helper test | actionable guidance; no uninstall command | verified |
| AC-005 | TODO | runtime checks in CI | workflow review + local commands | `.github/workflows/docs-ci.yml` | host checks are present and pass locally | verified |
| AC-006 | TODO | clean-room/manual evidence split | QA review | verification | automated and live results are separate | verified |
| INV-001 | intent | no maintainer absolute SDK path | unit + repository search | build helper tests; SDK root assignment review | runtime defaults contain no personal path | verified |
| INV-002 | intent | explicit override precedence | unit | SDK helper tests | environment selections win | verified |
| INV-003 | intent | fail closed target selection | unit | ADB resolver tests | other ready devices are never selected | verified |
| INV-004 | intent | no automatic uninstall | integration + diff review | install helper test | failed install leaves app untouched | verified |
| INV-005 | intent | no environment ownership expansion | diff review | scripts / workflow | no install/license/release automation | verified |
| INV-006 | intent | evidence boundaries stay honest | qa-review | verification | unrun live checks are deferred | verified |

## Manual QA Checklist

- [ ] Current Arch environmentでAPK buildが成功し、SDK / platform / build-toolsが表示される。
- [ ] auto-discovered Waydroid targetへinstall / settings launchが成功する。
- [ ] `--device`で同じtargetを明示できる。
- [ ] `python scripts/doctor.py`がbridge readinessを報告する。

## Regression Checklist

- [ ] Existing 33 host tests pass。
- [ ] Fixture / live daemon imports and compiles。
- [ ] User service dry-run remains valid。
- [ ] Android debug keystore / build outputs remain ignored。
- [ ] Docs validators and whitespace check pass。

## Out of Scope

- SDK自動導入、license自動受諾、Gradle migration、release artifact/signing。
- 非Arch distroの検証。
- CI上のWaydroid / Apple Music E2E。

## Open Questions

- None。対応環境、Android整備の温度感、ADB target policyはユーザー合意済み。
