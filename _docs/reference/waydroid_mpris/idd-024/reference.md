---
title: "doctor.py --json の FAIL 集計と非 UTF-8 stdout — 下調べで見たもの"
status: active
created_at: 2026-09-24
updated_at: 2026-09-24
references:
  - "_docs/intent/waydroid_mpris/idd-022/decision.md"
  - "_docs/qa/waydroid_mpris/idd-022/qa.md"
  - "_docs/reference/waydroid_mpris/idd-022/reference.md"
related_issues:
  - 5
related_prs: []
---

# doctor.py --json の FAIL 集計と非 UTF-8 stdout — 下調べで見たもの

## Overview

- IDD-024 (doctor.py --json の FAIL 集計の一元化と非 UTF-8 stdout 対応) の下調べで参照した
  file と、その理由の記録。
- baseline の確認結果: unittest discover 44 tests / py_compile / shell syntax / install dry-run
  は緑。
- records 検査には既存の赤が 1 件ある。`validate-todo` が TODO.md の Core-Test-17 (QA path と
  Risk High の qa.md 要求) で失敗する。本 lane の変更前から存在し、成果物とは無関係である。
- IDD-022 (issue #3, --json 追加) の Round 2 が「`ok` と終了コードの集計式の重複」を nit として
  残しており、本 lane (issue #5) はその残件と非 UTF-8 stdout 問題を扱う。
- 下調べ中の質問回答: q1 = `ensure_ascii=True` で全 ASCII 出力にする。q2 = 非 UTF-8 挙動の
  test は helper 出力を非 UTF-8 stdout に書いて検査する (stub で `main()` まで流さない)。

## 確認した事実

- FAIL 集計の重複は `scripts/doctor.py` の 2 行にある。L151 の exit code 式
  (`return 1 if any(check.status == "FAIL" ...)`) と L156 の JSON `ok` 式
  (`"ok": not any(check.status == "FAIL" ...)`) が独立に同じ判定を書いており、片方だけの更新で
  乖離し得ることを確認した。
- 非 UTF-8 stdout での異常終了を実測した。`PYTHONIOENCODING=ascii` の下で非 ASCII の detail を
  含む check 列を `render_json_report` して `sys.stdout.write` すると `UnicodeEncodeError` で
  1 byte も出力せず異常終了する (`json.dumps(..., ensure_ascii=False)` が L162 にあるため)。
- `LC_ALL=C` 単独では Python 3.14 は PEP 538 (locale coercion) と PEP 540 (UTF-8 mode) により
  stdout が UTF-8 になることを実測した。決定的な再現条件は `PYTHONIOENCODING=ascii` のような
  明示的な encoding 指定である。
- 非 ASCII の detail は実運用で発生し得る。`check_probe_snapshot` は probe の title / artist を
  detail に含み、`check_from_process` は waydroid / playerctl の command 出力を detail に含む。
  同梱 fixture の title / artist は ASCII だが、実機の Apple Music metadata は非 ASCII になり得る。
- `which → None` の既存 unit test 経路では detail がすべて ASCII に固定されるため、非 UTF-8
  crash は既存 test では再現しない。非 ASCII detail を `main()` まで流すには
  `subprocess.run` と `AdbRecoveryManager` の stub が必要である。
- `--json` 使用時の書き込みは `sys.stdout.write(render_json_report(checks))` (L146) の 1 箇所で、
  人間可読出力と exit code 規則は `--json` の有無で共有されていることを確認した。

## 下調べで見たもの

- `scripts/doctor.py` — 変更対象。FAIL 集計の重複 (L151 / L156)、`--json` 時の書き込み経路
  (L146)、`ensure_ascii=False` (L162) を確認
- `tests/test_doctor_json.py` — 既存 test の構成を確認。`shutil.which` を None に固定し
  `subprocess.run` を raise する mock で外部 command を禁じ、`render_json_report` の helper
  test と `main()` の JSON 単一性 / rc=1 を検査する。IDD-022 の DEC-043 が stub test を避けた
  経緯の確認先
- `scripts/run-disruptive-waydroid-restart-qa.py` — `ensure_ascii=False` の先例。file への書き込み
  は `encoding="utf-8"` を明示し stdout は `print` であり、doctor の stdout 問題と条件が違うこと
  を確認
- `fixtures/probe/apple-music-playing.sample.json` — probe detail の非 ASCII 起点 (title / artist)
  の確認。同梱 fixture は ASCII であることを確認
- `_docs/intent/waydroid_mpris/idd-022/decision.md` — decision.md full schema と DEC-042
  (`ensure_ascii=False` の判断) の確認。本 lane の DEC がこの判断をどう変えるかの根拠
- `_docs/qa/waydroid_mpris/idd-022/qa.md` — qa_schema 5 の先例と、Round 2 の nit
  (集計式の重複) が本 lane の由来であることの確認
- `_docs/reference/waydroid_mpris/idd-022/reference.md` — reference.md の一行形式の先例を確認
- `scripts/validate-intent-delta.ts` — `scripts/` が workflow-sensitive prefix であり、対象 code
  変更には qa.md の `risk: High` 以上の下限があることを確認。risk High かつ DEC 新設の round では
  R2 を非発動にできない
- `scripts/validate-qa.ts` — `qa_schema: 5` の必須見出し 3 節と、`qa_status: planned` は Round 無し
  で許容されることを確認
- `scripts/validate-intent.ts` — DEC 見出しは `DEC-` 3 桁以上、INV 行は
  `- INV-nnn (from DEC-nnn):` 形式を要求することを確認。番号帯 DEC-101〜 / INV-020〜 は 3 桁
  zero padding で書く
- `README.md` — Diagnostics 節の `--json` 案内と unittest 列挙行の現状を確認。JSON の byte 列を
  固定する記述は無く、`ensure_ascii` の変更は README を必ずしも変えないことを確認
- `scripts/check-docs.sh` — area の記録検査の構成 (todo / doc-links / intent / qa / intent-delta
  等) を確認。baseline の赤は `validate-todo` (Core-Test-17) の 1 件のみ
- `/home/penne/dev/active/work/pi-web-idd/.agents/skills/writing/SKILL.md` — 文章の作法 (1 主張
  1 文、見出し 40 文字前後、出典は Why 側に書く) を確認

## Verification

- 関連 QA: `_docs/qa/waydroid_mpris/idd-024/qa.md`
