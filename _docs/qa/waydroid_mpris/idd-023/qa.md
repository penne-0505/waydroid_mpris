---
title: "QA: doctor.py に --quiet を追加して FAIL と WARN を一目で見つけられるようにする"
status: active
qa_schema: 5
qa_status: partial
risk: High
created_at: 2026-09-24
updated_at: 2026-09-24
references:
  - "_docs/intent/waydroid_mpris/idd-023/decision.md"
  - "_docs/reference/waydroid_mpris/idd-023/reference.md"
related_issues:
  - 6
related_prs: []
---

# QA: doctor.py に --quiet を追加して FAIL と WARN を一目で見つけられるようにする

## Acceptance Criteria

- AC-001: `python scripts/doctor.py --quiet` の stdout が FAIL と WARN の check 行だけを含み、PASS の check 行を含まない
- AC-002: FAIL も WARN も無いとき `--quiet` の stdout が 1 行で通過を示す
- AC-003: `--quiet` の有無に関わらず check 結果の exit code が FAIL の有無だけで決まる (使用 error の rc=2 は対象外)
- AC-004: `--quiet` 無しの stdout と exit code が実装前と変わらない
- AC-005: `--quiet` と `--json` の同時指定が README に文書化した挙動になる
- AC-006: 新 unit test が unittest discover で通り、外部 command を実行しない
- AC-007: README の doctor section に `--quiet` の案内と `--json` 同時指定の挙動の記述がある
- AC-008: README / QUICKSTART / docs-ci.yml の unittest 列挙行に新 test file がある

## Checks

| ID | Source | Requirement / Invariant | Check Type | Command / File | Status |
| --- | --- | --- | --- | --- | --- |
| AC-001 | DEC-061, INV-020 | quiet が FAIL/WARN 行だけを出す | command | `tests/test_doctor_quiet.py` の filter 検査と、`which→None` の `main()` で PASS 行の不在を確認 | verified |
| AC-002 | DEC-062, INV-021 | all-passed の 1 行 | command | helper 単体 test と、健全な host での `python scripts/doctor.py --quiet` の実行 | verified |
| AC-003 | DEC-061, INV-022 | check 結果の exit code 規則の維持 | command | `tests/test_doctor_quiet.py` (rc=1 側) と、健全な host での rc=0 の実行 | verified |
| AC-004 | DEC-061 | 既存出力の非変化 | command | 実装前後の `python scripts/doctor.py` の stdout / stderr / rc の diff | verified |
| AC-005 | DEC-063 | `--json` 同時指定の挙動 | command | `tests/test_doctor_quiet.py` での同時指定の検査 (rc=2 を含む) | verified |
| AC-006 | DEC-064, INV-023 | 外部 command を使わない unit test | command | `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py'` と test 本体の目視 | verified |
| AC-007 | DEC-065 | README の案内行 | diff-review | `README.md` の Diagnostics 節を目視で突き合わせ | verified |
| AC-008 | DEC-065, INV-019 | unittest 列挙行への新 test 追加 | command | README / QUICKSTART / docs-ci.yml の列挙行への `grep tests/test_doctor_quiet.py` | verified |
| AGENT-001 | DEC-064, INV-023 | agent misbehavior: 新 test が外部 command を実行しない | command | `tests/test_doctor_quiet.py` が `subprocess.run` を raise する mock で外部 command 実行を検知 | verified |
| ROLLBACK-001 | DEC-061, DEC-065 | rollback / recovery: 差し戻しで実装前の出力と exit code に戻る | diff-review | 対象 5 file の差し戻し (runtime state を持たない) | verified |
| R2-001 | DEC-061, DEC-062, DEC-063, DEC-064, DEC-065 | 記録のみから設計判断を再構成できる | diff-review | TODO `waydroid_mpris-R2-23` | planned |

## Rounds

<!-- 追記専用。実装後に Round を追記する。 -->

### Round 1 (2026-09-24)

- **Intent Delta**: 新設: DEC-061, DEC-062, DEC-063, DEC-064, DEC-065
- **R2**: PENDING（Issue lane の S3 で実施）
- **Verdict**: PARTIAL

実施内容:

- `scripts/doctor.py` の `--json` を `argparse` の mutually exclusive group に移し、`--quiet` (store_true) を足した (DEC-061)。
- quiet 有効時は check 列から `FAIL` と `WARN` の行だけを既存形式で出し、`FAIL` も `WARN` も無いときは `OK all N checks passed` の 1 行を出すようにした (DEC-061 / DEC-062)。
- 出力生成を `format_check_line` と `render_quiet_report` の 2 helper に分け、人間可読出力も同じ formatter を使うようにした (DEC-064)。
- 同時指定を argparse の mutually exclusive group で使用 error (rc=2) にした (DEC-063)。
- `tests/test_doctor_quiet.py` を追加した。helper の filter / all-passed 両側と、`shutil.which` を None に固定した `main()` の FAIL 行一致 / rc=1 / 同時指定の rc=2 を検査する (DEC-064)。
- `README.md` の Diagnostics 節に `--quiet` と `--json` 同時指定の使用 error を文書化し、README / QUICKSTART / docs-ci.yml の unittest 列挙行に `tests/test_doctor_quiet.py` を足した (DEC-065)。`AGENTS.md` は触っていない。
- 検証: AC-001 は helper の filter 検査と、PATH を空にした `doctor.py --quiet` の stdout が `FAIL` 行のみ (PASS 行 0) で人間可読出力の `FAIL` 行と一致することで確認した。AC-002 は helper が `OK all 2 checks passed` の 1 行を返すことと、健全な host の実行が `OK all 13 checks passed` の 1 行 / rc=0 であることで確認した。AC-003 は `which→None` と PATH 空の実行が rc=1、健全な host が rc=0 で、`--quiet` の有無で一致することで確認した。AC-004 は `git show HEAD:scripts/doctor.py` と作業中の doctor.py を同じ runner で実行し、非 quiet の stdout と rc が live / PATH 空の両方で byte-identical であることを diff で確認した。AC-005 は両順序 (`--quiet --json` / `--json --quiet`) が rc=2 になることを test と実機で確認した。AC-006 は discover 51 tests が緑であることで確認した。AC-007 / AC-008 は README の案内行と 3 file の列挙行 (各 1 箇所) で確認した。
- public 4 check (unittest 51 tests / py_compile / shell syntax / install dry-run) は緑である。
- records scope の `check-docs.sh` は既知の TODO.md 赤 (Core-Test-17) のみで、本 lane の記録 3 file は緑である。
- agent misbehavior の確認: 新 test は `scripts.doctor.shutil.which` を None に固定し、`subprocess.run` を raise する mock を当てて外部 command の実行を検知する (AGENT-001 / INV-023)。`--quiet` と `--json` の同時指定は check 収集の前の parse で弾くため、この経路でも外部 command を実行しない。
- rollback / recovery の確認: 本差分は `scripts/doctor.py` / `tests/test_doctor_quiet.py` / `README.md` / `QUICKSTART.md` / `.github/workflows/docs-ci.yml` の 5 file に閉じ、runtime state / migration / data を持たない。差し戻しで `--quiet` と 2 helper が消え、AC-004 の byte-identical な実装前出力に戻る (ROLLBACK-001)。
- review fix (1 巡目): R2-001 が参照していた `waydroid_mpris-R2-23` を TODO.md の Backlog に積み、R2 の負債を着手可能な状態にした (F-1)。all-passed 行の文言を literal で固定していた test を、DEC-062 の Change freedom が不変とする「1 行・件数を含む・problem status を含まない」の検査へ変えた (F-2)。
