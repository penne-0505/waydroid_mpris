---
title: "QA Verification: Waydroid MPRIS bridge MVP and compatibility hardening"
status: active
draft_status: n/a
qa_status: verified
risk: High
created_at: 2026-07-09
updated_at: 2026-07-09
references:
  - "_docs/intent/Core/waydroid-mpris-bridge/decision.md"
  - "_docs/plan/Core/waydroid-mpris-bridge/plan.md"
  - "_docs/qa/Core/waydroid-mpris-bridge/test-plan.md"
  - "_docs/reference/Core/bridge-protocol/reference.md"
  - "../../../../fixtures/probe/apple-music-playing.sample.json"
related_issues: []
related_prs: []
---

# QA Verification: `Waydroid MPRIS bridge MVP and compatibility hardening`

## Summary

M0 capability probe, M1 Android companion snapshot updates, M2 host MPRIS
metadata MVP, M3 bidirectional command bridge, M4 artwork pipeline, M5
daily-use entrypoints, and M6 restart/absent-session plus MPRIS consumer
compatibility hardening were implemented and checked. The current live path is
ADB-backed: the host daemon polls the Android companion's `latest_probe.json`,
exposes MPRIS on the user session bus, sends commands back with an explicit
Android broadcast receiver, projects MPRIS `Position` while the same track is
playing, and caches exported Android artwork as a host-readable complete PNG
`file://` URI.

## Verification Verdict

Verdict: PASS

Reason: metadata, controls, position, artwork, docs, diagnostics, stale-state
clearing during Waydroid stop, ADB reconnect recovery, and absent-session
command failure behavior are verified.

## Commands Run

```bash
./scripts/build-android-probe.sh
./scripts/install-android-probe.sh
adb install --no-incremental -r android/probe/build/outputs/waydroid-mpris-probe-debug.apk
adb shell settings get secure enabled_notification_listeners
adb shell am start -n dev.penne.waydroidmpris.probe/.MainActivity
adb shell cat /sdcard/Android/data/dev.penne.waydroidmpris.probe/files/latest_probe.json
python -m unittest tests/test_protocol_mapping.py tests/test_adb_transport.py tests/test_live_failure_mapping.py tests/test_position_projection.py tests/test_artwork_cache.py
python -m py_compile host/waydroid_mpris/*.py scripts/run-host-mpris-live.py scripts/run-host-mpris-fixture.py scripts/doctor.py scripts/run-disruptive-waydroid-restart-qa.py
python scripts/run-host-mpris-fixture.py fixtures/probe/apple-music-playing.sample.json
python scripts/run-host-mpris-live.py --device 192.168.240.112:5555 --poll-interval 0.5 --artwork-cache /tmp/waydroid-mpris-artwork-test
playerctl --list-all
playerctl --player=waydroid_mpris status
playerctl --player=waydroid_mpris metadata --format '{{title}}|{{artist}}|{{album}}|{{mpris:length}}'
busctl --user get-property org.mpris.MediaPlayer2.waydroid_mpris /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player Position
busctl --user get-property org.mpris.MediaPlayer2.waydroid_mpris /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player Position
busctl --user get-property org.mpris.MediaPlayer2.waydroid_mpris /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player Position
busctl --user get-property org.mpris.MediaPlayer2.waydroid_mpris /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player Position
playerctl --player=waydroid_mpris pause
playerctl --player=waydroid_mpris play
playerctl --player=waydroid_mpris play-pause
playerctl --player=waydroid_mpris next
playerctl --player=waydroid_mpris previous
playerctl --player=waydroid_mpris metadata --format '{{title}}|{{mpris:artUrl}}'
file /tmp/waydroid-mpris-artwork-test/1829662818-ede62f6b782b.png
python - <<'PY' /home/penne/.cache/waydroid-mpris/artwork/358082592-becb44ddfe81.png
from pathlib import Path
import sys
b = Path(sys.argv[1]).read_bytes()
print(b.endswith(bytes.fromhex("0000000049454e44ae426082")))
PY
python scripts/doctor.py
python scripts/doctor.py --device 192.168.240.112:5555
python -m py_compile scripts/run-disruptive-waydroid-restart-qa.py
bash -n scripts/install-user-service.sh
./scripts/install-user-service.sh --dry-run
systemd-analyze verify --user /tmp/waydroid-mpris-generated.service
./scripts/install-user-service.sh --dry-run --device 192.168.240.112:5555 --poll-interval 0.5
systemd-analyze verify --user /tmp/waydroid-mpris-generated-device.service
python scripts/run-disruptive-waydroid-restart-qa.py --i-understand-this-stops-waydroid --device 192.168.240.112:5555 --output /tmp/waydroid-mpris-restart-qa.json
sudo waydroid container stop
sudo systemctl stop waydroid-container.service
sudo systemctl start waydroid-container.service
waydroid session start
adb connect 192.168.240.112:5555
adb shell am start -n dev.penne.waydroidmpris.probe/.MainActivity
adb shell cat /sdcard/Android/data/dev.penne.waydroidmpris.probe/files/latest_probe.json
playerctl --player=waydroid_mpris status
playerctl --player=waydroid_mpris play-pause
busctl --user get-property org.mpris.MediaPlayer2.waydroid_mpris /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player CanControl
./scripts/check-docs.sh
git diff --check
```

Result:

```text
Android probe build: PASS
ADB install: PASS
Notification listener: PASS after user allowed Waydroid MPRIS Probe
Apple Music MediaSession probe: PASS
Host protocol/ADB/position/artwork cache unit tests: PASS, 17 tests
Host MPRIS fixture daemon: PASS
Host MPRIS live daemon: PASS
playerctl live status: Playing
playerctl live metadata: nameless|kurayamisaka|kurayamisaka yori ai wo komete|309000000
MPRIS live position projection: PASS, 50069859 -> 51073398 -> 52076931 -> 53080721 us while playing
Android probe position fields: PASS, positionMs/rawPositionMs/probeElapsedRealtimeMs present
playerctl pause/play: PASS
playerctl play-pause: PASS, Paused -> Playing
playerctl next/previous: PASS, nameless -> うらみ交信 -> nameless
playerctl artUrl: nameless|file:///tmp/waydroid-mpris-artwork-test/1829662818-ede62f6b782b.png
cached artwork file: PNG image data, 315 x 315, IEND-complete
cached artwork completeness: PASS, host cache replaced truncated PNG with IEND-complete PNG
dynamic-music-pill cache: PASS, extension cache created IEND-complete PNG after host cache replacement
doctor without daemon: PASS with host MPRIS WARN
doctor with daemon: PASS
user service helper syntax: PASS
user service helper dry-run: PASS, generated current checkout path and optional ADB serial
generated systemd user service verification: PASS
disruptive restart QA runner: PASS through stop-state check; timed out during session start on this device
Waydroid container recovery: PASS after systemd container restart and ADB reauthorization
stale state while stopped: before_stop Playing -> during_stop Stopped
after restart probe: selectedAppleMusicSession null, sessionCount 0
absent-session MPRIS status: Stopped
absent-session command: playerctl play-pause exit 1, CanControl false
CanControl: true
Docs validator: PASS
Whitespace check: PASS
```

## Automated Test Results

| Command / Test | Result | Notes |
| --- | --- | --- |
| `./scripts/build-android-probe.sh` | PASS | Produces `android/probe/build/outputs/waydroid-mpris-probe-debug.apk`. Java 26 / apksigner warnings are non-fatal. |
| `python -m unittest tests/test_protocol_mapping.py tests/test_adb_transport.py tests/test_live_failure_mapping.py tests/test_position_projection.py tests/test_artwork_cache.py` | PASS | 17 mapping / ADB transport / failure mapping / position projection / artwork cache tests passed. |
| `python -m py_compile ...` | PASS | Host modules and scripts compile. |
| `bash -n scripts/install-user-service.sh` | PASS | User service helper shell syntax is valid. |
| `./scripts/install-user-service.sh --dry-run ...` | PASS | Generated unit uses the current checkout path, current Python path, poll interval, and optional ADB serial. |
| `systemd-analyze verify --user ...` | PASS | Generated default and explicit-device user services are valid systemd unit files. |
| `./scripts/check-docs.sh` | PASS | Documentation, TODO, QA, and scope validators passed. |
| `git diff --check` | PASS | No whitespace errors. |

## Manual QA Results

| Checklist Item | Result | Notes |
| --- | --- | --- |
| ADB authorization | PASS | User approved Waydroid ADB debugging prompt before this checkpoint. |
| Unsafe app install prompt | PASS | User allowed the Android unsafe-app install prompt; later reinstall succeeded without another prompt. |
| Notification listener permission | PASS | Secure setting includes `dev.penne.waydroidmpris.probe/.ProbeNotificationListener`. |
| Apple Music playing-state probe | PASS | Live probe observed `com.apple.android.music`, title, artist, album, duration, playing state, actions, content artwork URI, and 315x315 bitmap artwork. |
| ADB command receiver | PASS | `pause` and `play` broadcast commands returned `ok: true` and updated Apple Music playback state. |
| Live MPRIS metadata | PASS | `playerctl` read live title / artist / album / length from Apple Music through `waydroid_mpris`. |
| Live MPRIS position | PASS | Repeated MPRIS `Position` reads advance during Apple Music playback after host projection. |
| Live MPRIS controls | PASS | `pause`, `play`, `play-pause`, `next`, and `previous` reached Apple Music through MPRIS -> host daemon -> ADB -> Android receiver. |
| Live MPRIS artwork | PASS | `mpris:artUrl` points to a host-readable, IEND-complete cached PNG file; invalid prior cache was replaced. |
| Diagnostics | PASS | `scripts/doctor.py` distinguishes host daemon absence as WARN and returns all PASS while daemon is running. |
| Documentation | PASS | README / Quickstart / usage guide / generated systemd helper / static sample unit are project-specific. |
| Disruptive restart QA | PASS | During Waydroid stop, MPRIS changed from `Playing` to `Stopped`; after restart, ADB reauthorization restored access. |
| Absent Apple Music session | PASS | After restart, companion snapshot had `sessionCount: 0`; host MPRIS reported `Stopped`, `CanControl=false`, and `playerctl play-pause` exited 1. |

## Acceptance Criteria Coverage

| ID | Result | Evidence |
| --- | --- | --- |
| AC-001 | PASS | Android companion recorded Apple Music package, metadata keys, playback state, actions, and artwork availability. |
| AC-002 | PASS | Fixture daemon and live daemon expose MPRIS metadata; `playerctl` reads status and metadata. |
| AC-003 | PASS | `playerctl pause/play/play-pause/next/previous` reached selected Apple Music session. |
| AC-004 | PASS | Host maps ADB read failure to empty snapshot, unit tests stale mapping, and disruptive QA confirmed `Playing` did not remain while Waydroid was stopped. |
| AC-005 | PASS | Android exports album art as PNG, host atomically caches and validates it, and `playerctl metadata mpris:artUrl` returns a readable complete `file://` URI. |
| AC-006 | PASS | README, Quickstart, usage guide, doctor command, user service helper, and static sample unit document build / install / run / diagnose. |
| AC-007 | PASS | `tests/test_position_projection.py` covers monotonic projection, pause holding, duration clamp, and missing-session reset; live `Position` advances during playback. |

## Invariant Coverage

| ID | Result | Evidence |
| --- | --- | --- |
| INV-001 | PASS | Android snapshot code reads MediaSession metadata/state/capabilities and does not forward raw notification payloads. |
| INV-002 | PASS | Missing-session mapping and ADB read failure path are unit-tested; disruptive QA confirmed stopped-source state does not remain `Playing`. |
| INV-003 | PASS | Commands resolve the current Apple Music MediaSession, host reads Android command result and raises on `ok:false`, and no broadcast fallback to other apps is implemented. |
| INV-004 | PASS | Current live transport uses ADB and user-session D-Bus; no host network listener is opened. |
| INV-005 | PASS | Artwork cache failure is isolated from metadata/control; host only publishes complete cached host-readable `file://` art URLs and replaces truncated cache entries. |
| INV-006 | PASS | Host MPRIS daemon remains fixture-testable without live Waydroid. |
| INV-007 | PASS | TODO / plan / survey / reference / QA were updated with M0-M6 and compatibility-hardening findings. |

## Deferred / Not Covered

- The bridge does not fetch or provide lyrics. Lyric display remains dependent
  on the MPRIS consumer and its own lyric provider coverage.
- Extension-side cache invalidation is outside this bridge. The bridge now
  publishes complete PNG art and replaces its own truncated cache entries, but a
  third-party extension may still need reload or track change to discard its own
  older invalid cache.

## Residual Risks

None

## Operational Notes

- This Waydroid setup can require container-service restart and Android ADB
  reauthorization after disruptive stop/restart.
- For daily use, approve the Android ADB debugging prompt with "Always allow
  from this computer"; otherwise the host daemon will fall back to `Stopped` /
  no active media while the device is `unauthorized`.
- ADB polling is verified for this local setup, but longer daily-use
  observation may still motivate a socket transport.

## Follow-up TODOs

None for the bridge MVP.
