---
title: "QA Verification: Reproducible Arch setup"
status: active
draft_status: n/a
qa_status: verified
risk: Medium
created_at: 2026-07-11
updated_at: 2026-07-11
references:
  - "_docs/qa/Core/reproducible-arch-setup/test-plan.md"
  - "_docs/intent/Core/reproducible-arch-setup/decision.md"
  - "_docs/plan/Core/reproducible-arch-setup/plan.md"
related_issues: []
related_prs: []
---

# QA Verification: Reproducible Arch setup

## Summary

2026-07-11 に portable Android SDK discovery、target-scoped install / settings helpers、Arch dependency guidance、runtime CI checksを検証した。fake SDK rootsによるclean-room相当unit checksと、current Arch / Waydroid environmentでのbuild / install / doctorを分離して実行した。

## Verification Verdict

Verdict: PASS

全AC / INVに対応するautomated、manual、diff-review evidenceがあり、初期setup再現性にmaterialな未確認事項はない。GitHub-hosted CI job自体はpush前のため未実行だが、workflowに記載した各project commandはlocalでPASSしており、これはrepository変更の完了を妨げる残リスクとは扱わない。

## Commands Run

```bash
python -m unittest tests/test_protocol_mapping.py tests/test_adb_transport.py tests/test_adb_recovery.py tests/test_live_failure_mapping.py tests/test_position_projection.py tests/test_artwork_cache.py tests/test_android_setup.py
python -m py_compile host/waydroid_mpris/*.py scripts/run-host-mpris-live.py scripts/run-host-mpris-fixture.py scripts/doctor.py scripts/resolve-waydroid-adb-target.py scripts/run-disruptive-waydroid-restart-qa.py
bash -n scripts/*.sh
./scripts/install-user-service.sh --dry-run > /tmp/waydroid-mpris-repro.service
systemd-analyze --user verify /tmp/waydroid-mpris-repro.service
./scripts/build-android-probe.sh
python scripts/resolve-waydroid-adb-target.py
python scripts/resolve-waydroid-adb-target.py --device 192.168.240.112:5555
./scripts/install-android-probe.sh --device 192.168.240.112:5555 --apk android/probe/build/outputs/waydroid-mpris-probe-debug.apk
./scripts/open-android-notification-listener-settings.sh --device 192.168.240.112:5555
python scripts/doctor.py
./scripts/check-docs.sh
git diff --check
```

## Automated Test Results

- Host / setup unit suite: **PASS** — 38 tests、0 failures、0 errors。
- fake SDK checks: **PASS** — explicit root/version precedence、latest installed selection、missing SDK guidance、maintainer path absence。
- Python compile / shell syntax: **PASS**。
- generated systemd user unit: **PASS**。
- Android build: **PASS** — SDK `$HOME/Android/Sdk`、Platform `android-36.1`、Build-Tools `37.0.0`、JDK 26.0.1。
- docs validators / whitespace: **PASS**。

## Manual QA Results

- auto target resolution: **PASS** — `192.168.240.112:5555`。
- explicit target resolution: **PASS** — 同じserialがready targetとして返った。
- target-scoped reinstall: **PASS** — `adb -s 192.168.240.112:5555 install ...`が`Success`、companion activityが起動した。
- notification-listener settings: **PASS** — explicit target上でAndroid settings intentが起動した。
- doctor after reinstall: **PASS** — dependencies、Waydroid、ADB target、package、listener、probe、artwork、MPRIS status / metadataが全項目PASS。
- signature mismatch destructive reproduction: **not performed** —別debug key導入とuninstallは不要な破壊操作になるため、known error mapping test、script control flow、no-uninstall diff reviewで確認した。

## Acceptance Criteria Coverage

- AC-001: **PASS** — README / Quickstart / usage guideにArch packages、SDK components、known-good versions、success criteriaを記載。
- AC-002: **PASS** — personal defaultを除去し、environment / common paths、version overrides、preflight、selection outputをunit / live buildで確認。
- AC-003: **PASS** — existing fail-closed recovery testsとlive auto / explicit resolver、target-scoped install / settingsで確認。
- AC-004: **PASS** — mismatch guidanceとautomatic uninstall absenceをtest / diff reviewで確認。
- AC-005: **PASS** — workflowにunit、compile、shell、service dry-run、Android build jobを追加し、対応local commandsがPASS。
- AC-006: **PASS** — fake SDK / static checksとlive Waydroid resultsを本verificationで分離。

## Invariant Coverage

- INV-001: **PASS** — runtime script defaultsにmaintainer absolute SDK pathなし。
- INV-002: **PASS** — `ANDROID_HOME`、`ANDROID_SDK_ROOT`、platform / build-tools overridesの優先をunit test。
- INV-003: **PASS** — Waydroid-derived / explicit targetのみを使用し、既存recovery testsでunrelated device fallbackなし。
- INV-004: **PASS** — mismatch pathはguidance後exitし、uninstall commandを持たない。
- INV-005: **PASS** — SDK install、license acceptance、release signingをscripts / workflowへ追加していない。
- INV-006: **PASS** — automated、manual、未実行destructive mismatchを別項目として記録。

## Deferred / Not Covered

- GitHub-hosted runner上の新runtime job実行結果。push / PR後にGitHub Actionsが正典となる。
- 非Arch distroのruntime support。
- bit-for-bit identical APK、release signing、配布artifact。
- automatic ADB recoveryのdisruptive restart / authorization transition。`Core-Test-17`で別追跡する。

## Residual Risks

None

## Follow-up TODOs

None for this task. Existing `Core-Test-17` remains the separate automatic-recovery live QA task.
