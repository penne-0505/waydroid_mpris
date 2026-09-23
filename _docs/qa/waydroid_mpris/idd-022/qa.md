---
title: "QA: doctor.py に machine-readable な --json 出力を追加する"
status: active
qa_schema: 5
qa_status: verified
risk: Low
created_at: 2026-09-24
updated_at: 2026-09-24
references:
  - "_docs/intent/waydroid_mpris/idd-022/decision.md"
  - "_docs/reference/waydroid_mpris/idd-022/reference.md"
related_issues:
  - 3
related_prs: []
---

# QA: doctor.py に machine-readable な --json 出力を追加する

## Acceptance Criteria

- AC-001: `python scripts/doctor.py --json` の stdout が単一の JSON object として parse でき、`PASS xxx:` 形式の人間可読行を含まない
- AC-002: JSON の `checks` 配列の各要素が `name` / `status` / `detail` を持ち、人間可読出力と同じ check 集合と status を映す
- AC-003: `FAIL` が 1 つ以上のとき全体結果が fail を示し exit code が 1、`FAIL` が無いとき全体結果が pass を示し exit code が 0 である
- AC-004: `--json` 無しの stdout と exit code が実装前と変わらない
- AC-005: 新 unit test が unittest discover で通り、`adb` / `waydroid` / `playerctl` の外部 command を実行しない
- AC-006: README の doctor section に `--json` の案内 1 行がある
- AC-007: README の Development Checks の unittest 行に `tests/test_doctor_json.py` がある

## Checks

| ID | Source | Requirement / Invariant | Check Type | Command / File | Status |
| --- | --- | --- | --- | --- | --- |
| AC-001 | DEC-041, INV-014 | `--json` 時の stdout が JSON のみ | command | `python scripts/doctor.py --json \| python -m json.tool` と、人間可読行が混ざらないことの目視 | verified |
| AC-002 | DEC-042, INV-016 | checks 配列の要素構造と既存出力との一致 | command | `tests/test_doctor_json.py` の構造検査と、`--json` 無し出力との突き合わせ | verified |
| AC-003 | DEC-042, INV-015, INV-017 | 全体結果と exit code の規則 | command | `tests/test_doctor_json.py` での helper 両側 (FAIL 有無別) の検査と、健全な host での実行で exit code 0 を確認 | verified |
| AC-004 | DEC-041, INV-017 | 既存出力の非変化 | command | 実装前後の `python scripts/doctor.py` の出力 diff と exit code (実機実行を含む) | verified |
| AC-005 | DEC-043, INV-018 | 外部 command を使わない unit test | command | `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py'` と、test 本体の目視 | verified |
| AC-006 | DEC-044 | README の案内行 | diff-review | `README.md` の Diagnostics 節を目視で突き合わせ | verified |
| AC-007 | DEC-044, INV-019 | unittest 列挙行への新 test 追加 | command | README / QUICKSTART / docs-ci.yml の unittest 行への `grep tests/test_doctor_json.py` | verified |

## Rounds

<!-- 追記専用。実装後に Round を追記する。 -->

### Round 1 (2026-09-24)

- **Intent Delta**: applied: DEC-041, DEC-042, DEC-043, DEC-044
- **R2**: 非発動 (Intent Delta は既存 DEC の applied のみ、risk Low)
- **Verdict**: PASS

実施内容:

- `scripts/doctor.py` に `--json` (store_true) を足し、有効時は人間可読行を出さず `render_json_report(checks)` の文字列を stdout に 1 回書くようにした (DEC-041)。
- JSON を `{"ok", "checks"}` の 2 key にし、`ok` は FAIL の有無だけで決め、各 check は name / status / detail をそのまま持つようにした (DEC-042)。整形は先例に揃えて `indent=2` / `ensure_ascii=False` と末尾改行にした。
- 出力整形を `main()` の外の helper `render_json_report` に分けた (DEC-043)。
- `tests/test_doctor_json.py` を追加した。helper の key 構造と `ok` の両側、`shutil.which` を None に固定した `main()` の JSON 単一性 / rc=1 / 人間可読行の不在、人間可読出力との name / status / detail 一致を検査する (DEC-043 / INV-016)。test は `subprocess.run` を raise する mock で外部 command を禁じている (INV-018)。
- `README.md` の Diagnostics 節に `--json` の案内を 1 行足し、README / QUICKSTART / docs-ci.yml の unittest 列挙行に `tests/test_doctor_json.py` を足した (DEC-044)。`AGENTS.md` は触っていない。
- 検証: AC-001 は `--json` の stdout が `json.tool` を通り `^(PASS|WARN|FAIL) ` 行を含まないことで確認した (rc=0)。AC-002 は live の人間可読 13 check と JSON の name / status / detail が一致することで確認した。AC-003 は live (全 PASS, rc=0, ok=true) と PATH を空にした FAIL 実行 (rc=1, ok=false) で両側を確認した。AC-004 は `--json` 無しの stdout / stderr / rc が実装前後で byte-identical であることを diff で確認した。AC-005 は discover 44 tests が緑であることで確認した。AC-006 / AC-007 は README の案内行と 3 file の列挙行で確認した (各 1 箇所)。records scope の `check-docs.sh` は既知の TODO.md 赤 (Core-Test-17) のみで、本 lane の成果物 3 file は緑である。
- public 4 check (unittest 44 tests / py_compile / shell syntax / install dry-run) は緑である。
