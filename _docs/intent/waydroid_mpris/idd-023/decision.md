---
title: "doctor.py に --quiet を追加して FAIL と WARN を一目で見つけられるようにする — 設計判断"
status: active
intent_schema: 3
created_at: 2026-09-24
updated_at: 2026-09-24
references:
  - "_docs/qa/waydroid_mpris/idd-023/qa.md"
  - "_docs/reference/waydroid_mpris/idd-023/reference.md"
related_issues:
  - 6
related_prs: []
---

# doctor.py に --quiet を追加して FAIL と WARN を一目で見つけられるようにする — 設計判断

## Context

`scripts/doctor.py` は 13 件の check を `PASS name: detail` 形式で 1 行ずつ出し、`FAIL` と `WARN`
が `PASS` の行に埋もれる。lane の goal は `--quiet` flag の追加、全通過時の 1 行出力、exit code
規則の維持、`--json` との組み合わせの README への文書化、外部 command を呼ばない unit test である。
check の内容や評価 logic を変えることは non-goal である。

下調べで判明した前提は次のとおり。

- doctor.py は IDD-022 で追加した `--json` を既に持ち、人間可読出力は `main()` 内で
  `f"{check.status:<4} {check.name}: {check.detail}"` を 1 行ずつ print する。status は
  `PASS` / `WARN` / `FAIL` の 3 値で、exit code は `FAIL` のみを数える。
- `WARN` を出し得る check は `host MPRIS player` と `latest probe artwork` の 2 つである。
- 健全な host での実行は 13 check すべて `PASS` で rc=0 である (実測)。
- `tests/test_doctor_json.py` の `run_main` は `shutil.which` を None に差し替えるため
  4 command check がすべて `FAIL` になり rc=1 になる。外部 command を呼ばない test の経路が既にある。
- README / QUICKSTART / docs-ci.yml の unittest 列挙行は repo の全 test file を列挙する
  規約 (INV-019) がある。新 test file は 3 箇所の列挙に加える必要がある。

## Decisions

### DEC-061: --quiet は FAIL と WARN の行だけを出す

- **What**: argparse に `--quiet` (`store_true`) を追加する。有効時は `PASS` の check 行を省き、
  `FAIL` と `WARN` の行を既存と同じ形式で出す。件数サマリなどの追加行は付けない (質問 q3 の回答)。
- **Why**: quiet の目的は問題のある check を一目で見つけることである。`PASS` 行はその目的に対して
  雑音であり、行形式を既存に揃えると既存の目視や grep の知識がそのまま使える。
- **Change freedom**: 出力の生成方法 (helper の分割や名前) は自由。既存の人間可読行の形式と
  status の 3 値を変えないこと。
- **Anchors**: `scripts/doctor.py`

### DEC-062: FAIL も WARN も無いときは 1 行の all-passed を出す

- **What**: `--quiet` で `FAIL` も `WARN` も無いとき、通過を示す 1 行だけを出す。
  文言は件数を含む `OK all N checks passed` 形式にする (質問 q2 の回答)。
- **Why**: all-passed を出さないと quiet が「何も出ない」場合を作り、成功の確認ができない。
  件数を含めると quiet でも check 数の変化に気付ける。`WARN` は exit code では失敗でないが
  目で見るべき状態なので、all-passed の条件から外す (質問 q4 の回答)。
- **Change freedom**: 文言の細部は自由。件数を含み 1 行で通過が判別できることを変えないこと。
- **Anchors**: `scripts/doctor.py`

### DEC-063: --json と --quiet の同時指定は使用 error にする

- **What**: 両 flag が同時に指定されたときは使用 error にする (質問 q1 の回答)。
- **Why**: 2 つの flag は出力形式の選択として矛盾し、どちらかを黙って無視すると消費者の期待から
  外れる。使用 error は argparse の規約で rc=2 になり、check 結果の exit code 規則 (0 と 1) には
  触れない。
- **Change freedom**: error message の文言は自由。check 結果の exit code 規則を変えないこと。
- **Anchors**: `scripts/doctor.py`

### DEC-064: quiet の出力生成を helper に分けて test 可能にする

- **What**: check 列から quiet 出力を作る処理を `main()` の外の helper に置く。新 test
  (`tests/test_doctor_quiet.py`) は helper 単体 (FAIL/WARN の filter と all-passed の両側) と、
  `shutil.which` を None に差し替えた `main()` (4 check がすべて FAIL, rc=1, quiet 行が人間可読行の
  部分集合になる。この経路では all-passed 行を出さない) で構成する。rc=0 側の all-passed は
  健全な host での実行で確認する。
- **Why**: IDD-022 と同じ制約で、`which→None` の `main()` は rc=1 しか作れず、通過側を `main()` で
  作るには外部 command の実行 (INV-018 違反) か過剰な stub が必要である。`test_doctor_json.py` の
  `run_main` 経路を再利用できる。
- **Change freedom**: helper の名前と返す型は自由。`main()` の check 収集と条件評価の flow を
  変えないこと。
- **Anchors**: `scripts/doctor.py`, `tests/test_doctor_quiet.py`

### DEC-065: README の doctor section に --quiet を文書化し、新 test を列挙行に足す

- **What**: README の Diagnostics 節に `--quiet` の案内と `--json` 同時指定時の挙動 (DEC-063) を
  追加する。README / QUICKSTART / docs-ci.yml の unittest 列挙行に `tests/test_doctor_quiet.py` を
  追加する。AGENTS.md には触れない。
- **Why**: lane の goal が README の doctor section への文書化を要求する。列挙形式の unittest 行は
  新 test を入れないとその command が新 test を走らせない (INV-019)。
- **Change freedom**: 文言と例示の形式は自由。AGENTS.md を変えないこと。
- **Anchors**: `README.md`, `QUICKSTART.md`, `.github/workflows/docs-ci.yml`

## Consequences / Impact

- `python scripts/doctor.py --quiet` で FAIL と WARN の行 (または all-passed の 1 行) が得られる。
- `--quiet` 無しの挙動 (人間可読行、`--json`、exit code) は変わらない。
- doctor.py には出力生成の helper が 1 つ増える。check 収集と条件評価は変わらない。
- 新 test file が unittest discover と 3 箇所の列挙行の対象に加わる。

## Quality Implications

- quiet 出力の check 行は人間可読出力と同じ形式で status と detail が一致する (all-passed の 1 行は除く)。
- exit code 規則が `--quiet` の有無で変わらないこと。
- 新 test が外部 command を実行しないこと。
- 確認観点は `_docs/qa/waydroid_mpris/idd-023/qa.md` の Checks に対応付ける。

## Intent-derived Invariants

- INV-020 (from DEC-061): --quiet の stdout は FAIL と WARN の check 行と all-passed 行以外の行を含まない
- INV-021 (from DEC-062): FAIL も WARN も無いとき --quiet の stdout は 1 行である
- INV-022 (from DEC-061): check 結果の exit code 規則 (FAIL あり 1 / なし 0) は --quiet の有無で変わらない
- INV-023 (from DEC-064): 新 unit test は外部 command を実行しない

## Rollback / Follow-ups

- Rollback は `scripts/doctor.py` / `tests/test_doctor_quiet.py` / `README.md` / `QUICKSTART.md` /
  `.github/workflows/docs-ci.yml` の差し戻しで完結する。runtime への影響はない。
- quiet 出力の消費者 (cron や monitoring 側) の整備は本 lane の scope 外である。
