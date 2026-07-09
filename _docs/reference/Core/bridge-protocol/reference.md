---
title: Waydroid MPRIS bridge protocol
status: active
draft_status: n/a
created_at: 2026-07-09
updated_at: 2026-07-09
references:
  - "_docs/plan/Core/waydroid-mpris-bridge/plan.md"
  - "_docs/intent/Core/waydroid-mpris-bridge/decision.md"
  - "_docs/qa/Core/waydroid-mpris-bridge/test-plan.md"
  - "../../../../fixtures/probe/apple-music-playing.sample.json"
related_issues: []
related_prs: []
---

# Waydroid MPRIS bridge protocol

## Purpose

This document defines the current message shape for the Android companion and
host daemon. The first live transport is ADB-backed: the host polls the Android
snapshot file and dispatches explicit commands to the companion receiver.

## Snapshot Event

The Android side writes a snapshot whenever the selected media session changes,
the playback state changes, the notification listener connects, an Apple Music
notification is posted/removed, a command is dispatched, or a manual probe is
requested. The host live daemon reads the latest snapshot with `adb shell cat`.

```json
{
  "schema": "dev.penne.waydroid_mpris.probe.v0",
  "reason": "activity",
  "targetPackage": "com.apple.android.music",
  "notificationListenerEnabled": true,
  "sessionCount": 1,
  "sessions": [],
  "selectedAppleMusicSession": {}
}
```

### Top-level Fields

| Field | Type | Notes |
| --- | --- | --- |
| `schema` | string | Current draft schema id. |
| `reason` | string | Probe/update trigger such as `activity`, `listener_connected`, or `apple_music_notification_posted`. |
| `targetPackage` | string | Expected to be `com.apple.android.music` for this project. |
| `notificationListenerEnabled` | boolean | Whether the Android notification listener is enabled for the probe app. |
| `sessionCount` | number | Number of active media sessions visible to the listener. |
| `sessions` | array | All visible media sessions after privacy filtering. |
| `selectedAppleMusicSession` | object or null | First active Apple Music session selected for host projection. |

## Session Object

| Field | Type | Notes |
| --- | --- | --- |
| `packageName` | string | Android package name owning the MediaSession. |
| `metadata` | object | Normalized MediaSession metadata. |
| `playbackState` | object | Normalized playback state and available actions. |

## Metadata Object

| Field | Type | Notes |
| --- | --- | --- |
| `present` | boolean | `false` when Android reports no metadata. |
| `mediaId` | string | Optional media id from Apple Music. |
| `title` | string | Track title. Maps to `xesam:title`. |
| `artist` | string | Track artist. Maps to `xesam:artist` as a single-item array. |
| `album` | string | Album name. Maps to `xesam:album`. |
| `albumArtist` | string | Album artist. Maps to `xesam:albumArtist`. |
| `durationMs` | number | Track duration. Host converts to MPRIS microseconds. |
| `albumArtUri` | string | Android content URI when provided. Not directly host-readable. |
| `description` | object | Android MediaDescription fields useful for fallback display. |
| `artwork` | object | Presence and size of bitmap metadata. The host must treat artwork as optional. |
| `artworkFile` | object | Optional exported PNG file path inside Android external app files. Host caches this file before publishing `mpris:artUrl`. |

## Playback State Object

| Field | Type | Notes |
| --- | --- | --- |
| `present` | boolean | `false` when Android reports no playback state. |
| `state` | string | Normalized state such as `playing`, `paused`, or `stopped`. |
| `stateCode` | number | Raw Android PlaybackState code. |
| `positionMs` | number | Projected position in milliseconds at probe time. Android computes this from raw PlaybackState position, update time, playback state, and speed. |
| `rawPositionMs` | number | Raw Android PlaybackState position before probe-time projection. |
| `speed` | number | Playback speed. |
| `updateTimeMs` | number | Android elapsed realtime for the position update. |
| `probeElapsedRealtimeMs` | number | Android elapsed realtime when the probe snapshot was written. |
| `actionsRaw` | number | Raw Android action bitmask. |
| `actions` | array | Normalized action names such as `pause`, `next`, `previous`, `seekTo`, and `stop`. |

The host daemon projects MPRIS `Position` forward with the host monotonic clock
while the same track remains `Playing`. This keeps polling MPRIS clients, seek
bars, and synchronized lyric clients from seeing a stale fixed position when
Android does not push continuous MediaSession position updates.

## Command Event

The host sends commands through an explicit Android broadcast receiver:

```bash
adb shell am broadcast \
  -a dev.penne.waydroidmpris.probe.COMMAND \
  -n dev.penne.waydroidmpris.probe/.BridgeCommandReceiver \
  --es command playPause
```

The receiver requires `android.permission.MEDIA_CONTENT_CONTROL`; in the current
Waydroid setup, the ADB shell caller satisfies that permission check. The
Android companion then resolves the current Apple Music MediaSession and calls
only that session's `TransportControls`.

| Command | Android action |
| --- | --- |
| `play` | `TransportControls.play()` |
| `pause` | `TransportControls.pause()` |
| `playPause` | Pause if the selected session is playing; otherwise play. |
| `next` | `TransportControls.skipToNext()` |
| `previous` | `TransportControls.skipToPrevious()` |
| `stop` | `TransportControls.stop()` |
| `seekTo` | `TransportControls.seekTo(positionMs)` when a position is supplied. |

Command results are written to `latest_command_result.json` in the companion's
app files directory and external app files directory.

## Transport

The first live transport intentionally avoids opening a socket:

- metadata/state: `adb shell cat /sdcard/Android/data/dev.penne.waydroidmpris.probe/files/latest_probe.json`
- commands: `adb shell am broadcast` to the explicit companion receiver
- host exposure: user-session D-Bus MPRIS only

This is local to the ADB connection and does not expose a network listener. A
future transport may replace ADB, but doing so must update plan / intent / QA
because it changes INV-004's exposure boundary.

## Artwork Cache

When Android metadata contains bitmap artwork, the companion exports the first
available source in this order: `albumArt`, `displayIcon`, `art`. The exported
file is a PNG under Android external app files, for example:

```text
/storage/emulated/0/Android/data/dev.penne.waydroidmpris.probe/files/artwork/<media-id>.png
```

The host live daemon reads that file through ADB, caches it under
`~/.cache/waydroid-mpris/artwork` by default, and publishes the cached
host-readable `file://` URI as `mpris:artUrl`. Cache failure must not remove
title / artist / controls.

Android publishes artwork atomically through a temporary file and rename. The
host validates cached PNG files before reusing them; incomplete PNG cache entries
are replaced from the Android source instead of being republished.

## Privacy Boundary

The Android companion must send only MediaSession-derived metadata, playback
state, action capabilities, and artwork availability. It must not forward raw
notification payloads or unrelated notification data.

## Fixture

The current redacted fixture is
`fixtures/probe/apple-music-playing.sample.json`.
