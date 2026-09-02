---
title: "QA: MPRIS position lead offset"
status: active
qa_status: verified
risk: High
qa_schema: 4
draft_status: n/a
created_at: 2026-09-02
updated_at: 2026-09-02
references:
  - "_docs/intent/Core/mpris-position-lead/decision.md"
related_issues: []
related_prs: []
---

# QA: `MPRIS position lead offset`

<!-- Canonical path: _docs/qa/Core/mpris-position-lead/qa.md -->
<!-- Risk High はパス自動下限 (scripts/) による。DEC 新設と併せて R2 が発動する。 -->

## Acceptance Criteria

- AC-001: lead 未指定 (既定 0) のとき、公開される `Position` は導入前と同一の projection 結果になる。
- AC-002: lead > 0 のとき、公開される `Position` が lead 分だけ前方の値になり、0 と duration で clamp される。
- AC-003: lead を設定しても、`Seek` / `SetPosition` から Android へ送出される seek 位置に lead が混入しない (INV-008)。
- AC-004: lead が CLI (`--position-lead-ms`) と user service installer の双方から設定でき、既定は 0 である。

## Checks

| ID | Source | Requirement / Invariant | Check Type | Command / File | Status |
| --- | --- | --- | --- | --- | --- |
| AC-001 | TODO | 既定 0 で projection 挙動が不変。 | unit | `tests/test_position_projection.py` | planned |
| AC-002 | TODO | lead 適用後も 0 / duration で clamp。 | unit | `tests/test_position_projection.py` | planned |
| AC-003 | TODO | lead が seek 位置へ漏れない。 | unit | `tests/test_mpris_position_lead.py` | planned |
| AC-004 | TODO | CLI と installer の引数導線、既定 0。 | manual | `python scripts/run-host-mpris-live.py --help`; `./scripts/install-user-service.sh --dry-run` | planned |
| INV-008 | intent | lead は公開 Position にのみ作用し、Android への seek 位置に作用しない。 | unit | `tests/test_mpris_position_lead.py` | planned |

## Rounds

### Round 1 (2026-09-02)

- **Commands**:

  ```bash
  python -m unittest tests/test_protocol_mapping.py tests/test_adb_transport.py \
    tests/test_adb_recovery.py tests/test_live_failure_mapping.py \
    tests/test_position_projection.py tests/test_artwork_cache.py \
    tests/test_mpris_position_lead.py
  python -m py_compile host/waydroid_mpris/*.py scripts/run-host-mpris-live.py \
    scripts/run-host-mpris-fixture.py scripts/doctor.py
  python scripts/run-host-mpris-live.py --help
  bash -n scripts/install-user-service.sh
  ./scripts/install-user-service.sh --dry-run
  ./scripts/install-user-service.sh --dry-run --position-lead-ms 400
  ./scripts/check-docs.sh
  ```

  結果: unit 40 tests OK / py_compile OK / `--help` に `--position-lead-ms` 出力 /
  installer dry-run は既定で `ExecStart` に offset を出さず、`--position-lead-ms 400`
  指定時のみ付与。`check-docs.sh` は rc=1 だが、error は
  `_docs/documentation_guide.md` から v2.5.3 migration で削除済みの 4 standards への
  リンク切れのみで、本変更以前から存在する (`Workflow-Chore-22` の担当範囲)。
  本変更が触れた文書には error / warning なし。

- **AC Coverage**:
  - AC-001: covered — `test_default_lead_keeps_published_position_identical`。既定 0 で
    `published_position_us()` が `position_us()` と一致。
  - AC-002: covered — `test_lead_shifts_published_position_forward` /
    `test_lead_is_clamped_to_duration` / `test_lead_does_not_apply_without_track` /
    `test_published_position_carries_lead`。
  - AC-003: covered — `test_seek_base_excludes_lead` /
    `test_set_position_round_trip_cancels_lead`。lead ありと lead なしの bridge が
    同一の `seekTo` を dispatch することを比較で確認。
  - AC-004: covered — CLI `--help` と installer dry-run の 2 形態を実行。
  - INV-008: covered — AC-003 と同一テスト。

- **Intent Delta**: DEC-007 新設 (`_docs/intent/Core/mpris-position-lead/decision.md`)。
  INV-008 を併設。ポインタは `position.py` の `published_position_us` と
  `mpris_service.py` の `SetPosition` に配置。

- **R2**: PENDING — DEC 新設 かつ Risk High (path 自動下限) により発動。`Core-R2-24` を TODO に追加。

- **Transferable Principles**: candidate あり。「体感的な遅延・ずれの報告に対しては、
  自層の誤差を実測して寄与を定量化してから対策層を決める」を
  `_docs/intent/Core/conventions/decision.md` に DEC-008 (candidate) として追記した。

- **Verdict**: PASS

<!-- R1 review notes: `serve_fixture` に lead 引数を通していないのは意図的な省略。
     fixture mode は決定的な検証用経路であり、調整点を二重化すると未検証の第二経路が生じる。
     `_player_fingerprint` は probe 由来の raw positionUs を使うため lead の影響を受けず、
     PropertiesChanged の発火条件は変化しない。 -->
