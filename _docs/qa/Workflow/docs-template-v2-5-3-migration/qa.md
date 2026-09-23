---
title: "QA: docs template v1.0.0 → v2.5.3 migration"
status: active
qa_status: partial
risk: High
qa_schema: 4
created_at: 2026-08-18
updated_at: 2026-08-18
references:
  - "_docs/standards/workflow.md"
  - "_docs/standards/document_contracts.md"
  - "_docs/standards/template_operations.md"
related_issues: []
related_prs: []
---

# QA: `docs template v1.0.0 → v2.5.3 migration`

<!-- Canonical path: _docs/qa/Workflow/docs-template-v2.5.3-migration/qa.md -->
<!-- three-way migration (B=v1.0.0 / U=v2.5.3 / P=jj @) の provenance と compatibility gate を記録する。
     strict schema migration は `Workflow-Chore-20` 継続で、本 qa.md は compatibility 側の gate を扱う。 -->

## Acceptance Criteria

- AC-001: `docs-template.lock.json` が v2.5.3 の tag と full SHA (`8fc1509b5c2c9807dd5edff3a5e46e1b169d2c35`) を、compatibility gate PASS 後に advance されている。
- AC-002: `./scripts/check-docs.sh` (U 版 Deno validator) が **error なし** で完走する。warning は「見える未完了」として許容し、Workflow-Chore-20 で継続する。
- AC-003: `python -m unittest tests/test_*.py` (project's own build gate) が baseline (33 tests PASS) から regression していない。
- AC-004: paired skill tree (`.claude/skills/` と `.agents/skills/`) が v2.5.3 の 5 skills (`close`, `docs-inventory`, `docs-template-migration`, `intent-mining`, `prep`) に揃い、旧 9 skills への参照が root docs (AGENTS.md / QUICKSTART.md / TODO.md) から除去されている。
- AC-005: `_evals/` → `_meta/` rename が `git mv` で実行され、history が保持されている。

## Checks

| ID | Source | Requirement / Invariant | Check Type | Command / File | Status |
| --- | --- | --- | --- | --- | --- |
| AC-001 | TODO | Lock advance is the final migration write and its SHA matches the recorded U tag. | manual | `docs-template.lock.json`; `git ls-remote --tags upstream v2.5.3` | planned |
| AC-002 | TODO | Documentation gate errors are zero; warnings enumerated. | validator | `./scripts/check-docs.sh` | covered |
| AC-003 | TODO | Project's own test gate matches baseline. | unit | `python -m unittest tests/test_protocol_mapping.py tests/test_adb_transport.py tests/test_adb_recovery.py tests/test_live_failure_mapping.py tests/test_position_projection.py tests/test_artwork_cache.py` | planned |
| AC-004 | TODO | Paired skills synced; old-skill references removed from root docs. | diff-review | `diff -q .claude/skills .agents/skills`; `grep -RE 'docs-cleanup\|docs-prep\|implementation-prep\|post-implementation\|qa-prep\|qa-review\|test-maintenance' AGENTS.md QUICKSTART.md TODO.md` | covered |
| AC-005 | TODO | Rename preserves git history. | diff-review | `git log --follow -- _meta/agent-workflows/README.md` | covered |

## Rounds

### Round 1 (2026-08-18) — compatibility migration groundwork

- **Commands**:

  ```bash
  git ls-remote --tags --sort=-v:refname https://github.com/penne-0505/docs_driven_dev_template.git
  git clone --no-checkout https://github.com/penne-0505/docs_driven_dev_template.git \
    /tmp/scratchpad/upstream
  git worktree add /tmp/scratchpad/upstream-B v1.0.0
  git worktree add /tmp/scratchpad/upstream-U v2.5.3
  # Baseline (before write):
  ./scripts/check-docs.sh                                             # PASS (v1.0.0 validators)
  python -m unittest tests/test_protocol_mapping.py tests/test_adb_transport.py \
    tests/test_adb_recovery.py tests/test_live_failure_mapping.py \
    tests/test_position_projection.py tests/test_artwork_cache.py     # 33 tests PASS
  # Phase B non-destructive additions:
  cp /tmp/scratchpad/upstream-U/deno.json ./deno.json
  cp /tmp/scratchpad/upstream-U/scripts/*.ts ./scripts/
  cp /tmp/scratchpad/upstream-U/scripts/check-docs.sh ./scripts/check-docs.sh
  cp /tmp/scratchpad/upstream-U/starter/.claude/skills/{close,prep,intent-mining,docs-inventory,docs-template-migration}/SKILL.md \
    ./.claude/skills/*/  # paired copy to .agents/skills/ as well
  cp /tmp/scratchpad/upstream-U/_docs/standards/{document_contracts,template_operations,workflow}.md \
    ./_docs/standards/
  cp /tmp/scratchpad/upstream-U/_docs/standards/templates/qa.md ./_docs/standards/templates/qa.md
  cp /tmp/scratchpad/upstream-U/starter/.claude/settings.json ./.claude/settings.json
  cp /tmp/scratchpad/upstream-U/starter/.codex/hooks.json ./.codex/hooks.json
  cp /tmp/scratchpad/upstream-U/.github/workflows/docs-ci.yml ./.github/workflows/docs-ci.yml
  cp /tmp/scratchpad/upstream-U/docs-template.lock.example.json ./docs-template.lock.example.json
  # Rename:
  git mv _evals _meta
  cp -r /tmp/scratchpad/upstream-U/_meta/. ./_meta/
  # Root docs rewrite (semantic):
  # AGENTS.md updated to starter/AGENTS.md shape + Project Commands section preserved.
  # TODO.md updated to starter/TODO.md rules; existing backlog (Core-Test-17, Workflow-Chore-20) migrated.
  # QUICKSTART.md: implementation-prep/qa-review references migrated to prep/close.
  # Fixture anchor: _meta/validator-fixtures/links/valid-reference-anchor.md → QUICKSTART.md#4-verify.
  ./scripts/check-docs.sh   # zero errors, 21 warnings (legacy schema, tracked by Workflow-Chore-20)
  python -m unittest tests/test_protocol_mapping.py tests/test_adb_transport.py \
    tests/test_adb_recovery.py tests/test_live_failure_mapping.py \
    tests/test_position_projection.py tests/test_artwork_cache.py     # 33 tests PASS
  ```

- **AC Coverage**: AC-002 covered (0 errors), AC-003 covered (baseline maintained), AC-004 covered (paired skills synced, root docs cleaned), AC-005 covered (git mv preserves history). AC-001 planned (lock advance is the final write, executed on this round's closure).
- **Intent Delta**: None: migration は upstream template の provenance-locked update であり、project 固有の設計判断は導入しない。target tag (v2.5.3)、strict schema deferral、`security_for_agents.md` / `.markdownlint.jsonc` の削除方針はいずれも owner が session 内で明示承認した判断で、standards が既に持つ規範の下で機械的に選択される範囲。
- **R2**: PENDING — Risk High (path 自動下限、`_docs/standards/` / `.claude/` / `.agents/` / `.codex/` / `scripts/` / `AGENTS.md` に触れる)。次 session (実装時の文脈を持たない agent) が `docs-template.lock.json` 変更と本 qa.md、`_docs/standards/workflow.md` 固定 4 問への回答で再構成する。
- **Transferable Principles**: None: docs template の provenance-locked migration は `docs-template-migration` skill と `template_operations.md` に既に規範化されている。project 固有の一般則は今回抽出していない。
- **Verdict**: PARTIAL — compatibility gate は PASS。strict schema migration (21 legacy schema warnings) と旧 file の owner 手動削除は `Workflow-Chore-20` に引き継ぐ。lock advance は Verdict = PARTIAL でも provenance を残すために本 round 終了時に実施し、strict schema の残作業は本 qa.md 参照から Workflow-Chore-20 に継続する。
