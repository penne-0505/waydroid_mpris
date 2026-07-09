---
title: Waydroid MPRIS bridge usage guide
status: active
draft_status: n/a
created_at: 2026-07-09
updated_at: 2026-07-09
references:
  - "_docs/intent/Core/waydroid-mpris-bridge/decision.md"
  - "_docs/reference/Core/bridge-protocol/reference.md"
  - "_docs/qa/Core/waydroid-mpris-bridge/verification.md"
related_issues: []
related_prs: []
---

# Waydroid MPRIS bridge usage guide

## Requirements

- EndeavourOS / GNOME user session with D-Bus and MPRIS consumers.
- Waydroid running with Apple Music installed and signed in.
- `adb`, `playerctl`, `python`, and Android SDK build tools.
- ADB authorization for this host inside Waydroid. For daily use, approve the
  USB debugging prompt with "Always allow from this computer" so reconnects do
  not leave the device in `unauthorized`.
- Android notification listener access for `Waydroid MPRIS Probe`.

## Build And Install Android Companion

```bash
./scripts/build-android-probe.sh
./scripts/install-android-probe.sh
```

If Android blocks the debug APK as unsafe, allow it in the Waydroid prompt and
run the install command again. Then open notification listener settings:

```bash
./scripts/open-android-notification-listener-settings.sh
```

Enable `Waydroid MPRIS Probe`, start Apple Music playback, and leave Waydroid
ADB authorized. If the device is listed as `unauthorized`, reconnect with
`adb connect 192.168.240.112:5555` and approve the prompt inside Waydroid. While
ADB is unauthorized, the host daemon intentionally exposes `Stopped` / no active
track instead of stale Apple Music metadata.

## Run Host Daemon

The host daemon is required for GNOME / `playerctl` integration. The Android
companion can observe Apple Music by itself, but nothing is published as MPRIS
until `waydroid_mpris` is running on the host user session bus.

```bash
python scripts/run-host-mpris-live.py --poll-interval 1.0
```

If more than one ADB device is connected, pass the Waydroid serial:

```bash
python scripts/run-host-mpris-live.py --device 192.168.240.112:5555 --poll-interval 1.0
```

Check the exposed player:

```bash
playerctl --list-all
playerctl --player=waydroid_mpris metadata --format '{{title}}|{{artist}}|{{mpris:artUrl}}'
playerctl --player=waydroid_mpris play-pause
```

## Systemd User Service

Use the install helper for daily use. It writes a user service under
`~/.config/systemd/user`, fills in this checkout path, reloads the user systemd
manager, and starts the service only when `--enable-now` is passed.

```bash
./scripts/install-user-service.sh --enable-now
systemctl --user status waydroid-mpris.service
```

If more than one ADB device is connected, install the service with an explicit
serial:

```bash
./scripts/install-user-service.sh --device 192.168.240.112:5555 --enable-now
```

Use `./scripts/install-user-service.sh --dry-run` to inspect the generated unit
without writing it. If you need to reinstall after changing the serial or repo
path, rerun the helper with `--force`.

The static sample unit remains at `packaging/systemd/waydroid-mpris.service` for
manual inspection. It assumes the checkout lives at
`%h/dev/incubator/waydroid_mpris`; edit the paths if copying it by hand.

## Diagnostics

```bash
python scripts/doctor.py
```

The doctor distinguishes missing host commands, Waydroid not running, ADB device
absence, missing companion package, notification listener denial, missing Apple
Music session, absent artwork file, and host MPRIS daemon absence.

## Recovery Checklist

If metadata disappears or commands stop working:

```bash
python scripts/doctor.py
adb devices
waydroid status
./scripts/install-user-service.sh --dry-run
systemctl --user restart waydroid-mpris.service
```

If ADB no longer lists Waydroid as `device`, reconnect with
`adb connect 192.168.240.112:5555`, reopen Waydroid if needed, and accept the
ADB authorization prompt if Android shows one. For daily use, choose "Always
allow from this computer". If the notification listener check fails, run
`./scripts/open-android-notification-listener-settings.sh` and enable `Waydroid
MPRIS Probe` again.

The host daemon maps ADB read failure to an empty snapshot, so `playerctl`
should stop seeing the last Apple Music track as `Playing`.

After explicitly approving an interruption, the disruptive QA can be run with:

```bash
python scripts/run-disruptive-waydroid-restart-qa.py \
  --i-understand-this-stops-waydroid \
  --device 192.168.240.112:5555 \
  --output /tmp/waydroid-mpris-restart-qa.json
```

The script starts the host daemon, records the current MPRIS state, stops the
Waydroid session, verifies that `Playing` does not remain stale, starts
Waydroid again, waits for ADB, opens the companion activity, and writes a JSON
report.

On this EndeavourOS / Waydroid setup, `waydroid session start` alone timed out
once during disruptive QA. Recovery required stopping the container service and
starting it again with system privileges, then accepting the Android ADB
authorization prompt after Waydroid returned:

```bash
sudo waydroid container stop
sudo systemctl stop waydroid-container.service
sudo systemctl start waydroid-container.service
waydroid session start
adb connect 192.168.240.112:5555
```

## Current Limitations

- Transport is ADB-backed polling, not a socket protocol.
- The bridge exposes synchronized MPRIS `Position`, but it does not provide
  lyrics itself. Extensions that show lyrics may still depend on their own
  lyric provider coverage for the current track.
- Waydroid restart can require Android ADB reauthorization before the bridge can
  read snapshots again.
- The Android app is still named `Waydroid MPRIS Probe` internally because the
  probe app became the companion app seed.
