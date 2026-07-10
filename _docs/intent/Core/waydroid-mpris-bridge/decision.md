---
title: Waydroid MPRIS bridge architecture decision
status: active
draft_status: n/a
created_at: 2026-07-09
updated_at: 2026-07-10
references:
  - "_docs/survey/Core/waydroid-mpris-bridge/survey.md"
  - "_docs/plan/Core/waydroid-mpris-bridge/plan.md"
  - "_docs/qa/Core/waydroid-mpris-bridge/test-plan.md"
  - "_docs/intent/Core/waydroid-adb-auto-recovery/decision.md"
related_issues: []
related_prs: []
---

# Waydroid MPRIS bridge architecture decision

## Context

Waydroid 上の Apple Music を daily music client として使う場合、Linux host 側で
「再生中メディア」として扱えないことが主要な摩擦になる。GNOME / `playerctl` /
media keys は MPRIS を前提に統合されるが、Waydroid は Android MediaSession を
host MPRIS service として公開していない。

最低要件は host 側での操作と曲名表示である。artwork は望ましいが、Apple Music
と Waydroid の実測次第で取得できない可能性がある。

## Decision

本 project は、Waydroid 内 Android companion と Linux host daemon からなる
self-built bridge を実装する。

- Android companion は notification listener と MediaSession APIs を使い、
  Apple Music の selected session から metadata、playback state、capabilities を
  抽出する。
- Host daemon は bridge protocol event を MPRIS service に変換し、
  GNOME / `playerctl` / media keys へ公開する。
- Host からの MPRIS commands は bridge protocol command として Android companion
  へ戻し、selected session の `TransportControls` にだけ配送する。
- 初期 live transport は ADB を使う。host は Android companion が external app
  files に書いた snapshot を読み、commands は ADB shell から explicit receiver へ
  broadcast する。host 側に network listener は開かない。
- Artwork は optional enhancement として扱い、取得できない場合でも metadata と
  controls の MVP を成立させる。
- Implementation plan は probe 結果に応じて更新可能とし、TODO / plan / QA の同期を
  完了条件に含める。

## Alternatives

- **GSConnect / KDE Connect を使う**: 既製品として早く試せるが、Waydroid 内
  Android と host の接続、Apple Music session の選択、GNOME MPRIS 表示の安定性を
  project 側で制御しにくい。今回の目的は daily-use client として納得できる挙動を
  作ることなので、比較対象に留める。
- **Waydroid 本体へ MPRIS bridge を実装する**: 長期的には最も自然だが、scope が
  Waydroid upstream の設計・配布・review へ広がる。まず local project として
  Apple Music 用の制約を明確にした bridge を作る。
- **ADB media key forwarding のみで済ませる**: Play/Pause などの操作は軽く実現できる
  可能性があるが、曲名と artwork が出ない。最低要件を満たさない。
- **Apple Music の再生元を Web/PWA へ移す**: MPRIS 統合は楽になる可能性があるが、
  Android 版 Apple Music を Waydroid で使う理由を捨てる。今回の問題設定から外れる。

## Rationale

MPRIS は host 側 integration の正面玄関であり、Android MediaSession は Android 側
media state/control の正面玄関である。両者を project-owned protocol で接続すれば、
GNOME 側では通常の media player として扱え、Android 側では Apple Music の既存
MediaSession を壊さず利用できる。

また、fixture protocol を先に定義することで、Waydroid / Apple Music / account 状態に
依存しない host daemon tests を書ける。これは daily use tool としての回帰検出に必要である。

## Consequences / Impact

- Android app と host daemon の 2 component を保守する必要がある。
- Android notification listener permission を扱うため、privacy boundary を明文化する
  必要がある。
- Transport channel の選択を誤ると、local-only のつもりが外部 network へ command
  endpoint を expose する可能性がある。
- Apple Music の metadata / artwork exposure に依存する部分は probe によって計画が
  変わり得る。
- Artwork は cache と URI lifetime を扱うため、metadata/control MVP から分離する。

## Quality Implications

- Host MPRIS state は Android source state の projection であり、source が消えた場合に
  stale track を再生中として見せてはならない。
- Command は selected Apple Music session のみに配送する。session が不明な場合は失敗を
  明示し、fallback broadcast で別 app を動かさない。
- Notification listener は広い権限を持つため、host へ送る payload は media metadata と
  state に限定する。
- Artwork failure は core feature failure ではない。title / artist / controls の正常性を
  artwork 可否から切り離す。
- Live Waydroid がなくても protocol / MPRIS mapping を検証できる必要がある。

## Intent-derived Invariants

- INV-001: Android companion は raw notification payload や unrelated notification data を host へ送らず、選択中 media session の metadata/state/capabilities に限定する。
- INV-002: Host daemon は Android source が unavailable または stale になったとき、MPRIS state を `Stopped` または empty metadata へ落とし、古い track を `Playing` として残してはならない。
- INV-003: Host command は selected Apple Music session にだけ配送し、target session が不明または stale の場合は command を失敗扱いにする。
- INV-004: Bridge transport は default で local-only とし、外部 network へ expose する変更は plan / intent / QA の明示更新なしに入れてはならない。
- INV-005: Artwork は optional capability であり、取得・decode・cache・URI 生成に失敗しても title / artist / playback controls を失敗させてはならない。
- INV-006: Host MPRIS daemon は fixture protocol input だけで metadata/state mapping を検証できなければならない。
- INV-007: Probe や実装中の発見で計画が変わる場合、TODO / plan / QA を同じ変更範囲で同期し、古い milestone 前提を active guidance として残してはならない。

## Enforced in (optional)

- INV-001: Android metadata normalization and outbound event schema.
- INV-002: Host daemon source-liveness and MPRIS state mapping tests.
- INV-003: Android command handler and host command routing tests.
- INV-004: Transport configuration and security/privacy review.
- INV-005: Artwork pipeline tests and manual QA.
- INV-006: Host fixture tests.
- INV-007: Documentation review and `scripts/check-docs.sh`.

## Rollback / Follow-ups

- If Apple Music does not expose enough MediaSession metadata, keep M0 findings
  in survey and retarget the project to notification-derived metadata only if it
  can satisfy INV-001.
- If artwork is unreliable, ship M3 as the first usable milestone and keep M4 as
  an enhancement.
- If ADB transport proves unreliable for daily use, compare ADB forward,
  container IP, and local socket approaches in a follow-up survey update before
  replacing the current M3 path.
