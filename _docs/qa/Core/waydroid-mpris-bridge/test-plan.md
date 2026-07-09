---
title: "QA Test Plan: Waydroid MPRIS bridge"
status: active
draft_status: n/a
qa_status: planned
risk: High
created_at: 2026-07-09
updated_at: 2026-07-09
references:
  - "_docs/survey/Core/waydroid-mpris-bridge/survey.md"
  - "_docs/intent/Core/waydroid-mpris-bridge/decision.md"
  - "_docs/plan/Core/waydroid-mpris-bridge/plan.md"
related_issues: []
related_prs: []
---

# QA Test Plan: `Waydroid MPRIS bridge`

## Source of Intent

- Completed checkpoint tasks: `Core-Chore-9`, `Core-Feat-10`, `Core-Feat-11`,
  `Core-Feat-12`, `Core-Enhance-13`, `Core-Enhance-14`, `Core-Enhance-15`
- Completed compatibility hardening: MPRIS position projection, complete-PNG
  artwork cache replacement, ADB authorization guidance, and generated systemd
  user service helper.
- Open TODO: none
- Survey: `_docs/survey/Core/waydroid-mpris-bridge/survey.md`
- Plan: `_docs/plan/Core/waydroid-mpris-bridge/plan.md`
- Intent: `_docs/intent/Core/waydroid-mpris-bridge/decision.md`

## Quality Goal

Waydroid 上の Apple Music を GNOME / `playerctl` から通常の MPRIS player として扱える
状態へ近づける。最低限、操作と曲名表示を実現し、privacy-sensitive な notification
access と command routing を local-only かつ selected session 限定で扱う。

## Acceptance Criteria

- AC-001: Android probe が Apple Music の active media session を識別し、取得可能な
  metadata keys、playback state、actions、artwork availability を記録する。
- AC-002: Host daemon が fixture event から MPRIS service を公開し、`playerctl` で
  status と title / artist metadata を読める。
- AC-003: Host MPRIS commands が bridge protocol を通じて selected Apple Music
  session の `TransportControls` へ配送される。
- AC-004: Android source unavailable / stale session / transport disconnect 時に、
  host MPRIS が stale track を `Playing` として残さない。
- AC-005: Artwork が取得できる場合は `mpris:artUrl` として公開され、取得できない場合も
  title / artist / controls は動く。
- AC-006: Install / run / diagnose / permission grant 手順が README、guide、または
  reference に記録されている。
- AC-007: Host MPRIS `Position` が同一 track の `Playing` 中に進み、paused /
  missing session では不自然に進み続けない。

## Intent-derived Invariants

- INV-001: Android companion は raw notification payload や unrelated notification data を host へ送らず、選択中 media session の metadata/state/capabilities に限定する。
- INV-002: Host daemon は Android source が unavailable または stale になったとき、MPRIS state を `Stopped` または empty metadata へ落とし、古い track を `Playing` として残してはならない。
- INV-003: Host command は selected Apple Music session にだけ配送し、target session が不明または stale の場合は command を失敗扱いにする。
- INV-004: Bridge transport は default で local-only とし、外部 network へ expose する変更は plan / intent / QA の明示更新なしに入れてはならない。
- INV-005: Artwork は optional capability であり、取得・decode・cache・URI 生成に失敗しても title / artist / playback controls を失敗させてはならない。
- INV-006: Host MPRIS daemon は fixture protocol input だけで metadata/state mapping を検証できなければならない。
- INV-007: Probe や実装中の発見で計画が変わる場合、TODO / plan / QA を同じ変更範囲で同期し、古い milestone 前提を active guidance として残してはならない。

## Risk Assessment

- Risk level: High
- Risk rationale: Android notification listener permission、host command routing、
  local transport exposure、D-Bus desktop integration を扱う。失敗時には unrelated
  notification data exposure、誤った media session 操作、stale state 表示が起こり得る。
- Regression risk: protocol schema と MPRIS mapping が変わったとき、GNOME / `playerctl`
  表示や command routing が静かに壊れること。
- Data safety risk: Low。永続データは基本扱わないが、artwork cache を作る場合は cleanup と
  file exposure を確認する。
- Security / privacy risk: High。notification listener は広い可視性を持つため、outbound
  payload を media session data に限定する必要がある。
- UX risk: Medium。stale metadata、permission 未許可、Waydroid 未起動、transport
  disconnect は daily use の体験を損なう。
- Agent misbehavior risk: Medium。plan が probe 結果で変わる前提を忘れ、古い milestone
  を固定仕様として実装する可能性がある。

## Test Strategy

- Unit:
  - protocol event/command schema validation;
  - Android metadata normalization from fake session snapshots;
  - host MPRIS metadata/state mapping;
  - host MPRIS position projection while Android raw position is stale;
  - stale source clearing;
  - artwork absent / invalid URI handling.
- Integration:
  - host daemon fixture stream to D-Bus MPRIS query;
  - command schema to Android command handler with fake selected session;
  - transport local binding and reconnect behavior.
- E2E:
  - Waydroid + Apple Music + Android companion + host daemon;
  - GNOME media UI and `playerctl` status / metadata / position / play-pause / next / previous.
- Manual QA:
  - notification listener permission grant;
  - Apple Music package selection;
  - media key behavior;
  - artwork visibility when available;
  - Waydroid stop/restart behavior.
- Validator / static check:
  - `scripts/check-docs.sh`;
  - `./scripts/build-android-probe.sh`;
  - host unit tests and Python compile checks;
  - generated systemd user service verification.
- Diff review:
  - no raw notification payload forwarding;
  - local-only transport default;
  - TODO / plan / QA synchronization after probe changes.

## Test Matrix

| ID | Source | Requirement / Invariant | Test Type | Command / File | Expected Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001 | TODO | Apple Music session capability is measured. | manual QA + probe log | `adb shell cat .../latest_probe.json` | package, metadata keys, playback state, actions, artwork availability recorded. | verified |
| AC-002 | TODO | Host daemon exposes MPRIS metadata from fixture and live snapshot. | integration | `playerctl --player=waydroid_mpris metadata` | title / artist / status match fixture or live Apple Music. | verified |
| AC-003 | TODO | MPRIS commands reach selected session. | integration + manual QA | `playerctl --player=waydroid_mpris play-pause` | Apple Music playback toggles; command target logged. | verified |
| AC-004 | TODO | Stale session is cleared. | unit + integration | host daemon tests and live absent-source QA | source unavailable maps to `Stopped` or empty metadata. | verified |
| AC-005 | TODO | Artwork is optional and non-blocking. | unit + manual QA | `tests/test_artwork_cache.py`; `playerctl metadata mpris:artUrl` | valid complete PNG art exposes `mpris:artUrl`; truncated cache is replaced; absent art preserves metadata/control. | verified |
| AC-006 | TODO | Daily-use operations are documented. | diff review + doctor | README / Quickstart / guide / `scripts/doctor.py` / `scripts/install-user-service.sh` | install, run, diagnose, permission, and service setup steps exist. | verified |
| AC-007 | TODO | MPRIS position advances during playback. | unit + live query | `tests/test_position_projection.py`; `busctl ... Position` | repeated position reads increase while playing and stop advancing when paused or source is absent. | verified |
| INV-001 | intent | No raw unrelated notification payload leaves Android. | diff review + live snapshot | Android snapshot schema | event schema contains only media session fields. | verified |
| INV-002 | intent | Host does not keep stale `Playing` state. | unit + integration | host stale-state tests and live restart QA | source unavailable maps to `Stopped` or empty metadata. | verified |
| INV-003 | intent | Commands target selected Apple Music session only. | unit + manual QA | Android command handler, `playerctl` live commands | unknown/stale target command fails; no broadcast fallback. | verified |
| INV-004 | intent | Transport is local-only by default. | config review + integration | ADB transport review | daemon exposes only user-session D-Bus and no network listener. | verified |
| INV-005 | intent | Artwork failure does not fail MVP. | unit + diff review | artwork cache provider | title / artist / controls pass without art; invalid PNG cache is not republished. | verified |
| INV-006 | intent | Host MPRIS mapping is fixture-testable. | integration | `tests/test_protocol_mapping.py` | no live Waydroid required for host mapping tests. | verified |
| INV-007 | intent | Probe-driven plan changes update docs together. | diff review + validator | `scripts/check-docs.sh` | TODO / plan / QA remain synchronized after changes. | verified |

## Manual QA Checklist

- [x] Grant notification listener access to the Android companion inside Waydroid.
- [x] Start Apple Music playback and confirm the selected session package is Apple Music.
- [x] Confirm `playerctl` displays title and artist.
- [x] Use `playerctl play-pause` and confirm Apple Music toggles playback.
- [x] Use next / previous and confirm commands affect Apple Music.
- [x] Stop or restart Waydroid and confirm host MPRIS state does not remain stale `Playing`.
- [x] If artwork is available, confirm `mpris:artUrl` points to a readable local URI.

## Regression Checklist

- [ ] Fixture metadata mapping still passes after protocol changes.
- [ ] Stale source clearing still passes after transport changes.
- [ ] Command target validation still rejects stale / unknown sessions.
- [ ] Artwork absence remains supported.
- [ ] Documentation validators pass after milestone plan changes.

## High-risk Checklist

- [x] Rollback or recovery path is documented for host daemon service setup.
- [x] Data safety has been checked for artwork cache and generated logs.
- [x] Security / privacy implications of notification listener payload and transport binding have been checked.
- [x] Failure modes for permission denied, Waydroid stopped, Apple Music absent, and transport disconnect are understood.

## Out of Scope

- Apple Music account, DRM, subscription, or audio quality validation.
- General-purpose Android media bridge for multiple simultaneous players.
- Public network remote control.
- Waydroid upstream integration.

## Open Questions

- Should the long-term transport remain ADB polling or move to a socket protocol after longer daily-use observation?
