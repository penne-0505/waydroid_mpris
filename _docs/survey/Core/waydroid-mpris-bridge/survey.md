---
title: Waydroid MPRIS bridge technical survey
status: active
draft_status: n/a
created_at: 2026-07-09
updated_at: 2026-07-09
references:
  - "_docs/plan/Core/waydroid-mpris-bridge/plan.md"
  - "_docs/intent/Core/waydroid-mpris-bridge/decision.md"
  - "_docs/qa/Core/waydroid-mpris-bridge/test-plan.md"
  - "_docs/reference/Core/bridge-protocol/reference.md"
  - "../../../../fixtures/probe/apple-music-playing.sample.json"
related_issues: []
related_prs: []
---

# Waydroid MPRIS bridge technical survey

## Background

Waydroid 上の Apple Music は Linux host 側へ音声を出せるが、Android の
MediaSession が GNOME の MPRIS consumer へ直接公開されない。そのため
GNOME のメディア欄、`playerctl`、メディアキーからは Apple Music が通常の
Linux media player として扱われない。

本プロジェクトは、Waydroid 内 Android companion と host daemon を分け、
Android 側の再生状態と操作を host 側の MPRIS service に変換することを狙う。

## Objective

- Android 側で Apple Music の active media session から曲名、artist、再生状態、
  duration、position、artwork 相当を取得できる見込みを確認する。
- host 側で GNOME / `playerctl` が読める最小 MPRIS surface を定義する。
- Waydroid 固有の導入、通信、検証上の不確実性を洗い出す。
- 実装マイルストーンを、probe 結果に応じて変更できる粒度に分ける。

## Method

2026-07-09 時点で以下の一次情報を確認した。

- Waydroid docs:
  <https://docs.waydro.id/>
- Waydroid app install:
  <https://docs.waydro.id/usage/install-and-run-android-applications>
- Android `MediaSessionManager`:
  <https://developer.android.com/reference/kotlin/android/media/session/MediaSessionManager>
- Android `NotificationListenerService`:
  <https://developer.android.com/reference/kotlin/android/service/notification/NotificationListenerService>
- Android `MediaController.TransportControls`:
  <https://developer.android.com/reference/android/media/session/MediaController.TransportControls>
- MPRIS Player interface:
  <https://specifications.freedesktop.org/mpris/latest/Player_Interface.html>
- MPRIS metadata guidelines:
  <https://www.freedesktop.org/wiki/Specifications/mpris-spec/metadata/>

## Results

- Waydroid is a Linux container based Android runtime. Android applications can be
  installed with `waydroid app install xyz.apk` and launched by package name with
  `waydroid app launch com.foo.bar`.
- `MediaSessionManager.getActiveSessions(notificationListener)` returns active
  `MediaController` instances in priority order. A third-party app can use it
  when it is an enabled notification listener; otherwise it needs privileged
  `MEDIA_CONTENT_CONTROL`.
- `NotificationListenerService` must be declared with
  `BIND_NOTIFICATION_LISTENER_SERVICE` and the
  `android.service.notification.NotificationListenerService` intent filter.
  The user must explicitly enable notification listener access in Android
  settings.
- `MediaController.TransportControls` supports `play`, `pause`, `skipToNext`,
  `skipToPrevious`, `seekTo`, and related commands. This is the likely command
  path from host MPRIS methods back to Apple Music.
- MPRIS `org.mpris.MediaPlayer2.Player` exposes `PlaybackStatus`, `Metadata`,
  `Position`, `CanPlay`, `CanPause`, `CanGoNext`, `CanGoPrevious`, `CanSeek`,
  and `CanControl`. `PlaybackStatus` must be one of `Playing`, `Paused`, or
  `Stopped`.
- MPRIS metadata must at least include `mpris:trackid` for a current track.
  Common useful keys for this project are `xesam:title`, `xesam:artist`,
  `xesam:album`, `mpris:length`, and optional `mpris:artUrl`.
- `mpris:artUrl` is a URI to an image representing the track or album. Clients
  must not assume the URI remains valid after the player stops exposing it.
- M0 live probe on 2026-07-09 confirmed the target Apple Music package as
  `com.apple.android.music`.
- M0 live probe confirmed that Apple Music exposes a visible MediaSession with
  non-empty title, artist, album, album artist, media id, duration, content URI
  artwork, album art bitmap, display icon bitmap, playback state, position,
  speed, and action bitmask.
- Observed Apple Music actions while playing were normalized as `pause`, `next`,
  `previous`, `seekTo`, and `stop`. A separate paused-state probe may still be
  useful before final command mapping because Android action availability can
  vary by state.
- Artwork is available in two forms in the observed environment: Android content
  URI and 315x315 bitmap metadata. Host-readable `mpris:artUrl` still requires a
  later extraction/cache step because the content URI is Android-side.
- ADB authorization is working for the Waydroid instance. APK install may trigger
  Android's unsafe-app verification prompt; once the user allowed it, `adb
  install --no-incremental -r` succeeded.
- `run-as` is not usable in this Waydroid image due `setegid(AID_PACKAGE_INFO)`
  failure, but the probe writes a readable copy to
  `/sdcard/Android/data/dev.penne.waydroidmpris.probe/files/latest_probe.json`.

## Discussion

The self-built bridge is technically plausible because Android offers a
notification-listener route to active media sessions, and MPRIS has a small
enough core surface for a first host daemon.

The main uncertainty is not the standards boundary; it is live behavior inside
Waydroid with Apple Music:

- whether Apple Music exposes complete metadata through `MediaController`
  (confirmed for the current playing-state probe);
- whether artwork is present as bitmap, URI, or only notification large icon
  (confirmed as URI plus album art / display icon bitmaps in the current
  playing-state probe);
- whether Waydroid's Android settings reliably expose notification listener
  permission for the companion app (confirmed after user approval);
- whether a companion background service remains alive enough for daily use;
- whether ADB-backed polling is sufficient for daily use, or should later be
  replaced by a socket transport.

The plan should still treat the first milestone as a capability probe because a
paused-state probe and longer background-lifetime check remain useful. However,
the main metadata/artwork feasibility risk is now reduced: Apple Music exposes
enough MediaSession data for the planned metadata MVP and enough artwork data to
justify M4 as a real enhancement.

## Recommended Actions

1. Keep the minimal Android probe as the companion-app seed.
2. Use `_docs/reference/Core/bridge-protocol/reference.md` and
   `fixtures/probe/apple-music-playing.sample.json` as the v0 host fixture
   contract.
3. Build the host MPRIS daemon against fixture protocol messages first, so
   `playerctl` behavior can be tested without Apple Music or Waydroid.
4. Keep the ADB-backed transport as the first live path because it avoids
   opening a host network listener and has passed metadata/control QA.
5. Add artwork after metadata/control work, and make artwork absence a supported
   state rather than a failure.
