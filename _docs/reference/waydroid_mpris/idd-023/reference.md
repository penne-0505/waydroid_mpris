---
title: "doctor.py の --quiet — 下調べで見たもの"
status: active
created_at: 2026-09-24
updated_at: 2026-09-24
references:
  - "_docs/intent/waydroid_mpris/idd-023/decision.md"
  - "_docs/qa/waydroid_mpris/idd-023/qa.md"
related_issues:
  - 6
related_prs: []
---

# doctor.py の --quiet — 下調べで見たもの

## Overview

- IDD-023 (doctor.py への --quiet 追加) の下調べで参照した file と、その理由の記録。
- baseline の確認結果: unittest discover 44 tests / py_compile / shell syntax / install dry-run は緑。
- records 検査 (`bash scripts/check-docs.sh`) には既存の赤が 1 件ある。`validate-todo` が
  TODO.md の Core-Test-17 (canonical QA path と Risk High の qa.md 要求) で失敗する。
  本 lane の変更前から存在し、本 lane の成果物 3 file は緑である。
- 健全な host での `python scripts/doctor.py` は 13 check すべて `PASS` で rc=0 である (実測)。
  `WARN` を出し得る check は `host MPRIS player` と `latest probe artwork` の 2 つである。
- 下調べ中の質問回答: q1 = 両方指定は使用 error にする。q2 = 件数を含む `OK all N checks passed`
  形式にする。q3 = FAIL/WARN の行だけ出す。q4 = WARN 行を出す (all-passed にまとめない)。
- plan review (IDD-023-1) の指摘 F1〜F4 を現物で確認し、すべて decision.md / qa.md に反映した。
  F1 は `scripts/` と `.github/` が path-based risk floor の対象で risk: High が必要なこと、
  F2 は DEC 新設 lane に R2 の計画 (Checks の R2-001 行) が必要なこと、F3 は「部分集合」の
  主張が all-passed 行と矛盾しないよう範囲を狭めたこと、F4 は INV-022 と AC-003 を
  check 結果の exit code に限定したことを確認した。

## 下調べで見たもの

- `scripts/doctor.py` — 変更対象。人間可読出力が `main()` 内の per-check print であること、`--json` の既存実装、status の 3 値と exit code が `FAIL` のみを数える構成を確認
- `tests/test_doctor_json.py` — `shutil.which` を None に差し替える `run_main` が 4 check をすべて `FAIL` (rc=1) にすること、helper 単体 test と `main()` test の分離の先例を確認。新 test も同じ経路を使う
- `README.md` — 編集対象。Diagnostics 節の doctor の説明段落 (`--json` の案内を含む) と unittest 列挙行を確認
- `QUICKSTART.md` / `.github/workflows/docs-ci.yml` — unittest 列挙行の残り 2 箇所を確認。新 test file を列挙に入れる必要 (INV-019) の根拠
- `scripts/check-docs.sh` — area の記録検査の構成と baseline の赤の切り分けのために確認
- `scripts/validate-intent.ts` / `scripts/validate-qa.ts` / `scripts/validate-frontmatter.ts` — intent_schema 3 (DEC 見出しと What / Why / Change freedom 必須、INV 行は 3 桁以上) と qa_schema 5 (`qa_status: planned` は Round 無しで許容) の要件を確認
- `_docs/intent/waydroid_mpris/idd-022/decision.md` — 同じ doctor.py を変えた直近の lane の decision.md の full schema の先例を確認
- `_docs/qa/waydroid_mpris/idd-022/qa.md` — qa_schema 5 の qa.md と、`which→None` の test 制約の経緯を確認
- `_docs/reference/waydroid_mpris/idd-022/reference.md` — reference.md の一行形式の先例を確認
- `_docs/standards/quality_assurance.md` — Risk 分類の定義を確認。doctor.py の出力に flag を足す変更は機能挙動に触れるため Medium と判断した
- `/home/penne/dev/active/work/pi-web-idd/.agents/skills/writing/SKILL.md` — 文章の作法 (1 主張 1 文、見出し 40 文字前後、出典は Why 側に書く) を確認

## Verification

- 関連 QA: `_docs/qa/waydroid_mpris/idd-023/qa.md`
