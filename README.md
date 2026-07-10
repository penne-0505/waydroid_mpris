# waydroid_mpris

Waydroid 上の Apple Music を GNOME / `playerctl` から通常の MPRIS player として扱うための bridge です。

Android companion が Apple Music の MediaSession から曲名、再生状態、操作 capability、artwork を読み、Linux host daemon がそれを `org.mpris.MediaPlayer2.waydroid_mpris` として公開します。

## Current Status

- Live metadata: verified with Apple Music in Waydroid.
- Controls: `play`, `pause`, `play-pause`, `next`, `previous` verified through `playerctl`.
- Artwork: Android bitmap artwork is exported, cached on host, and exposed as `mpris:artUrl`.
- Position: MPRIS `Position` is projected while playing for seek bars and synchronized lyric clients.
- Transport: ADB-backed local bridge. No host network listener is opened.
- Recovery: the live daemon discovers the running Waydroid IP, reconnects a missing/offline ADB target with bounded backoff, and keeps `unauthorized` as an operator action. Automated coverage passes; disruptive live recovery QA remains deferred.

The bridge verification record is in [_docs/qa/Core/waydroid-mpris-bridge/verification.md](_docs/qa/Core/waydroid-mpris-bridge/verification.md). Automatic recovery has a `PARTIAL` verification record in [_docs/qa/Core/waydroid-adb-auto-recovery/verification.md](_docs/qa/Core/waydroid-adb-auto-recovery/verification.md); live restart / authorization QA requires explicit approval.

## Requirements

- Waydroid with Apple Music installed and signed in.
- `adb`, `playerctl`, `python`.
- Android SDK build tools. By default the build script uses `/home/penne/Android/Sdk`, or `ANDROID_HOME` / `ANDROID_SDK_ROOT` if set.
- ADB authorization for this host inside Waydroid. For daily use, allow the USB
  debugging prompt with "Always allow from this computer" so the daemon can
  reconnect after Waydroid or ADB restarts.
- Notification listener access for `Waydroid MPRIS Probe` inside Waydroid.

## Build And Install

```bash
./scripts/build-android-probe.sh
./scripts/install-android-probe.sh
./scripts/open-android-notification-listener-settings.sh
```

Enable `Waydroid MPRIS Probe` in Android notification listener settings, then start Apple Music playback.

## Run

Apple Music playback is visible to GNOME only while the host MPRIS daemon is
running. The Android companion records the media session, but it does not publish
MPRIS by itself.

```bash
python scripts/run-host-mpris-live.py --poll-interval 1.0
```

The daemon resolves the running Waydroid IP and scopes every bridge command to
that ADB serial, so unrelated connected devices are not selected. To pin a
specific Waydroid serial instead of using discovery:

```bash
python scripts/run-host-mpris-live.py --device 192.168.240.112:5555 --poll-interval 1.0
```

If Waydroid shows a USB debugging authorization prompt, allow this computer.
Without ADB authorization the daemon cannot read the Android companion snapshot,
so MPRIS consumers may show `No active media` / `Stopped` even while Apple Music
is playing. The daemon does not bypass `unauthorized`; after approval, its
read-only state checks resume the bridge automatically.

Check from host:

```bash
playerctl --list-all
playerctl --player=waydroid_mpris metadata --format '{{title}}|{{artist}}|{{mpris:artUrl}}'
playerctl --player=waydroid_mpris play-pause
```

If `playerctl --list-all` does not show `waydroid_mpris`, start the host daemon
or enable the systemd user service from the usage guide.

## Optional User Service

For daily use, generate and install a systemd user service from the current
checkout path:

```bash
./scripts/install-user-service.sh --enable-now
```

To pin a specific serial in the generated service:

```bash
./scripts/install-user-service.sh --device 192.168.240.112:5555 --enable-now
```

## Diagnostics

```bash
python scripts/doctor.py
```

The doctor is read-only. It reports the resolved target as `device`, `missing`,
`offline`, or `unauthorized`; the last state explicitly requires approval inside
Waydroid.

For systemd user service setup and troubleshooting details, see [_docs/guide/Core/waydroid-mpris-bridge/usage.md](_docs/guide/Core/waydroid-mpris-bridge/usage.md).

## Development Checks

```bash
python -m unittest tests/test_protocol_mapping.py tests/test_adb_transport.py tests/test_adb_recovery.py tests/test_live_failure_mapping.py tests/test_position_projection.py tests/test_artwork_cache.py
python -m py_compile host/waydroid_mpris/*.py scripts/run-host-mpris-live.py scripts/run-host-mpris-fixture.py scripts/doctor.py scripts/run-disruptive-waydroid-restart-qa.py
bash -n scripts/install-user-service.sh
./scripts/install-user-service.sh --dry-run
./scripts/build-android-probe.sh
./scripts/check-docs.sh
git diff --check
```

## License

[MIT](LICENSE.txt)
