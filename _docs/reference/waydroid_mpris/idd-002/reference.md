---
title: 公開ファイルを開発記録から独立させる — 下調べで見たもの
status: active
created_at: 2026-09-23
updated_at: 2026-09-23
references:
  - "_docs/intent/waydroid_mpris/idd-002/decision.md"
  - "_docs/qa/waydroid_mpris/idd-002/qa.md"
related_issues:
  - 1
related_prs: []
---

# 公開ファイルを開発記録から独立させる — 下調べで見たもの

## Overview

- IDD-002 (公開ファイルを開発記録から独立させる) の下調べで参照した file と、その理由の記録。
- baseline の確認結果: public 側 4 check (unittest 38 tests / py_compile / shell syntax / install dry-run) は緑。records 検査は CI と同じ scope (`DD_SCOPE_BASE=43dd1b9d...`, `DD_SCOPE_DIFF_FILTER=ACMR`) で緑 (未 commit の成果物は git diff に載らないため)。
- 下調べ中の質問回答: q1 = 赤を許容し validator には触らない (records 検査 `check-docs.sh` の赤は records 移出まで許容。docs CI は DEC-032 の validator step 削除により影響なし)。
- plan review (IDD-002-1) の指摘 F1〜F8 を現物で確認し、F1〜F5 と F8 を decision.md / qa.md に反映した。F6 は INV-011 の文言と Quality Implications の注記で、F7 は Rollback / Follow-ups で扱った。

## 下調べで見たもの

- `README.md` — 編集対象。verification record 2 link を含む段落、usage guide link、Development Checks の docs 検査行と docs workflow 段落を確認
- `QUICKSTART.md` — 編集対象。§1 の usage guide 言及、§4 の「separate PARTIAL verification」文言、§6 の docs 検査 / skills / template 節を確認
- `AGENTS.md` — 編集対象。残す運用原則と落とす records workflow 規則の線引き (9 行 + docs check 行) を確認
- `_docs/guide/Core/waydroid-mpris-bridge/usage.md` — 移動対象。records の frontmatter と本文 (`_docs/qa/...` への言及、`Core-Test-17`) を確認
- `_docs/guide/Core/waydroid-mpris-bridge/assets/adb-authorization-timeout-setting.png` — 移動対象の画像。usage.md が相対 path で参照していることを確認
- `.github/workflows/docs-ci.yml` — 編集対象。lint job の markdownlint globs (`_docs` / `_evals` / `TODO.md` を含む) と Deno + `check-docs.sh` step、runtime job の内容を確認
- `scripts/check-docs.sh` — area の records 検査の構成 (fmt / frontmatter / todo / doc-links / intent / qa / comments / hook / smoke) を確認。overlay 構成では smoke test を skip すること、`set -euo pipefail` により frontmatter の失敗で以降の validator が走らないことを確認
- `scripts/validate-intent.mjs` — 成果物の area 名 `waydroid_mpris` (underscore) が path 正規表現に合わず拒否されること、`intent_schema` は 2 しか受け付けないことを確認
- `scripts/validate-qa.mjs` — `qa.md` という file 名と `qa_schema: 5` が現行規則 (test-plan / verification, schema 2) に拒否されることを確認
- `scripts/validate-doc-links.mjs` — frontmatter reference の存在検証と QA path 検査で同じ拒否が起きること、`docs/` が `ROOT_RELATIVE_PREFIXES` に無く frontmatter reference の `docs/...` は directory 相対で解決されることを確認、`_docs/plan/Core/waydroid-adb-auto-recovery/plan.md` が usage.md を frontmatter reference に持つことを確認
- `scripts/validate-frontmatter.mjs` — 共通 frontmatter に `draft_status` が必須であること (IDD 成果物の schema とは一致しない) を確認
- `scripts/scope.mjs` — env 未設定の local 実行では scope が null (全走査) になり、成果物が検証対象になることを確認
- `_docs/plan/Core/waydroid-adb-auto-recovery/plan.md` — usage guide への frontmatter reference を確認 (DEC-033 の対象)
- `_docs/standards/documentation_guidelines.md` — `_docs` の path / frontmatter / `intent_schema: 2` の規約を確認。本 lane の成果物 schema がこの repo の規約と衝突することを確認
- `overlay.manifest` — public 側と records 側の境界 (records: `_docs` / `_meta` / `_evals` / `.agents` / `.claude` / `.codex` / validators / lock file 系) を確認
- `.markdownlint.jsonc` — `ignores` の `_docs/archives/**` が records 移出後に無効になることを確認 (follow-up)
- `.gitattributes` — `scripts/*.mjs linguist-vendored` 行が records 移出後に無効になることを確認 (follow-up)
- `CLAUDE.md` / `CLAUDE.local.md` — `@./AGENTS.md` 読み込みの構成と、`CLAUDE.local.md` が records 側であることを確認
- `AGENTS.override.md` — 上段 embed が `AGENTS.md` の byte-identical な写してあること、workspace 規範の正本であることを確認 (plan review F5)
- `/home/penne/dev/active/work/pi-web-idd/packages/idd-core/src/init/init.ts` — embed を再生成するのは `idd init` (`composeOverride`) だけで、AGENTS.md 編集後に同期するコマンドが無いことを確認
- `scripts/agent-workflow-hook.mjs` — docs 判定が `_docs/` prefix と root 4 file のみで `docs/` を含まないことを確認 (plan review F7)
- `_docs/intent/Core/waydroid-mpris-bridge/decision.md` — この repo の既存 decision.md の schema (6 節、`draft_status` あり) を確認
- `/home/penne/dev/active/work/pi-web-idd/_docs/intent/pi-web-idd/idd-904/decision.md` — IDD lane の decision.md (DEC 番号付き、What / Why / Change freedom / Anchors) の full schema の先例
- `/home/penne/dev/active/work/pi-web-idd/_docs/qa/pi-web-idd/idd-904/qa.md` — `qa_schema: 5` の qa.md (AC / Checks 表 / Rounds) の先例
- `/home/penne/dev/active/work/pi-web-idd/scripts/validate-intent.ts` / `validate-qa.ts` — IDD lane 形式 (underscore は除く area, `qa.md`, `intent_schema: 3`, `qa_schema: 5`) を受け付ける newer validator が別 repo に存在することを確認。underscore area は newer validator でも受け付けないことを確認
- `/home/penne/dev/active/work/pi-web-idd/.agents/skills/writing/SKILL.md` — 文章の作法 (1 主張 1 文、見出し 40 文字前後、出典を Why 側に書く) を確認
- `/home/penne/dev/active/work/pi-web-idd/state/pipeline/plan-review/IDD-002-1/plan-review.md` — 別 model の査読指摘 (F1〜F8) とその実測 (frontmatter 短絡、`git mv` の exit 128、doc-links の相対解決) の確認に使用

## Verification

- 関連 QA: `_docs/qa/waydroid_mpris/idd-002/qa.md`
