---
title: "doctor.py に machine-readable な --json 出力を追加する — 設計判断"
status: active
intent_schema: 3
created_at: 2026-09-24
updated_at: 2026-09-24
references:
  - "_docs/qa/waydroid_mpris/idd-022/qa.md"
  - "_docs/reference/waydroid_mpris/idd-022/reference.md"
related_issues:
  - 3
related_prs: []
---

# doctor.py に machine-readable な --json 出力を追加する — 設計判断

## Context

`scripts/doctor.py` は check 結果を `PASS adb target: ...` 形式の人間可読行でしか出さない。
script や monitoring から結果を使うには parse が必要で、machine-readable な出力がない。
lane の goal は `--json` flag の追加、既存出力と exit code 規則の維持、外部 command を
呼ばない unit test、README への 1 行追記である。check の条件評価を変えることは non-goal である。

下調べで判明した前提は次のとおり。

- doctor.py の check 収集は `main()` 内にあり、末尾で 1 行ずつ print して exit code を返す。
  status は `PASS` / `WARN` / `FAIL` の 3 値で、exit code は `FAIL` のみを数える。
- repo には JSON 出力の先例が 1 件ある。`scripts/run-disruptive-waydroid-restart-qa.py` は
  `json.dumps(report, indent=2, ensure_ascii=False)` に改行を付けて出し、check を
  `{"name", "status", "detail"}` の `checks` 配列として持ち、exit code は `status == "FAIL"`
  の有無で決める。
- `tests/test_adb_recovery.py` が `from scripts.doctor import ...` で doctor の helper を
  import して検査しており、外部 command を呼ばない test の経路が既にある。
- README の Development Checks の unittest 行は存在する test file をすべて列挙する形式で、
  AGENTS.md の Unit checks 行は `test_android_setup.py` が欠けた簡易 command である。

## Decisions

### DEC-041: --json は JSON だけを stdout に出す

- **What**: argparse に `--json` (`store_true`) を追加する。有効時は既存の per-check print を
  行わず、全 check を含む単一 JSON object を stdout に 1 回だけ print する。
- **Why**: 消費者は stdout をそのまま parse したい。人間可読行が混ざると JSON parse が壊れる。
- **Change freedom**: JSON の整形や key 名は DEC-042 に従う。stderr の扱いは変えない。
- **Anchors**: `scripts/doctor.py`

### DEC-042: JSON は checks 配列と全体結果の 2 key にする

- **What**: JSON object を `{"ok": bool, "checks": [{"name", "status", "detail"}]}` の形にする。
  `ok` は `FAIL` が 1 つ以上で `false`、それ以外 (`WARN` を含む) で `true` とする。`status` は既存の
  `PASS` / `WARN` / `FAIL` をそのまま文字列で保持する。整形は先例に揃えて
  `json.dumps(..., indent=2, ensure_ascii=False)` に改行を付ける。
- **Why**: 全体結果は boolean の `ok` にする (質問 q1 の回答)。`checks` 配列の形と整形は
  `run-disruptive-waydroid-restart-qa.py` の先例と同じにして、repo 内の JSON 出力を読む側の
  知識を共有できるようにする。`WARN` は exit code 規則でも失敗に数えないため、`ok` も同じ
  規則に揃える。
- **Change freedom**: 将来の追加 key は自由。`ok` の判定規則と既存の 3 key の意味を変えない。
- **Anchors**: `scripts/doctor.py`

### DEC-043: 出力整形を helper に分けて test 可能にする

- **What**: check 列から JSON 文字列を作る処理を `main()` の外の helper 関数に置く。新 test
  (`tests/test_doctor_json.py`) は 2 つに分かれる。作った `Check` object で helper を直接呼び、JSON の
  構造と `ok` の両側 (FAIL 有無別) を検査する。`shutil.which` を None を返す monkeypatch に差し替え、
  `sys.argv` を `"--json"` 付きに差し替えた上で `main()` を呼び、人間可読行の出ないことと exit code 1 を
  検査する。exit code 0 側は unit test にせず、健全な host での実行で確認する。
- **Why**: `which→None` の `main()` は 4 command check がすべて FAIL になり exit code 1 しか作れない
  (実測)。`PASS` 側を `main()` で作るには adb / waydroid / playerctl の実行 (INV-018 違反) か
  `subprocess` / `AdbRecoveryManager` の stub が必要で、stub の test は doctor の挙動ではなく stub を
  検査することになる。`ok` の両側は helper の単体 test で満たし、exit code 0 は実機で観測する。
  `main()` は引数を取らず `parse_args()` が `sys.argv` を読むため、呼び出しには `sys.argv` の差し替えも
  必要である (plan review F1 / F2)。
- **Change freedom**: helper の名前と分割の細かさは自由。`main()` の check 収集と条件評価の flow を
  変えないこと。
- **Anchors**: `scripts/doctor.py`, `tests/test_doctor_json.py`

### DEC-044: test 列挙行と README に新記述を足す

- **What**: README の Diagnostics 節 (doctor section) に `--json` の使い方を示す 1 行を追加する。
  test file を列挙する unittest 行のうち README / QUICKSTART / docs-ci.yml の 3 箇所に
  `tests/test_doctor_json.py` を追加する (質問 q2 の回答と plan review F3 / F4)。AGENTS.md には
  触れない。
- **Why**: 列挙形式の unittest 行は新 test を入れないとその command が新 test を走らせない。列挙箇所は
  README / QUICKSTART / docs-ci.yml / AGENTS.md の 4 箇所あるが、AGENTS.md は既に
  `test_android_setup.py` が欠けた簡易 command で、embed 同期まで含めると本 lane の範囲を超える。
- **Change freedom**: 文言と例示の形式は自由。AGENTS.md の Unit checks 行を変えないこと。
- **Anchors**: `README.md`, `QUICKSTART.md`, `.github/workflows/docs-ci.yml`

## Consequences / Impact

- `python scripts/doctor.py --json` で単一 JSON object が stdout に得られ、script から
  `json.loads` で直接読めるようになる。
- `--json` 無しの挙動 (人間可読行と exit code) は変わらない。
- doctor.py には出力整形の helper が 1 つ増える。check 収集と条件評価は変わらない。
- 新 test file が unittest discover と README / QUICKSTART / docs-ci.yml の unittest 行の対象に加わる。

## Quality Implications

- JSON 出力が人間可読出力と同じ check 集合を同じ status で映すこと。
- `--json` の有無に関わらず exit code 規則が同じであること。
- 新 test が `adb` / `waydroid` / `playerctl` の外部 command を実行しないこと。
- 確認観点は `_docs/qa/waydroid_mpris/idd-022/qa.md` の Checks に対応付ける。

## Intent-derived Invariants

- INV-014 (from DEC-041): `--json` 使用時は人間可読行を stdout に出さない
- INV-015 (from DEC-042): JSON の `ok` は FAIL のみで決まり WARN を失敗に数えない
- INV-016 (from DEC-042): JSON の各 check は人間可読出力と同じ name / status / detail をそのまま持つ
- INV-017 (from DEC-041): `--json` の有無に関わらず exit code 規則は同じである
- INV-018 (from DEC-043): 新 unit test は adb / waydroid / playerctl の外部 command を実行しない
- INV-019 (from DEC-044): README / QUICKSTART / docs-ci.yml の unittest 列挙行は repo の全 test file を含む

## Rollback / Follow-ups

- Rollback は `scripts/doctor.py` / `tests/test_doctor_json.py` / `README.md` / `QUICKSTART.md` /
  `.github/workflows/docs-ci.yml` の差し戻しで完結する。runtime への影響はない。
- `--json` の消費者 (monitoring 側) の整備は本 lane の scope 外である。
