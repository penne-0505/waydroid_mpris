---
title: "doctor.py --json の FAIL 集計の一元化と非 UTF-8 stdout 対応 — 設計判断"
status: active
intent_schema: 3
created_at: 2026-09-24
updated_at: 2026-09-24
references:
  - "_docs/qa/waydroid_mpris/idd-024/qa.md"
  - "_docs/reference/waydroid_mpris/idd-024/reference.md"
related_issues:
  - 5
related_prs: []
---

# doctor.py --json の FAIL 集計の一元化と非 UTF-8 stdout 対応 — 設計判断

## Context

`scripts/doctor.py` の `--json` 出力に 2 つの欠陥がある。1 つ目は FAIL 判定が exit code
(L151) と JSON `ok` (L156) の 2 箇所に独立して書かれており、片方だけ更新すると `ok` と
exit code が乖離することである。2 つ目は `json.dumps(..., ensure_ascii=False)` の出力を
`sys.stdout.write` するため、stdout が非 UTF-8 の環境 (`PYTHONIOENCODING=ascii` 等) では
非 ASCII の detail で `UnicodeEncodeError` になり、1 byte も JSON を出力せず異常終了する
ことである。

lane の goal は FAIL 集計の一元化、非 UTF-8 stdout での有効な JSON 出力と現行 exit code の
維持、外部 command を呼ばない unit test による両挙動の検証である。check の内容と評価基準の
変更、`--json` 無し出力の変更は non-goal である。

下調べで判明した前提は次のとおり。

- IDD-022 (issue #3) が `--json` と `render_json_report` を追加した。その Round 2 は
  「`ok` と終了コードの集計式の重複」を nit として残件にしており、本 lane はその残件を
  含む (issue #5)。
- `LC_ALL=C` 単独では Python 3.14 は PEP 538 / PEP 540 により stdout が UTF-8 になる。
  決定的な再現条件は `PYTHONIOENCODING=ascii` のような明示的な encoding 指定であり、
  実測で `UnicodeEncodeError` と無出力を確認した。
- 非 ASCII の detail は実運用で発生し得る。`check_probe_snapshot` は probe の title / artist
  を、`check_from_process` は waydroid / playerctl の command 出力を detail に含む。
- 既存の `which → None` unit test 経路では detail が全 ASCII に固定され、非 UTF-8 crash は
  再現しない。非 ASCII detail を `main()` まで流すには `subprocess.run` と
  `AdbRecoveryManager` の stub が必要である。

## Decisions

### DEC-101: FAIL 集計を 1 箇所に集約する

- **What**: check 列の FAIL 有無判定を 1 つの helper に集め、JSON の `ok` と exit code の
  両方をそこから導く。判定規則自体 (FAIL のみを失敗と数え、WARN を失敗に数えない) は
  変えない。
- **Why**: 現行は 2 箇所が独立に同じ式を書いており、片方だけ更新すると `ok` と exit code が
  乖離する。IDD-022 Round 2 が nit として残した重複である。
- **Change freedom**: helper の名前と形 (述語関数など) は自由。既存の `render_json_report(checks)`
  の 1 引数 signature は変えない。既存 4 test が 1 引数で呼んでおり、`ok` を引数で渡す形にすると
  既存 44 tests が落ちる (plan review F1)。check の収集 flow と status 評価基準を変えないこと。
- **Anchors**: `scripts/doctor.py`

### DEC-102: --json の出力を ensure_ascii=True にする

- **What**: `render_json_report` の `json.dumps` を `ensure_ascii=True` に変える。非 ASCII は
  `\uXXXX` escape になり、出力が全 ASCII となる。`indent=2` と末尾改行の整形は変えない。
- **Why**: `ensure_ascii=False` + `sys.stdout.write` は stdout が非 UTF-8 のとき
  `UnicodeEncodeError` で 1 byte も出力せず異常終了する (実測)。全 ASCII 出力ならどの
  stdout encoding でも JSON 全体が出る。UTF-8 環境での JSON の byte 列は変わるが、
  `json.loads` の結果は等価で、消費者への差分は escape 表現だけである (質問 q1 の回答)。
- **Change freedom**: escape 以外の JSON 構造と整形は変えない。README に byte 列を固定する
  記述は無く、必須の追記は無い。`run-disruptive-waydroid-restart-qa.py` の `ensure_ascii=False`
  は file 書き込みが `encoding="utf-8"` 明示で条件が違い、本 lane で触れない。
- **Anchors**: `scripts/doctor.py`

### DEC-103: 非 UTF-8 挙動と集計の一貫は helper レベルの unit test で検査する

- **What**: `tests/test_doctor_json.py` に 3 類を足す。1 つ目は非 ASCII detail を含む check 列
  から作った report 文字列が全 ASCII で `json.loads` できること。2 つ目はその文字列を
  `encoding="ascii"` の stdout wrapper に書いても JSON 全体が得られること。3 つ目は PASS /
  WARN / FAIL の混在列で FAIL 判定が WARN を失敗に数えないこと。`main()` の
  `ok` / exit code 一致は既存の `which → None` 経路が引き続き検査する。
- **Why**: 非 ASCII detail を `main()` まで流すには `subprocess.run` と `AdbRecoveryManager`
  の stub が必要で、IDD-022 の DEC-043 は stub test は doctor の挙動ではなく stub を検査する
  ことになると判断した。helper レベルなら非 ASCII detail を直接作れる (質問 q2 の回答)。
  `which → None` の `main()` は status が全 FAIL に固定されるため、WARN を失敗に数える誤った
  判定は混在列の test でしか検出できない (plan review F2)。
- **Change freedom**: test 名と分割の細かさは自由。`main()` を stub で拡張しないこと。
- **Anchors**: `tests/test_doctor_json.py`

## Consequences / Impact

- `python scripts/doctor.py --json` が非 UTF-8 stdout 環境でも JSON 全体を出力し、現行と同じ
  exit code を返す。
- UTF-8 環境でも非 ASCII の detail は `\uXXXX` escape で出力され、JSON の byte 列が変わる。
  parse 結果は変わらない。
- FAIL 集計の式が 1 箇所になり、`ok` と exit code が常に同じ判定から導かれる。
- `--json` 無しの人間可読出力と exit code は変わらない。

## Quality Implications

- JSON の `ok` と exit code がどの check 列でも乖離しないこと。
- 非 UTF-8 環境で traceback や 0 byte 出力にならず、JSON 全体が出ること。
- 既存の unittest 44 tests が引き続き緑であること。
- 確認観点は `_docs/qa/waydroid_mpris/idd-024/qa.md` の Checks に対応付ける。

## Intent-derived Invariants

- INV-024 (from DEC-101): JSON の `ok` と exit code は同一の FAIL 判定から導かれる
- INV-025 (from DEC-102): `--json` の stdout はどの stdout encoding の環境でも JSON 全体を出力する
- INV-026 (from DEC-103): 非 UTF-8 挙動の検査は外部 command を呼ばない unit test で行う

## Rollback / Follow-ups

- Rollback は `scripts/doctor.py` / `tests/test_doctor_json.py` の差し戻しで完結する。
  runtime への影響はない。
- 非 ASCII を含む stdout への `ensure_ascii=False` 出力を持つ他 script
  (`run-disruptive-waydroid-restart-qa.py`) は本 lane の scope 外であり、同型の問題が将来
  表面化したら別途判断する。
