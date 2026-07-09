# Quickstart

## 1. Prerequisites

```bash
command -v adb
command -v playerctl
command -v python
waydroid status
adb devices
```

Waydroid must be running, ADB must show the Waydroid device as `device`, and Apple Music must be installed and signed in.
If Waydroid shows a USB debugging prompt, allow this computer. For daily use,
enable "Always allow from this computer"; otherwise ADB may become
`unauthorized` after reconnects and the host player will fall back to
`Stopped` / no active media.

## 2. Android Companion

```bash
./scripts/build-android-probe.sh
./scripts/install-android-probe.sh
./scripts/open-android-notification-listener-settings.sh
```

Enable `Waydroid MPRIS Probe` in the Android settings screen. Start playback in Apple Music.

## 3. Host MPRIS Daemon

This step is required. Apple Music playback in Waydroid will not appear in GNOME
until the host daemon is running.

```bash
python scripts/run-host-mpris-live.py --poll-interval 1.0
```

If ADB has more than one device:

```bash
python scripts/run-host-mpris-live.py --device 192.168.240.112:5555 --poll-interval 1.0
```

## 4. Verify

```bash
playerctl --list-all
playerctl --player=waydroid_mpris status
playerctl --player=waydroid_mpris metadata --format '{{title}}|{{artist}}|{{mpris:artUrl}}'
playerctl --player=waydroid_mpris play-pause
python scripts/doctor.py
```

## 5. Optional Systemd User Service

Use this if you want the host daemon to start automatically in daily use.

Generate a service from this checkout path and start it:

```bash
./scripts/install-user-service.sh --enable-now
```

If ADB has more than one device:

```bash
./scripts/install-user-service.sh --device 192.168.240.112:5555 --enable-now
```

Use `--dry-run` to inspect the generated unit before installing it. The static
sample remains available at `packaging/systemd/waydroid-mpris.service`.
