---
title: "QA: 公開ファイルを開発記録から独立させる"
status: active
qa_schema: 5
qa_status: verified
risk: Low
created_at: 2026-09-23
updated_at: 2026-09-24
references:
  - "_docs/intent/waydroid_mpris/idd-002/decision.md"
  - "_docs/reference/waydroid_mpris/idd-002/reference.md"
related_issues:
  - 1
related_prs: []
---

# QA: 公開ファイルを開発記録から独立させる

## Acceptance Criteria

- AC-001: `AGENTS.md` から records 依存の規則が消え、運用原則と Project Commands だけが残っている (`grep -nE "_docs|skill|check-docs|qa-review|docs-template|test-plan" AGENTS.md` が空)
- AC-002: `docs/usage.md` と `docs/assets/adb-authorization-timeout-setting.png` が存在し、`docs/usage.md` の画像参照が相対 path で有効である
- AC-003: `docs/usage.md` に records の path と task ID が出ない (`grep -nE "_docs/|Core-Test" docs/usage.md` が空)
- AC-004: `README.md` に `_docs` への link がなく、usage guide への link と文言が `docs/usage.md` を指している
- AC-005: `QUICKSTART.md` から docs 検査と records workflow の記述が消えている (`grep -nE "check-docs|docs-inventory|implementation-prep|qa-review|docs-template|DD_SCOPE|PARTIAL verification" QUICKSTART.md` が空)
- AC-006: `docs-ci.yml` の lint job に validator 系 step が存在せず、markdownlint globs が `README.md` / `AGENTS.md` / `QUICKSTART.md` / `docs/**` に限られている
- AC-007: runtime 挙動が変わっていない (unittest / py_compile / shell syntax / install dry-run の public 4 check が緑)
- AC-008: public file 全体に records 参照が残っていない (`grep -rnE "_docs/|_evals/|check-docs|\\.agents/|\\.claude/|\\.codex/" README.md QUICKSTART.md AGENTS.md docs/ .github/` が空)
- AC-009: validator を個別実行した失敗が、既知の非互換 (成果物 3 file の `draft_status` 欠落、underscore area、`qa.md` の path) だけに限定され、usage.md 移動由来の失敗を含まない (q1 の回答により赤を許容)
- AC-010: `AGENTS.override.md` 上段の embed が、編集後の `AGENTS.md` と一致している (embed 部分の抽出結果と `AGENTS.md` の diff が空)

## Checks

| ID | Source | Requirement / Invariant | Check Type | Command / File | Status |
| --- | --- | --- | --- | --- | --- |
| AC-001 | DEC-022, DEC-023 | AGENTS.md から records 規則の除去 | command | `grep -nE "_docs|skill|check-docs|qa-review|docs-template|test-plan" AGENTS.md` | verified |
| AC-002 | DEC-024, INV-010 | guide と画像の移動と参照の有効性 | command | `test -f docs/usage.md && test -f docs/assets/adb-authorization-timeout-setting.png` と usage.md 内の相対画像参照の目視 | verified |
| AC-003 | DEC-025, INV-011 | usage.md から records 言及の除去 | command | `grep -nE "_docs/|Core-Test" docs/usage.md` | verified |
| AC-004 | DEC-027, DEC-028 | README の link 更新 | diff-review | `README.md` の link と文言を目視で突き合わせ | verified |
| AC-005 | DEC-026, DEC-030 | QUICKSTART から docs workflow の除去 | command | `grep -nE "check-docs|docs-inventory|implementation-prep|qa-review|docs-template|DD_SCOPE|PARTIAL verification" QUICKSTART.md` | verified |
| AC-006 | DEC-031, DEC-032, INV-012, INV-013 | CI lint job の構成 | diff-review | `.github/workflows/docs-ci.yml` の lint job を目視で突き合わせ | verified |
| AC-007 | DEC-021, INV-008 | runtime 挙動の不変 | command | unittest / py_compile / shell syntax / install dry-run の public 4 check | verified |
| AC-008 | INV-011 | public file 全体の records 参照の不在 | command | `grep -rnE "_docs/|_evals/|check-docs|\\.agents/|\\.claude/|\\.codex/" README.md QUICKSTART.md AGENTS.md docs/ .github/` | verified |
| AC-009 | DEC-033, DEC-034 | records 検査の赤が既知の非互換のみ | command | `bash scripts/check-docs.sh` は frontmatter の失敗で短絡するため、`deno run --allow-read --allow-env --allow-run=git scripts/validate-frontmatter.mjs` / `validate-doc-links.mjs` / `validate-intent.mjs` / `validate-qa.mjs` を個別実行して失敗原因を確認 | verified |
| AC-010 | DEC-022 | embed の一致 | command | `sed -n '/embed:begin AGENTS.md/,/embed:end AGENTS.md/p' AGENTS.override.md` の抽出結果と `AGENTS.md` の diff | verified |

## Rounds

<!-- 追記専用。実装後に Round を追記する。 -->

### Round 1 (2026-09-24)

- **Intent Delta**: applied: DEC-021, DEC-022, DEC-023, DEC-024, DEC-025, DEC-026, DEC-027, DEC-028, DEC-029, DEC-030, DEC-031, DEC-032, DEC-033, DEC-034
- **R2**: 非発動 (Intent Delta は既存 DEC の applied のみ、risk Low)
- **Verdict**: PASS (AC-009 の records 赤は DEC-034 / q1 の許容範囲)

実施内容:

- `AGENTS.md` を運用原則 5 項目と Project Commands だけに再構成し、documentation / skill / QA / intent comment / security / template の規則と docs check 行を外した (DEC-022 / DEC-023)。`AGENTS.override.md` 上段の embed を新しい `AGENTS.md` と byte-identical に同期した (DEC-022)
- `_docs/guide/Core/waydroid-mpris-bridge/usage.md` を `docs/usage.md` へ、同 `assets/adb-authorization-timeout-setting.png` を `docs/assets/` へ `git mv` した (DEC-024)。`docs/usage.md` の records frontmatter を外し、本文の `_docs/qa/...` 言及と `Core-Test-17` を、disruptive 検証が未実施で明示承認が要る旨の平文に置き換えた (DEC-025)
- `README.md` の verification record 段落を削除し (DEC-027)、usage guide link と文言を `docs/usage.md` へ向け (DEC-028)、Development Checks から `check-docs.sh` 行と docs workflow 段落を外した (DEC-029)
- `QUICKSTART.md` §1 に `docs/usage.md` link を足し、§4 の PARTIAL verification 文言を平文に置き換え (DEC-026)、§6 から docs check / skills / template 節を外した (DEC-030)
- `.github/workflows/docs-ci.yml` の markdownlint globs を `README.md` / `AGENTS.md` / `QUICKSTART.md` / `docs/**/*.md` に限定し (DEC-031)、Setup Deno と documentation validators step を外して fetch-depth を 1 に戻した (DEC-032)
- `_docs/plan/Core/waydroid-adb-auto-recovery/plan.md` の frontmatter reference から、移動で切れる `_docs/guide/Core/waydroid-mpris-bridge/usage.md` を削除した (DEC-033)
- 検証: AC-001〜AC-008 / AC-010 は緑。public 4 check (unittest 38 tests / py_compile / shell syntax / install dry-run) は緑 (AC-007)。AC-009 は `check-docs.sh` が frontmatter で短絡し、個別実行した `validate-frontmatter` / `validate-doc-links` / `validate-intent` / `validate-qa` の失敗が成果物 3 file の `draft_status` 欠落・underscore area・`qa.md` path に限られることを確認した (usage.md 移動由来の失敗なし)
