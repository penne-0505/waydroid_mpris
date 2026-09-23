---
title: "QA: Waydroid ADB automatic recovery"
status: active
qa_status: partial
risk: High
qa_schema: 4
created_at: 2026-08-18
updated_at: 2026-08-18
references:
  - "_docs/intent/Core/waydroid-adb-auto-recovery/decision.md"
  - "_docs/plan/Core/waydroid-adb-auto-recovery/plan.md"
  - "_docs/qa/Core/waydroid-adb-auto-recovery/test-plan.md"
  - "_docs/qa/Core/waydroid-adb-auto-recovery/verification.md"
related_issues: []
related_prs: []
---

# QA: `Waydroid ADB automatic recovery`

<!-- Canonical path: _docs/qa/Core/waydroid-adb-auto-recovery/qa.md -->
<!-- 統合 qa doc。旧 test-plan.md / verification.md は Workflow-Chore-20 の
     semantic migration までは併存し、参照は上の references に残る。 -->

## Acceptance Criteria

TODO `Core-Test-17` の AC を継承する。Waydroid / ADB を実際に中断する live evidence
まで含めた完了条件は下記の通り。

- AC-001: new daemon code で稼働する installed service が ADB target 消失後に bounded retry で `device` へ戻り、manual `adb connect` なしで snapshot polling を再開する。
- AC-002: live `unauthorized` state が operator action required と診断され、approval 前は stopped state、approval 後は自動復帰になる。
- AC-003: journal が同一 failure を毎 poll 出さず、初回・状態変化・60 秒 reminder・recovery を観測できる。
- AC-004: recovery 前は MPRIS `Stopped` / no-track / `CanControl=false`、recovery 後は selected Apple Music session の metadata / controls / artwork が戻る。

## Checks

| ID | Source | Requirement / Invariant | Check Type | Command / File | Status |
| --- | --- | --- | --- | --- | --- |
| AC-001 | TODO | New daemon code の automatic reconnect が live 環境で observable。 | manual | `python scripts/run-disruptive-waydroid-restart-qa.py` + `journalctl --user -u waydroid-mpris.service` | planned |
| AC-002 | TODO | Live `unauthorized` transition の operator guidance と approval 後復帰。 | manual | `python scripts/doctor.py` + Android `Always allow` prompt 操作 | planned |
| AC-003 | TODO | Journal cadence: 初回 / 状態変化 / 60s reminder / recovery。 | manual | `journalctl --user -u waydroid-mpris.service -f` | planned |
| AC-004 | TODO | MPRIS safe state → recovery 後の metadata / artwork 復帰。 | manual | `playerctl --player=waydroid_mpris status/metadata` + `busctl --user get-property ...` | planned |
| INV-002 | intent | Automatic recovery は `unauthorized` を user consent なしに回避しない。 | manual + unit | `tests/test_adb_recovery.py`; live prompt observation | covered |
| INV-004 | intent | Recovery retry は bounded exponential backoff、identical failure は毎 poll 出さない。 | manual + unit | `tests/test_adb_recovery.py`; live journal | covered |
| INV-005 | intent | Recovery failure 中も MPRIS `Stopped` / empty / non-controllable を維持。 | manual + regression | `tests/test_live_failure_mapping.py`; live busctl | covered |

<!-- 既存 test-plan.md / verification.md の Test Matrix と Manual QA Checklist が
     詳細な履歴を持つ。planned Checks はそのうち live evidence が残せていない項目に絞る。 -->

## Rounds

### Round 1 (2026-07-10) — inherited from verification.md

- **Commands**:

  ```bash
  python -m unittest tests/test_protocol_mapping.py tests/test_adb_transport.py \
    tests/test_adb_recovery.py tests/test_live_failure_mapping.py \
    tests/test_position_projection.py tests/test_artwork_cache.py
  python -m py_compile host/waydroid_mpris/*.py scripts/run-host-mpris-live.py \
    scripts/run-host-mpris-fixture.py scripts/doctor.py \
    scripts/run-disruptive-waydroid-restart-qa.py
  bash -n scripts/install-user-service.sh
  ./scripts/install-user-service.sh --dry-run > /tmp/waydroid-mpris-dry-run.service
  systemd-analyze --user verify /tmp/waydroid-mpris-dry-run.service
  ./scripts/check-docs.sh
  git diff --check
  ```

- **AC Coverage**: AC-001..AC-007 (旧 numbering、`_docs/qa/Core/waydroid-adb-auto-recovery/verification.md` 参照)。
  Automated + read-only live checks は PASS。Live disruptive AC-001/002/005 は deferred。
- **Intent Delta**: None: Round 1 は 2026-07-10 の non-destructive verification 記録を統合しただけで、新しい設計判断は導入していない。既存 DEC 群 (`_docs/intent/Core/waydroid-adb-auto-recovery/decision.md`) が適用状態を継続する。
- **R2**: PENDING — Risk High で live disruptive verification (`Core-Test-17`) が実施される次 Round で再構成テストを実施する。
- **Transferable Principles**: None: automatic recovery の bounded retry / operator-action-required の切り分けは既存 DEC で表現済み。
- **Verdict**: PARTIAL — automated + read-only PASS、live disruptive verification は `Core-Test-17` へ deferred。

<!-- Round 2 は Core-Test-17 実装後に追記される。R2 は new DEC 新設 or
     Size >= M / Risk High の live verification 実施時に発動判定する。 -->
