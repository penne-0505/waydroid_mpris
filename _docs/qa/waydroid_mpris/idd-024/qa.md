---
title: "QA: doctor.py --json の FAIL 集計の一元化と非 UTF-8 stdout 対応"
status: active
qa_schema: 5
qa_status: partial
risk: High
created_at: 2026-09-24
updated_at: 2026-09-24
references:
  - "_docs/intent/waydroid_mpris/idd-024/decision.md"
  - "_docs/reference/waydroid_mpris/idd-024/reference.md"
related_issues:
  - 5
related_prs: []
---

# QA: doctor.py --json の FAIL 集計の一元化と非 UTF-8 stdout 対応

## Acceptance Criteria

- AC-001: JSON の `ok` と exit code が同一の FAIL 判定から導かれる
- AC-002: 非 UTF-8 の stdout でも `--json` が JSON 全体を出力する
- AC-003: `--json` 使用時の exit code が現行規則 (FAIL で 1、それ以外で 0) のままである
- AC-004: `--json` 無しの stdout と exit code が変更前と変わらない
- AC-005: 非 UTF-8 挙動を検査する新 unit test が外部 command を呼ばず unittest discover で通る
- AC-006: check の収集内容と status 評価基準が変更前と変わらない
- AC-007: PASS と WARN が混在する check 列で FAIL 判定が WARN を失敗に数えない

## Checks

| ID | Source | Requirement / Invariant | Check Type | Command / File | Status |
| --- | --- | --- | --- | --- | --- |
| AC-001 | DEC-101, INV-024 | `ok` と exit code の判定の一元化 | command | `tests/test_doctor_json.py` の既存 ok / exit code 一致検査と、`main()` と `render_json_report` が同一の判定を使うことの diff 目視 | verified |
| AC-002 | DEC-102, INV-025 | 非 UTF-8 stdout での JSON 全体の出力 | command | `PYTHONIOENCODING=ascii` 下の `python scripts/doctor.py --json \| python -m json.tool` と、非 ASCII detail の helper test | verified |
| AC-003 | DEC-101, INV-024 | exit code 規則の維持 | command | `tests/test_doctor_json.py` の既存 rc=1 検査と `PYTHONIOENCODING=ascii` 下の実行 | verified |
| AC-004 | DEC-102 | 既存出力の非変化 | command | 変更前後の `python scripts/doctor.py` (無 flag) の stdout / exit code diff | verified |
| AC-005 | DEC-103, INV-026 | 外部 command を使わない unit test | command | `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py'` と test 本体の目視 | verified |
| AC-006 | DEC-101 | check 収集と評価基準の非変化 | diff-review | `scripts/doctor.py` の check 収集部分の diff 目視 | verified |
| AC-007 | DEC-103 | 混在列で WARN を失敗に数えない FAIL 判定 | command | `tests/test_doctor_json.py` に足す PASS / WARN / FAIL 混在列での FAIL 判定の helper test | verified |
| AGENT-001 | DEC-103, INV-026 | agent misbehavior: 新 test が adb / waydroid / playerctl を実行しない | command | `tests/test_doctor_json.py` が `subprocess.run` を raise する mock で外部 command 実行を検知 | verified |
| ROLLBACK-001 | DEC-101, DEC-102 | rollback / recovery: 差し戻しで実装前の stdout と exit code に戻る | diff-review | `scripts/doctor.py` / `tests/test_doctor_json.py` の差し戻し (runtime state を持たない) | verified |
| R2-001 | DEC-101, DEC-102, DEC-103 | 記録のみから設計判断を再構成できる | diff-review | Issue lane の S3 で実施する R2 タスク (DEC 新設かつ risk High で発動) | planned |

AC-007 が守る規則自体は IDD-022 の DEC-042 / INV-015 (`ok` は FAIL のみで決まり WARN を失敗に
数えない) であり、本 lane はその規則を集約後の判定でも維持する。

## Rounds

<!-- 追記専用。実装後に Round を追記する。 -->

### Round 1 (2026-09-24)

- **Intent Delta**: 新設: DEC-101, DEC-102, DEC-103
- **R2**: PENDING（Issue lane の S3 で実施）
- **Verdict**: PARTIAL (R2 再構成テストが未実施。残リスクは本 round に記録)

実施内容:

- `scripts/doctor.py` に `has_failure(checks)` を足し、`main()` の exit code と `render_json_report` の `ok` の両方をこの 1 つの判定から導くようにした (DEC-101)。判定規則は FAIL のみを失敗と数える現行のままである。check の収集 flow と status 評価基準は変えていない (AC-001 / AC-006 / AC-007)。
- `render_json_report` の `json.dumps` を `ensure_ascii=False` から `ensure_ascii=True` に変えた (DEC-102)。非 ASCII の detail は `\uXXXX` escape になり、出力は全 ASCII になる。`indent=2` と末尾改行の整形は変えていない (AC-002)。
- `tests/test_doctor_json.py` に `NonAsciiDetailTest` と `FailureAggregationTest` を足した (DEC-103)。非 ASCII detail を含む report が全 ASCII で `json.loads` できること、その文字列が `encoding="ascii"` の stdout wrapper を通過すること、PASS / WARN / FAIL の混在列で WARN を失敗に数えないことを検査する (AC-002 / AC-007)。どちらも `render_json_report` / `has_failure` を直接呼び、外部 command を実行しない (AC-005 / INV-026)。
- 検証: AC-002 は `PYTHONIOENCODING=ascii` の下で `main()` に非 ASCII detail を流し、1217 byte の JSON 全体が出力され `json.tool` を通ることを確認した。同じ条件の `scripts/doctor.py --json` 実行も `json.tool` を通った。AC-003 は live の rc=0 と、`which → None` 経路および非 ASCII 注入実行の rc=1 で両側を確認した。AC-004 は `--json` 無しの stdout / stderr / rc が実装前後で byte-identical であることを diff で確認した。AC-001 は両呼び出しが `has_failure` を共有することの diff 目視と、rc と `ok` の一致 test で確認した。
- public 4 check (unittest 49 tests / py_compile / shell syntax / install dry-run) は緑である。
- agent misbehavior の確認: 新 test は外部 command を呼ばない。既存の `run_main` 経路は `scripts.doctor.subprocess.run` を raise する mock を引き続き持つ (AGENT-001 / INV-026)。
- rollback / recovery の確認: 本差分は `scripts/doctor.py` / `tests/test_doctor_json.py` の 2 file に閉じ、runtime state / migration / data を持たない。差し戻しで実装前の出力と exit code に戻る (ROLLBACK-001)。
- records 検査: `check-docs.sh` は既知の TODO.md 赤 (Core-Test-17) のみで、本 lane の成果物は緑である。

残リスク:

- R2 再構成テストが未実施である。Issue lane の S3 で隔離して行う。
- `run-disruptive-waydroid-restart-qa.py` の `ensure_ascii=False` は本 lane の scope 外に残る。file 書き込みが `encoding="utf-8"` 明示で stdout 問題の条件が違う。
