---
title: "QA Test Plan: Waydroid ADB automatic recovery"
status: active
draft_status: n/a
qa_status: planned
risk: High
created_at: 2026-07-10
updated_at: 2026-07-10
references:
  - "_docs/intent/Core/waydroid-adb-auto-recovery/decision.md"
  - "_docs/plan/Core/waydroid-adb-auto-recovery/plan.md"
  - "_docs/qa/Core/waydroid-adb-auto-recovery/verification.md"
  - "_docs/qa/Core/waydroid-mpris-bridge/test-plan.md"
related_issues: []
related_prs: []
---

# QA Test Plan: `Waydroid ADB automatic recovery`

## Source of Intent

- TODO: `Core-Enhance-16`
- Plan: `_docs/plan/Core/waydroid-adb-auto-recovery/plan.md`
- Intent: `_docs/intent/Core/waydroid-adb-auto-recovery/decision.md`
- Parent intent: `_docs/intent/Core/waydroid-mpris-bridge/decision.md`

## Quality Goal

Waydroid / ADB connection 消失後に、bridge が他 device や authorization boundary を侵さず
自動復帰を試みる。復帰までの MPRIS safe state、bounded retry/logging、operator diagnosis を
自動テスト可能にし、実 restart を伴う確認だけを明示的な live gap として分離する。

## Acceptance Criteria

- AC-001: explicit target がない daemon は running Waydroid IP から target を解決し、
  missing / offline から bounded retry で `device` へ復帰する。
- AC-002: `unauthorized` は operator action required として分類され、自動 bypass されない。
- AC-003: explicit `--device` と multiple-device 環境で target selection / `-s` routing が一意である。
- AC-004: 全 unavailable state が MPRIS stopped / empty / non-controllable state へ落ちる。
- AC-005: repeated identical failure log と retry attempt が bounded で、recovery が記録される。
- AC-006: no host listener、no Waydroid lifecycle mutation、no global ADB reset、selected Apple Music
  session only を維持する。
- AC-007: discovery / state / retry / logging / stale mapping に AC / INV 対応 regression test がある。

## Intent-derived Invariants

- INV-001: explicit `--device` は Waydroid IP discovery より常に優先され、全 bridge ADB I/O は resolved target へ `-s` 付きで送られなければならない。
- INV-002: automatic recovery は missing / offline の TCP target にだけ `adb connect` を行い、`unauthorized` を user consent なしに回避または ready 扱いしてはならない。
- INV-003: Waydroid stopped、IP unknown、unsupported target のとき、daemon は unrelated ADB device を fallback target として採用してはならない。
- INV-004: recovery retry は bounded exponential backoff に従い、同一 failure log は毎 poll 出力せず、状態変化と recovery を観測可能にしなければならない。
- INV-005: recovery failure 中も Android source unavailable は MPRIS `Stopped` / empty metadata / `CanControl=false` に写像され、stale `Playing` を残してはならない。
- INV-006: automatic recovery は ADB client connection だけを変更し、host network listener、Waydroid lifecycle mutation、host-wide ADB server reset を追加してはならない。
- INV-007: command routing と Android payload は既存 bridge の selected Apple Music session only / MediaSession-derived data only の境界を維持しなければならない。

## Risk Assessment

- Risk level: High
- Risk rationale: ADB authorization と command target selection に関わり、誤分類すると user consent
  bypass の誤認、unrelated device 操作、stale media state が起こり得る。
- Regression risk: recovery wrapper が既存 snapshot / command / artwork I/O を変え、正常接続時の
  metadata/control を壊す可能性がある。
- Data safety risk: Low。snapshot と artwork cache 以外の永続データは変更しない。
- Security / privacy risk: High。ADB shell target と Android authorization を扱う。listener 追加や
  host-wide ADB reset を禁止し、selected session / payload invariant を継承する。
- UX risk: High。自動復帰不能、30 秒以上の遅延、毎秒 journal spam、operator guidance 欠落が
  daily use を阻害する。
- Agent misbehavior risk: Medium。live E2E 未実行を unit PASS から推測して完了扱いにする、または
  destructive QA を無断実行する可能性がある。

## Test Strategy

- Unit: pure parser、fake subprocess runner、fake monotonic clock で全 state transition を確認する。
- Integration: recovery-aware transport が resolved target を snapshot / command / artwork に渡し、
  exception が empty MPRIS snapshot へ写像されることを確認する。
- E2E: 明示承認後だけ、Waydroid / ADB restart と installed service journal を確認する。
- Manual QA: read-only doctor、service dry-run、current MPRIS safe state を確認する。
- Validator / static check: unit suite、`py_compile`、`bash -n`、service `--dry-run`、docs validators、
  `git diff --check`。
- Diff review: no `kill-server`、no listen/bind、no session/container control、Android code unchanged、
  selected target に必ず `-s`。

## Test Matrix

| ID | Source | Requirement / Invariant | Test Type | Command / File | Expected Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001 | TODO | Running Waydroid target is discovered and missing/offline reconnects with bounded retry. | unit | `tests/test_adb_recovery.py` | IP-derived serial, connect command, retry schedule, recovered read pass. | verified |
| AC-002 | TODO | Unauthorized requires operator action. | unit + diagnostic | `tests/test_adb_recovery.py`; `scripts/doctor.py` | no connect on unauthorized; actionable detail. | verified |
| AC-003 | TODO | Explicit and multiple-device routing is unambiguous. | unit | `tests/test_adb_recovery.py`; `tests/test_adb_transport.py` | explicit serial wins and all payload commands contain matching `-s`. | verified |
| AC-004 | TODO | Unavailable source clears stale MPRIS state. | regression | `tests/test_live_failure_mapping.py`; `tests/test_protocol_mapping.py` | Stopped, no-track metadata, `CanControl=false` derivation. | verified |
| AC-005 | TODO | Retry and logs are bounded while recovery remains observable. | unit | `tests/test_adb_recovery.py`; `tests/test_live_failure_mapping.py` | fake-clock assertions for 1..30 second retry and 60 second reminder/recovery log. | verified |
| AC-006 | TODO | Existing local-only and selected-session boundaries remain. | static diff + regression | `git diff`; existing Android / protocol tests | no listener/lifecycle/global reset code; Android routing unchanged. | verified |
| AC-007 | TODO | AC/INV mapped tests and validators pass. | test + validator | full unit suite; `./scripts/check-docs.sh` | commands pass and matrix is updated to verified/deferred accurately. | verified |
| INV-001 | intent | Target precedence and `-s` routing never become implicit. | unit | `tests/test_adb_recovery.py`; `tests/test_adb_transport.py` | no unscoped bridge payload command. | verified |
| INV-002 | intent | Connect only applies to retryable TCP state; unauthorized is not bypassed. | unit | `tests/test_adb_recovery.py` | connect call set excludes unauthorized and unsupported serial. | verified |
| INV-003 | intent | No unrelated fallback device. | unit | `tests/test_adb_recovery.py` | Waydroid stopped/missing IP with another ready device still fails closed. | verified |
| INV-004 | intent | Retry/log cadence is bounded and transitions are visible. | unit | fake-clock recovery/reporter tests | attempts respect cap; identical errors suppressed; recovery emitted. | verified |
| INV-005 | intent | Failure maps to stopped/empty/non-controllable MPRIS. | regression | `tests/test_live_failure_mapping.py` | safe state remains after recovery exceptions. | verified |
| INV-006 | intent | No new listener or lifecycle/global reset mutation. | static diff | host/scripts/systemd diff | only ADB client connect and read-only status/devices commands added. | verified |
| INV-007 | intent | Apple Music routing/privacy remain unchanged. | regression + static diff | existing tests; Android diff | Android code unchanged and protocol tests pass. | verified |

## Manual QA Checklist

- [x] `python scripts/doctor.py` reports the discovered Waydroid serial and exact ADB state without changing Waydroid/service state.
- [x] Current unavailable source leaves `playerctl --player=waydroid_mpris status` at `Stopped` and no stale metadata.
- [ ] With explicit approval, restart/disconnect QA shows automatic recovery without manual `adb connect`.
- [ ] With explicit approval, journal shows one initial failure, bounded reminders, and a recovery transition.
- [ ] If Android presents authorization, doctor/log request approval and recover only after operator action.

## Regression Checklist

- [x] Existing 17 unit tests pass.
- [x] Snapshot, command result, and artwork reads use the same resolved target.
- [x] Selected Apple Music session command rejection still propagates as MPRIS command failure.
- [x] Source failure still clears MPRIS state.
- [x] Service dry-run remains valid and contains no fixed environment IP.
- [x] Docs validators and Python/shell static checks pass.

## High-risk Checklist

- [x] Rollback path is documented in the plan.
- [x] Data safety scope excludes destructive operations.
- [x] Security / privacy boundaries and authorization behavior are explicit.
- [x] Failure modes for stopped, missing, offline, unauthorized, multiple device, and unsupported serial are planned.
- [ ] Live recovery behavior is verified after explicit approval, or deferred with a `PARTIAL` verdict.

## Out of Scope

- Daemon-controlled Waydroid/service restart。
- Android authorization automation。
- ADB server global reset。
- Non-ADB transport。
- Physical Android device support。

## Open Questions

- Disruptive live E2E remains deferred until the operator explicitly approves Waydroid / ADB interruption.
