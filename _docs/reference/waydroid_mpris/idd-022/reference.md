---
title: "doctor.py の --json 出力 — 下調べで見たもの"
status: active
created_at: 2026-09-24
updated_at: 2026-09-24
references:
  - "_docs/intent/waydroid_mpris/idd-022/decision.md"
  - "_docs/qa/waydroid_mpris/idd-022/qa.md"
related_issues:
  - 3
related_prs: []
---

# doctor.py の --json 出力 — 下調べで見たもの

## Overview

- IDD-022 (doctor.py への --json 追加) の下調べで参照した file と、その理由の記録。
- baseline の確認結果: unittest discover 38 tests / py_compile / shell syntax / install dry-run は緑。
- records 検査には既存の赤が 2 件ある。`validate-todo` が TODO.md の Core-Test-17 (Risk High が
  test-plan.md を QA に指す) で、`validate-intent` が IDD-002 decision.md の INV 行 (2 桁の DEC 番号) で
  失敗する。どちらも本 lane の変更前から存在し、本 lane の成果物とは無関係である。
- 下調べ中の質問回答: q1 = 全体結果は boolean の `ok` にする。q2 = 新 test を README の unittest 行に追加する。
- plan review (IDD-022-1) の指摘 F1〜F4 を現物で実測し、すべて decision.md / qa.md に反映した。
  F1 は `which→None` の `main()` が rc=1 しか作れないこと (実測 rc=1)、F2 は `parse_args()` が
  `sys.argv` を読むこと、F3 は docs-ci.yml の runtime job が test file を列挙すること、F4 は
  QUICKSTART も列挙することを確認した。健全な host での `python scripts/doctor.py` は全 PASS・
  rc=0 であることも実測した。

## 下調べで見たもの

- `scripts/doctor.py` — 変更対象。check 収集が `main()` 内にあり、末尾で `f"{check.status:<4} {check.name}: {check.detail}"` を 1 行ずつ print して exit code を返す構成を確認。status は `PASS` / `WARN` / `FAIL` の 3 値で、exit code は `FAIL` のみを数えることを確認
- `scripts/run-disruptive-waydroid-restart-qa.py` — repo の JSON 出力の先例。`json.dumps(report, indent=2, ensure_ascii=False)` + 改行で、check を `{"name", "status", "detail"}` の `checks` 配列として出し、exit code は `status == "FAIL"` の有無で決める構成を確認。doctor の JSON 出力もこの形に揃える判断の根拠
- `tests/test_adb_recovery.py` — tests から `from scripts.doctor import check_from_inspection, check_mpris_metadata` と doctor の helper を import して検査する先例を確認。新 test も同じ import 経路で外部 command を呼ばずに済む
- `README.md` — 編集対象。Diagnostics 節の `python scripts/doctor.py` と doctor の説明段落、Development Checks の unittest 列挙行を確認
- `AGENTS.md` — Unit checks が test file の列挙形式であることを確認。新 test file を列挙に入れるかの判断 (質問 q2) の材料
- `scripts/check-docs.sh` — area の記録検査の構成 (frontmatter / todo / doc-links / intent / qa / comments / intent-delta) を確認
- `scripts/validate-intent.ts` — `intent_schema: 3` の必須見出し 6 節、DEC 見出し `### DEC-nnn:` と What / Why / Change freedom 必須、INV 行の正規表現が `INV-` と `DEC-` を 3 桁以上で要求することを確認。番号帯 DEC-041〜 / INV-014〜 は 3 桁 zero padding で書く
- `scripts/validate-qa.ts` — `qa_schema: 5` の必須見出し 3 節 (Acceptance Criteria / Checks / Rounds) と、`qa_status: planned` は Round 無しで許容されることを確認
- `scripts/validate-frontmatter.ts` / `scripts/validate-doc-links.ts` — 本 lane 成果物の frontmatter 必須 field と参照検査を確認
- `scripts/validate-todo.ts` — baseline の赤の原因を確認。`Size >= M` / `Risk >= Medium` の task は QA が `qa.md` であることを要求し、Core-Test-17 が `test-plan.md` を指すため失敗する
- `_docs/intent/waydroid_mpris/idd-002/decision.md` — 本 repo の IDD lane 成果物 decision.md の full schema の先例を確認
- `_docs/qa/waydroid_mpris/idd-002/qa.md` — `qa_schema: 5` の qa.md (AC / Checks 表 / Rounds) の先例を確認
- `_docs/reference/waydroid_mpris/idd-002/reference.md` — reference.md の一行形式の先例を確認
- `/home/penne/dev/active/work/pi-web-idd/.agents/skills/writing/SKILL.md` — 文章の作法 (1 主張 1 文、見出し 40 文字前後、出典は Why 側に書く) を確認

## Verification

- 関連 QA: `_docs/qa/waydroid_mpris/idd-022/qa.md`
