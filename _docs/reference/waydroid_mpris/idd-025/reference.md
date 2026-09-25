---
title: "MPRIS Position の lead offset — 下調べで見たもの"
status: active
created_at: 2026-09-25
updated_at: 2026-09-25
references:
  - "_docs/intent/waydroid_mpris/idd-025/decision.md"
  - "_docs/qa/waydroid_mpris/idd-025/qa.md"
related_issues:
  - 9
related_prs: []
---

# MPRIS Position の lead offset — 下調べで見たもの

## Overview

- IDD-025 (MPRIS Position の opt-in lead offset、issue #9) の下調べで参照した file と、
  その理由の記録。
- baseline の確認結果: unittest discover 57 tests / py_compile / shell syntax / install dry-run
  は緑。
- records 検査には既存の赤が 1 件ある。`validate-todo` が TODO.md の Core-Test-17 で失敗する。
  本 lane の変更前から存在し、成果物とは無関係である。
- 下調べ中の質問回答: q1 = 負の lead も受け付ける。q2 = 再生状態に関係なく lead を加える。
- plan review (1 回目) の指摘を受けて、以下を足した。負の lead の曲頭で起きる書き戻しの前進への
  対処、配線の test、test file の列挙への登録、AC-014 の検査 command の差し替えである。

## 確認した事実

- 実装は `origin/feat/mpris-position-lead` の commit `4aa08c6` にある。分岐元は `8308175` で、
  `main` には merge されていない。
- `4aa08c6` がコードと test で触る 6 file (`host/waydroid_mpris/position.py`、
  `host/waydroid_mpris/mpris_service.py`、`scripts/run-host-mpris-live.py`、
  `scripts/install-user-service.sh`、`tests/test_position_projection.py`、
  `tests/test_mpris_position_lead.py`) は、分岐元から現 HEAD まで変わっていない。
  `git show 4aa08c6 -- host scripts tests | git apply --check` は通った。
- `4aa08c6` は現行規約に合わない行を持つ。`position.py` と `mpris_service.py` に
  `# intent: DEC-007` があり、test に `# Covers AC-xxx` がある。
- 常駐の user service の unit は `/home/penne/dev/incubator/waydroid_mpris` (branch `main`) を
  指し、`ExecStart` に `--position-lead-ms "485"` を持つ。journal には
  `unrecognized arguments: --position-lead-ms 485` と status=2/INVALIDARGUMENT の終了が
  記録されている。service は inactive である。
- `Seek` は `position_projector.position_us()` を基準にしている。`SetPosition` は受け取った
  µs を ms に切り捨てて送っている。`PropertiesChanged` の発火判定 `_player_fingerprint` は
  projector ではなく probe の生の位置を使う。
- 既定の install dry-run の `ExecStart` は `--poll-interval "1.0"` だけを持つ。
  `4aa08c6` は lead が 0 のとき引数を書かないので、既定の出力は変わらない。
- `/usr/bin/python3` で `dbus` 1.4.0 を import できる。`mpris_service` を import する test も
  required の unittest check で走る。
- `4aa08c6` の projector を一時 directory に展開し、一時停止の session で `SetPosition` の往復を
  計算した。lead -400 ms・実位置 100 ms では公開値 0、送出 400 ms (+300 ms) になった。
  lead 400 ms・曲の長さの 100 ms 手前では送出が実位置より 300 ms 後ろになった。
  clamp されない位置では正負どちらの lead でも送出は実位置と一致した。
- CI の `Run host unit tests` は test file を列挙しており、`python3-dbus` を apt で入れている。
  `README.md` L142 と `QUICKSTART.md` L102 も同じ列挙を持つ。`AGENTS.md` L20 の列挙は既に
  `test_android_setup.py` / `test_doctor_json.py` / `test_doctor_quiet.py` を欠いている。
- local の `main` は `8308175` を指し、lane の基点 (`work-main` / HEAD `c8c471f`) とは 76 file 離れている。
  `git diff main` は template 移行の差分を含むので、注記の検査には使えない。
- `validate-comments.ts` は TS / JS だけを検査し、Python の注記は機械検査されない。
  注記が無いことは diff の grep で確かめる必要がある。

## 下調べで見たもの

- `host/waydroid_mpris/position.py` — 変更対象。`PositionProjector` の clamp と `position_us()` の現状を確認
- `host/waydroid_mpris/mpris_service.py` — 変更対象。`Seek` / `SetPosition` / `_player_properties` / `serve_live` と `_player_fingerprint` の位置の扱いを確認
- `scripts/run-host-mpris-live.py` — 変更対象。現行の argparse に `--position-lead-ms` が無いことを確認
- `scripts/install-user-service.sh` — 変更対象。option 解析と `ExecStart` の組み立て、既定 dry-run の出力を確認
- `tests/test_position_projection.py` — 変更対象。固定 clock と fixture session を使う既存 test の構成を確認
- `docs/usage.md` — 利用者向け説明の置き場。live daemon と installer の節の現状を確認
- `README.md` — unittest の列挙行 (L142) と live daemon の起動例の現状を確認
- `fixtures/probe/apple-music-playing.sample.json` — test が使う session の位置と曲の長さの出どころ
- `git show 4aa08c6` — 旧実装のコード・test・旧 layout の設計記録 (DEC-007 / INV-008 / candidate DEC-008) と旧 usage の追記を確認
- `scripts/validate-comments.ts` — governance 注記の検査対象が TS / JS だけであることを確認
- `scripts/validate-intent.ts` — DEC 見出しは 3 桁以上、INV 行は `- INV-nnn (from DEC-nnn):` 形式であることを確認。番号帯 INV-41〜 は 3 桁の INV-041〜 で書く
- `scripts/validate-qa.ts` — `qa_schema: 5` の必須 3 節と、`qa_status: planned` は Round 無しで許容されることを確認
- `scripts/validate-intent-delta.ts` — `scripts/` のパス下限で qa.md に `risk: High` 以上が要ることを確認
- `scripts/check-docs.sh` — records 検査の構成を確認。baseline の赤は `todo` の 1 件のみ
- `_docs/intent/waydroid_mpris/idd-024/decision.md` — decision.md full schema の先例を確認
- `_docs/qa/waydroid_mpris/idd-024/qa.md` — qa_schema 5 と Checks 表の先例を確認
- `_docs/reference/waydroid_mpris/idd-024/reference.md` — reference.md の一行形式の先例を確認
- `/home/penne/dev/active/work/pi-web-idd/.agents/skills/writing/SKILL.md` — 文章の作法 (1 主張 1 文、見出し 40 文字前後) を確認
- `journalctl --user -u waydroid-mpris` — 常駐 service の起動失敗の原因を確認
- `.github/workflows/docs-ci.yml` — CI が unittest の test file を列挙していることと、`python3-dbus` を入れていることを確認
- `QUICKSTART.md` — unittest の列挙行 (L102) の現状を確認
- `AGENTS.md` — Unit checks の列挙行 (L20) が既に古いことを確認
- `scripts/run-host-mpris-live.py` の `main()` と `mpris_service.serve_live` — 配線の test で差し替える依存の範囲を確認
- `/home/penne/dev/active/work/pi-web-idd/state/pipeline/plan-review/IDD-025-1-plan-reviewer/plan-review.md` — plan review の指摘の元
- `/home/penne/dev/active/work/pi-web-idd/state/pipeline/plan-review/IDD-025-1-plan-reviewer-flash/plan-review.md` — plan review の指摘の元

## Verification

- 関連 QA: `_docs/qa/waydroid_mpris/idd-025/qa.md`
