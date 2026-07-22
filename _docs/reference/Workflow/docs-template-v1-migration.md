---
title: Docs template v1 migration inventory
status: active
draft_status: n/a
created_at: 2026-07-22
updated_at: 2026-07-22
references:
  - "_docs/plan/Workflow/docs-template-v1-migration/plan.md"
  - "_docs/intent/Workflow/docs-template-v1-migration/decision.md"
  - "_docs/qa/Workflow/docs-template-v1-migration/test-plan.md"
  - "_docs/qa/Workflow/docs-template-v1-migration/verification.md"
related_issues: []
related_prs: []
---

# Docs template v1 migration inventory

## Provenance and cutoff

- Project: `/home/penne/dev/incubator/waydroid_mpris`
- Isolated worktree: `/tmp/docs-template-v1-rollout/waydroid_mpris`
- Cutoff: `2026-07-22T13:18:44+09:00`
- P: `43dd1b9d17ef4102ee3acacf95c1265056bed801`, clean and equal to
  `main` / `origin/main`; staged, unstaged, and untracked manifests were empty.
- B: `8c6039971b77f51f33e84bd9d1205365f634c049`, owner-confirmed legacy
  template commit, retained locally as `jj/keep/8c603997...`.
- U: annotated tag `v1.0.0` object
  `6a393ae11dbada5ecc38994762cb0710e7d4849d`, peeled commit
  `f71e9ab20466ea2972158334261f5ae2b2265754`.
- Source: `https://github.com/penne-0505/docs_driven_dev_template.git`.
- Destination branch: `codex/docs-template-v1-rollout-waydroid-mpris`.
- Ownership: this worktree only. Main, remote refs, active checkout, and other
  repositories are outside scope.
- Included lane: exactly B to U. Excluded: moving tips, unmerged branches, and
  upstream lifecycle/template-self history.

The upstream tag was resolved from the source repository with
`git -C /home/penne/dev/tools/templates/docs_driven_dev_template rev-parse refs/tags/v1.0.0^{}`.

## Classification and vocabulary

The table is the union of the upstream delta B to U and project delta B to P.
Every path has one upstream state, one project relation, exactly one resolution
from `apply`, `merge`, `keep`, `remove`, `defer`, and a separate disposition
that records its final state.

Resolution totals: apply=55, merge=19, keep=51, remove=7, defer=11. Total rows: 143.

## Three-way inventory

| Path | B to U | Relation at P | Resolution | Final disposition | Rationale |
| --- | --- | --- | --- | --- | --- |
| `.agents/skills/docs-cleanup/SKILL.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `.agents/skills/docs-inventory/SKILL.md` | added | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `.agents/skills/docs-prep/SKILL.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `.agents/skills/docs-template-migration/SKILL.md` | added | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `.agents/skills/frontend-design/SKILL.md` | removed | customized shared | remove | already absent at P and final; no migration deletion | P already omitted the obsolete template path and U also omits it |
| `.agents/skills/implementation-prep/SKILL.md` | modified | customized shared | merge | P contract merged with reviewed U behavior | shared path required preservation review rather than blind replacement |
| `.agents/skills/post-implementation/SKILL.md` | modified | customized shared | merge | P contract merged with reviewed U behavior | shared path required preservation review rather than blind replacement |
| `.agents/skills/qa-prep/SKILL.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `.agents/skills/qa-review/SKILL.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `.agents/skills/test-maintenance/SKILL.md` | modified | customized shared | merge | P contract merged with reviewed U behavior | shared path required preservation review rather than blind replacement |
| `.claude/settings.json` | added | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `.claude/skills/docs-cleanup/SKILL.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `.claude/skills/docs-inventory/SKILL.md` | added | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `.claude/skills/docs-prep/SKILL.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `.claude/skills/docs-template-migration/SKILL.md` | added | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `.claude/skills/frontend-design/SKILL.md` | removed | customized shared | remove | already absent at P and final; no migration deletion | P already omitted the obsolete template path and U also omits it |
| `.claude/skills/implementation-prep/SKILL.md` | modified | customized shared | merge | P contract merged with reviewed U behavior | shared path required preservation review rather than blind replacement |
| `.claude/skills/post-implementation/SKILL.md` | modified | customized shared | merge | P contract merged with reviewed U behavior | shared path required preservation review rather than blind replacement |
| `.claude/skills/qa-prep/SKILL.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `.claude/skills/qa-review/SKILL.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `.claude/skills/test-maintenance/SKILL.md` | modified | customized shared | merge | P contract merged with reviewed U behavior | shared path required preservation review rather than blind replacement |
| `.codex/hooks.json` | added | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `.github/workflows/docs-ci.yml` | modified | customized shared | merge | P contract merged with reviewed U behavior | shared path required preservation review rather than blind replacement |
| `.gitignore` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `AGENTS.md` | modified | customized shared | merge | P contract merged with reviewed U behavior | shared path required preservation review rather than blind replacement |
| `QUICKSTART.md` | modified | customized shared | merge | P contract merged with reviewed U behavior | shared path required preservation review rather than blind replacement |
| `README.md` | modified | customized shared | merge | P contract merged with reviewed U behavior | shared path required preservation review rather than blind replacement |
| `TODO.md` | modified | customized shared | merge | P contract merged with reviewed U behavior | shared path required preservation review rather than blind replacement |
| `_docs/documentation_guide.md` | modified | customized shared | merge | P contract merged with reviewed U behavior | shared path required preservation review rather than blind replacement |
| `_docs/guide/Core/waydroid-mpris-bridge/usage.md` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `_docs/intent/Core/reproducible-arch-setup/decision.md` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `_docs/intent/Core/waydroid-adb-auto-recovery/decision.md` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `_docs/intent/Core/waydroid-mpris-bridge/decision.md` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `_docs/intent/Template/intent-qa-finalization/decision.md` | removed | customized shared | remove | already absent at P and final; no migration deletion | P already omitted the obsolete template path and U also omits it |
| `_docs/intent/Workflow/code-intent-traceability/decision.md` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `_docs/intent/Workflow/incremental-adoption-scope/decision.md` | removed | upstream-owned unmodified | defer | retained as referenced legacy record | active P references make the no-project-reference deletion gate false |
| `_docs/intent/Workflow/intentional-omission-risk/decision.md` | removed | upstream-owned unmodified | defer | retained as referenced legacy record | active P references make the no-project-reference deletion gate false |
| `_docs/intent/Workflow/lifecycle-self-audit/decision.md` | added | upstream-owned unmodified | defer | excluded; absent from final tree | U template-self history is not a downstream project record |
| `_docs/plan/Core/reproducible-arch-setup/plan.md` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `_docs/plan/Core/waydroid-adb-auto-recovery/plan.md` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `_docs/plan/Core/waydroid-mpris-bridge/plan.md` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `_docs/plan/Template/intent-qa-finalization/plan.md` | removed | customized shared | remove | already absent at P and final; no migration deletion | P already omitted the obsolete template path and U also omits it |
| `_docs/plan/Workflow/code-intent-traceability/plan.md` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `_docs/plan/Workflow/incremental-adoption-scope/plan.md` | removed | upstream-owned unmodified | defer | retained as referenced legacy record | active P references make the no-project-reference deletion gate false |
| `_docs/plan/Workflow/lifecycle-self-audit/plan.md` | added | upstream-owned unmodified | defer | excluded; absent from final tree | U template-self history is not a downstream project record |
| `_docs/qa/Core/reproducible-arch-setup/test-plan.md` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `_docs/qa/Core/reproducible-arch-setup/verification.md` | unchanged | project-only | merge | project content retained with local CI-lint fix | project-only record changed only to satisfy full local markdownlint |
| `_docs/qa/Core/waydroid-adb-auto-recovery/test-plan.md` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `_docs/qa/Core/waydroid-adb-auto-recovery/verification.md` | unchanged | project-only | merge | project content retained with local CI-lint fix | project-only record changed only to satisfy full local markdownlint |
| `_docs/qa/Core/waydroid-mpris-bridge/test-plan.md` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `_docs/qa/Core/waydroid-mpris-bridge/verification.md` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `_docs/qa/Template/intent-qa-finalization/test-plan.md` | removed | customized shared | remove | already absent at P and final; no migration deletion | P already omitted the obsolete template path and U also omits it |
| `_docs/qa/Template/intent-qa-finalization/verification.md` | removed | customized shared | remove | already absent at P and final; no migration deletion | P already omitted the obsolete template path and U also omits it |
| `_docs/qa/Workflow/code-intent-traceability/test-plan.md` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `_docs/qa/Workflow/code-intent-traceability/verification.md` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `_docs/qa/Workflow/incremental-adoption-scope/test-plan.md` | removed | upstream-owned unmodified | defer | retained as referenced legacy record | active P references make the no-project-reference deletion gate false |
| `_docs/qa/Workflow/incremental-adoption-scope/verification.md` | removed | upstream-owned unmodified | defer | retained as referenced legacy record | active P references make the no-project-reference deletion gate false |
| `_docs/qa/Workflow/intentional-omission-risk/test-plan.md` | removed | upstream-owned unmodified | defer | retained as referenced legacy record | active P references make the no-project-reference deletion gate false |
| `_docs/qa/Workflow/intentional-omission-risk/verification.md` | removed | upstream-owned unmodified | defer | retained as referenced legacy record | active P references make the no-project-reference deletion gate false |
| `_docs/qa/Workflow/lifecycle-self-audit/test-plan.md` | added | upstream-owned unmodified | defer | excluded; absent from final tree | U template-self history is not a downstream project record |
| `_docs/qa/Workflow/lifecycle-self-audit/verification.md` | added | upstream-owned unmodified | defer | excluded; absent from final tree | U template-self history is not a downstream project record |
| `_docs/reference/Core/bridge-protocol/reference.md` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `_docs/standards/documentation_guidelines.md` | modified | customized shared | merge | P contract merged with reviewed U behavior | shared path required preservation review rather than blind replacement |
| `_docs/standards/documentation_operations.md` | modified | customized shared | merge | P contract merged with reviewed U behavior | shared path required preservation review rather than blind replacement |
| `_docs/standards/jj_workflow.md` | removed | customized shared | remove | already absent at P and final; no migration deletion | P already omitted the obsolete template path and U also omits it |
| `_docs/standards/quality_assurance.md` | modified | customized shared | merge | P contract merged with reviewed U behavior | shared path required preservation review rather than blind replacement |
| `_docs/standards/templates/intent.md` | modified | customized shared | merge | P contract merged with reviewed U behavior | shared path required preservation review rather than blind replacement |
| `_docs/standards/templates/plan.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_docs/standards/templates/qa-test-plan.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_docs/standards/templates/qa-verification.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_docs/survey/Core/waydroid-mpris-bridge/survey.md` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `_evals/agent-workflows/README.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/agent-workflows/cases/archive-flow.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/agent-workflows/cases/breaking-change.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/agent-workflows/cases/experimental-baseline.md` | added | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/agent-workflows/cases/historical-prompt-not-operational.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/agent-workflows/cases/intentional-omission-risk.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/agent-workflows/cases/medium-feature.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/agent-workflows/cases/misleading-optimization.md` | added | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/agent-workflows/cases/qa-prep-from-intent.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/agent-workflows/cases/rationale-preserving-change.md` | added | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/agent-workflows/cases/refactor-behavior-preservation.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/agent-workflows/cases/small-bug.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/agent-workflows/cases/stale-draft-cleanup.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/agent-workflows/cases/template-version-migration.md` | added | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/agent-workflows/expected-invariants.md` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/validator-fixtures/README.md` | modified | upstream-owned unmodified | merge | P contract merged with reviewed U behavior | final content differs from both P and U after compatibility reconciliation |
| `_evals/validator-fixtures/intent/invalid/missing-why.md` | added | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/validator-fixtures/intent/invalid/orphan-invariant.md` | added | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/validator-fixtures/intent/valid/decision.md` | added | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/validator-fixtures/links/valid-reference-anchor.md` | added | upstream-owned unmodified | apply | U behavior integrated with project-local hardening | local fixture, type-specific schema, anchor, or intent adaptation preserves U purpose |
| `_evals/validator-fixtures/qa/invalid/missing-invariant.md` | modified | customized shared | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/validator-fixtures/qa/invalid/qa-archive-path.md` | modified | customized shared | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/validator-fixtures/qa/invalid/status-verdict-mismatch.md` | modified | customized shared | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/validator-fixtures/qa/invalid/v2-missing-decision-scope.md` | added | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/validator-fixtures/qa/invalid/verification-in-progress-status.md` | modified | customized shared | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/validator-fixtures/qa/invalid/verification-missing-test-plan-reference.md` | modified | customized shared | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/validator-fixtures/qa/valid/test-plan.md` | modified | customized shared | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `_evals/validator-fixtures/qa/valid/verification-pass.md` | modified | customized shared | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `android/probe/src/main/AndroidManifest.xml` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `android/probe/src/main/java/dev/penne/waydroidmpris/probe/BridgeCommandReceiver.java` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `android/probe/src/main/java/dev/penne/waydroidmpris/probe/MainActivity.java` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `android/probe/src/main/java/dev/penne/waydroidmpris/probe/ProbeNotificationListener.java` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `android/probe/src/main/java/dev/penne/waydroidmpris/probe/ProbeRunner.java` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `android/probe/src/main/res/values/strings.xml` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `android/probe/src/main/res/values/styles.xml` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `docs-template.lock.example.json` | added | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `fixtures/probe/apple-music-playing.sample.json` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `host/waydroid_mpris/__init__.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `host/waydroid_mpris/adb_recovery.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `host/waydroid_mpris/adb_transport.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `host/waydroid_mpris/artwork.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `host/waydroid_mpris/mpris_service.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `host/waydroid_mpris/position.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `host/waydroid_mpris/protocol.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `packaging/systemd/waydroid-mpris.service` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `scripts/agent-workflow-hook.mjs` | added | upstream-owned unmodified | apply | U behavior integrated with project-local hardening | local fixture, type-specific schema, anchor, or intent adaptation preserves U purpose |
| `scripts/android-sdk-env.sh` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `scripts/build-android-probe.sh` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `scripts/check-docs.sh` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `scripts/doctor.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `scripts/install-android-probe.sh` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `scripts/install-user-service.sh` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `scripts/open-android-notification-listener-settings.sh` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `scripts/resolve-waydroid-adb-target.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `scripts/run-disruptive-waydroid-restart-qa.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `scripts/run-host-mpris-fixture.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `scripts/run-host-mpris-live.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `scripts/scope.mjs` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `scripts/test-agent-workflow-hook.mjs` | added | upstream-owned unmodified | apply | U behavior integrated with project-local hardening | local fixture, type-specific schema, anchor, or intent adaptation preserves U purpose |
| `scripts/test-agent-workflow-smoke.mjs` | added | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `scripts/test-validators.mjs` | modified | upstream-owned unmodified | apply | U behavior integrated with project-local hardening | local fixture, type-specific schema, anchor, or intent adaptation preserves U purpose |
| `scripts/validate-doc-links.mjs` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `scripts/validate-frontmatter.mjs` | modified | upstream-owned unmodified | apply | U behavior integrated with project-local hardening | local fixture, type-specific schema, anchor, or intent adaptation preserves U purpose |
| `scripts/validate-intent.mjs` | added | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `scripts/validate-qa.mjs` | modified | upstream-owned unmodified | apply | integrated exact U content | reusable distribution path has no retained project semantic delta |
| `tests/test_adb_recovery.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `tests/test_adb_transport.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `tests/test_android_setup.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `tests/test_artwork_cache.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `tests/test_live_failure_mapping.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `tests/test_position_projection.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |
| `tests/test_protocol_mapping.py` | unchanged | project-only | keep | preserved byte-identical to P | project-only runtime, helper, docs, test, or configuration path |

## Migration-created artifact manifest

These paths were absent from the initial union. They are tracked separately so
final raw diff reconciliation also covers migration output.

| Path | Resolution | Final disposition | Rationale |
| --- | --- | --- | --- |
| `_docs/plan/Workflow/docs-template-v1-migration/plan.md` | apply | created | migration contract |
| `_docs/intent/Workflow/docs-template-v1-migration/decision.md` | apply | created | durable why-first decisions |
| `_docs/qa/Workflow/docs-template-v1-migration/test-plan.md` | apply | created | pre-implementation QA matrix |
| `_docs/qa/Workflow/docs-template-v1-migration/verification.md` | apply | created | closure evidence |
| `_docs/reference/Workflow/docs-template-v1-migration.md` | apply | created | inventory and reconciliation |
| `docs-template.lock.json` | apply | created as final migration write | exact U provenance |
| `_evals/validator-fixtures/frontmatter/valid/intent-schema.md` | apply | created | intent schema acceptance fixture |
| `_evals/validator-fixtures/frontmatter/valid/qa-schema.md` | apply | created | QA schema acceptance fixture |
| `_evals/validator-fixtures/frontmatter/warning/intent-schema-on-plan.md` | apply | created | type-specific unknown warning fixture |
| `_evals/validator-fixtures/frontmatter/warning/qa-schema-on-intent.md` | apply | created | type-specific unknown warning fixture |
| `_evals/validator-fixtures/frontmatter/warning/unknown-field.md` | apply | created | generic unknown warning fixture |
| `_evals/validator-fixtures/frontmatter/invalid/duplicate-key.md` | apply | created | duplicate frontmatter rejection fixture |

## Final raw diff reconciliation

- Initial three-way union: 143 paths.
- Migration-created manifest: 12 paths.
- Final raw diff: 86 paths (54 tracked, 32 untracked before commit).
- Raw diff paths missing from inventory or artifact manifest: 0.
- Untracked paths missing from the artifact manifest or initial union: 0.
- Migration deletions from P: 0.

The check compares `git diff --name-only P` plus
`git ls-files --others --exclude-standard` against both path tables. Inventory
rows intentionally include unchanged final paths because the migration skill
requires the complete B-to-U and B-to-P union, not only the resulting diff.

## Deletion and lifecycle disposition

No tracked path was deleted merely because U omits it. The old frontend-design,
Template intent-qa-finalization, and jj workflow paths were already absent at P
and remain absent, so the migration performs no deletion for them.

The seven incremental-adoption / intentional-omission records are retained with
`defer` because active P references make the no-project-reference gate false.
The four U lifecycle-self-audit records are excluded additions and are absent
from the final tree. Hook intent anchors point to this project's DEC-006 rather
than to excluded template-self records.

## Schema disposition

- Compatibility migration: PASS. Legacy project docs remain accepted by U
  validators, while new migration docs use `intent_schema: 2` / `qa_schema: 2`.
- Strict schema migration: DEFERRED. Historical project intent / QA records were
  not bulk rewritten without semantic review. `Workflow-Chore-20` tracks the
  bounded review before a future release removes legacy acceptance.
- Support horizon: legacy compatibility is relied on only for the integrated U
  release. It is not a permanent project schema guarantee.

## Preservation boundary

Project runtime, Android sources, project fixtures, packaging, helper scripts,
and project tests remain byte-identical to P. README, QUICKSTART, AGENTS,
project CI, shared standards, and three locally customized paired skills were
merged rather than blindly replaced. The migration did not stop Waydroid,
disconnect ADB, reinstall the APK, update main, push, or modify remote refs.
