---
title: "QA Verification: Docs template v1 migration"
status: active
draft_status: n/a
qa_status: partial
risk: High
qa_schema: 2
created_at: 2026-07-22
updated_at: 2026-07-22
references:
  - "_docs/intent/Workflow/docs-template-v1-migration/decision.md"
  - "_docs/plan/Workflow/docs-template-v1-migration/plan.md"
  - "_docs/qa/Workflow/docs-template-v1-migration/test-plan.md"
  - "_docs/reference/Workflow/docs-template-v1-migration.md"
related_issues: []
related_prs: []
---

# QA Verification: `Docs template v1 migration`

## Summary

Compatibility migration from legacy B to pinned U is complete and passes all
docs, hook, paired-skill, project regression, provenance, and diff-preservation
checks. Strict schema migration is separately DEFERRED because historical
project intent / QA records require semantic review rather than bulk markers.

Overall Verdict: PARTIAL reflects the deferred strict-schema stage. It does not
indicate a compatibility, runtime, or provenance failure.

## Verification Verdict

Verdict: PARTIAL

Stage verdicts:

- Compatibility migration: PASS.
- Strict schema migration: DEFERRED.
- Provenance lock: PASS.

## Commands Run

```bash
date --iso-8601=seconds
git status --short --branch
git rev-parse HEAD origin/main main
git -C /home/penne/dev/tools/templates/docs_driven_dev_template   rev-parse refs/tags/v1.0.0 'refs/tags/v1.0.0^{}'

./scripts/check-docs.sh
DD_SCOPE_PATHS="$(git diff --name-only   43dd1b9d17ef4102ee3acacf95c1265056bed801 --   '_docs/**/*.md' '_evals/**/*.md')" ./scripts/check-docs.sh
npx --yes markdownlint-cli2 '_docs/**/*.md' '_evals/**/*.md'   README.md AGENTS.md TODO.md QUICKSTART.md   '!_docs/archives/**/*' '!_docs/standards/templates/**/*'   --config .markdownlint.jsonc
deno run --allow-read --allow-write --allow-env --allow-run   scripts/test-validators.mjs
deno run --allow-read --allow-run=git scripts/test-agent-workflow-hook.mjs
deno run --allow-read scripts/test-agent-workflow-smoke.mjs

python -m unittest tests/test_protocol_mapping.py   tests/test_adb_transport.py tests/test_adb_recovery.py   tests/test_live_failure_mapping.py tests/test_position_projection.py   tests/test_artwork_cache.py tests/test_android_setup.py
python -m py_compile host/waydroid_mpris/*.py   scripts/run-host-mpris-live.py scripts/run-host-mpris-fixture.py   scripts/doctor.py scripts/resolve-waydroid-adb-target.py   scripts/run-disruptive-waydroid-restart-qa.py
bash -n scripts/*.sh
PYTHON=/usr/bin/python ./scripts/install-user-service.sh --dry-run
./scripts/build-android-probe.sh
python scripts/resolve-waydroid-adb-target.py
python scripts/doctor.py
git diff --check
git diff --exit-code   43dd1b9d17ef4102ee3acacf95c1265056bed801 --   android host fixtures/probe packaging tests   scripts/android-sdk-env.sh scripts/build-android-probe.sh   scripts/doctor.py scripts/install-android-probe.sh   scripts/install-user-service.sh   scripts/open-android-notification-listener-settings.sh   scripts/resolve-waydroid-adb-target.py   scripts/run-disruptive-waydroid-restart-qa.py   scripts/run-host-mpris-fixture.py scripts/run-host-mpris-live.py
```

The final inventory reconciliation also compared
`git diff --name-only P` plus
`git ls-files --others --exclude-standard` with the initial union and
migration-created artifact manifest.

## Automated Test Results

| Command / Test | Result | Notes |
| --- | --- | --- |
| Baseline P docs wrapper | PASS | legacy validators before U import |
| U compatibility wrapper before shared merge | PASS | legacy docs accepted; reader-doc merge remained |
| Final unscoped docs wrapper | PASS | all validators, fixtures, hooks, smoke |
| Final scoped docs wrapper | PASS | explicit changed-doc scope; harness isolates nested fixture env |
| Full CI-equivalent markdownlint | PASS | 85 files, 0 issues |
| Frontmatter fixtures | PASS | correct schema type, unknown warnings, duplicate rejection |
| Hook unit / smoke / paired skills | PASS | all configured events and nine paired skills |
| Python unit tests | PASS | 38 tests |
| Python compile / shell syntax | PASS | all listed entry points and shell helpers |
| User service dry-run | PASS | generated unit uses isolated checkout |
| Android companion build | PASS | android-36.1 / Build-Tools 37.0.0 |
| ADB target resolution | PASS | `192.168.240.112:5555` resolved as `device` |
| Read-only doctor | PASS | Waydroid, companion, listener, probe, MPRIS all present |
| Runtime preservation diff | PASS | project runtime / helpers / packaging / tests unchanged from P |
| Raw diff reconciliation | PASS | 86 raw paths; 0 missing; 0 untracked manifest gaps |
| Lock provenance | PASS | tag `v1.0.0` peels to `f71e9ab...754` |

## Manual QA Results

| Checklist Item | Result | Notes |
| --- | --- | --- |
| Root project guidance | PASS | Arch-family, Waydroid, ADB target safety, project commands retained |
| Shared-file integration | PASS | reviewed pathwise; no wholesale root replacement |
| Resolution vocabulary | PASS | only apply / merge / keep / remove / defer; disposition is separate |
| Deletion gate | PASS | no P path deleted; referenced legacy records deferred |
| Template-self history | PASS | no lifecycle-self-audit docs imported |
| Active hook anchors | PASS | hook points to project DEC-006, not excluded upstream history |
| CI scope | PASS | checkout depth 0, pinned P baseline, `DD_SCOPE_DIFF_FILTER=ACMR` |
| Lint remediation | PASS | two local Verdict syntax fixes; no global rule suppression |
| Branch isolation | PASS | main / remote refs unchanged |

Failure audit:

- The first full run stopped because `/tmp` was full. Only this task's
  inventory snapshot was moved to a cache filesystem; evidence was preserved
  and the same commands passed with an external `TMPDIR`.
- The first scoped wrapper exposed inherited `DD_SCOPE_PATHS` inside nested
  frontmatter fixtures. The test harness now clears outer scope for those
  fixture commands; unscoped and scoped runs both pass.
- A plausible markdownlint-version mismatch was checked by rerunning the full
  CI glob with markdownlint-cli2. The two baseline MD036 findings reproduced
  and were fixed locally; the final run has zero issues.

## Acceptance Criteria Coverage

| ID | Result | Evidence |
| --- | --- | --- |
| AC-001 | PASS | 143-row union, 12 artifacts, final resolution and disposition |
| AC-002 | PASS | U distribution plus learned fixtures / hooks / CI integrated |
| AC-003 | PASS | stage verdicts separated; exact lock written after compatibility |
| AC-004 | PASS | project regressions and P runtime diff are clean |
| AC-005 | PASS | docs, lint, fixtures, hooks, smoke, paired, project gates pass |
| AC-006 | PASS | final raw diff missing count is zero |

## Decision Conformance

| ID | Result | Why the implementation remains aligned |
| --- | --- | --- |
| DEC-001 | PASS | one B/P/U lane and peeled immutable tag are recorded |
| DEC-002 | PASS | project runtime and reproducibility guidance remain intact |
| DEC-003 | PASS | compatibility and strict schema are not collapsed or bulk edited |
| DEC-004 | PASS | no unauthorized deletion; template-self history stays excluded |
| DEC-005 | PASS | final raw diff is fully covered by the two path tables |
| DEC-006 | PASS | bounded hook behavior is anchored without upstream self-history |

## Invariant Coverage

| ID | Result | Evidence |
| --- | --- | --- |
| INV-001 | PASS | lock tag / commit match upstream `git -C` resolution |
| INV-002 | PASS | runtime / helper / packaging / test diff from P is empty |
| INV-003 | PASS | lifecycle-self-audit paths are absent |
| INV-004 | PASS | raw diff inventory missing count is zero |

## Deferred / Not Covered

| ID | Reason | Follow-up |
| --- | --- | --- |
| Strict schema stage | semantic review is required; bulk markers are prohibited | `Workflow-Chore-20` |
| APK reinstall / settings UI | changes external device state; not needed for migration | None; build and doctor passed |
| Disruptive restart / ADB disconnect | explicitly outside migration scope | existing `Core-Test-17` |

## Residual Risks

- Historical project intent / QA records still rely on U's legacy-compatible
  validator path. A future template release may remove it; `Workflow-Chore-20`
  must review and order strict conversion before adopting such a release.
- Seven old workflow records cannot be removed while active project references
  remain. The same follow-up will decide retention or reference-safe
  supersession.

## Follow-up TODOs

- `Workflow-Chore-20`: review strict docs schema adoption and legacy references.
- `Core-Test-17`: existing disruptive Waydroid recovery verification; unchanged
  by this migration.
