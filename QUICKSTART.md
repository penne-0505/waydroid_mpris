# Quickstart

## 1. Prerequisites

Supported baseline: Arch 系 Linux with GNOME / systemd user session. Install
host dependencies and provide an existing Android SDK Platform + Build-Tools:

```bash
sudo pacman -S --needed python python-dbus python-gobject playerctl android-tools jdk-openjdk
export ANDROID_SDK_ROOT="$HOME/Android/Sdk"  # when auto-discovery does not match your setup
```

```bash
command -v adb
command -v playerctl
command -v python
python -c 'import dbus, gi'
waydroid status
adb devices
```

Waydroid must be running, and Apple Music must be installed and signed in. The
host daemon discovers the running Waydroid IP and runs `adb connect` when its
target is missing or offline. If Waydroid shows a USB debugging prompt, allow
this computer. For daily use, enable "Always allow from this computer";
Android can still expire that grant after an inactivity window. An
`unauthorized` target requires operator approval and the host player remains
`Stopped` / no active media until approval. See the [usage guide](docs/usage.md)
"ADB authorization timeout" section for diagnosis and prevention.

## 2. Android Companion

```bash
./scripts/build-android-probe.sh
./scripts/install-android-probe.sh
./scripts/open-android-notification-listener-settings.sh
```

The helpers resolve the running Waydroid target and never select another ready
ADB device. Use `--device SERIAL` to override discovery. If a reinstall fails
with `INSTALL_FAILED_UPDATE_INCOMPATIBLE`, manually remove the existing
companion, reinstall, and enable notification-listener access again.

Enable `Waydroid MPRIS Probe` in the Android settings screen. Start playback in Apple Music.

## 3. Host MPRIS Daemon

This step is required. Apple Music playback in Waydroid will not appear in GNOME
until the host daemon is running.

```bash
python scripts/run-host-mpris-live.py --poll-interval 1.0
```

Unrelated ADB devices are not selected by automatic discovery. To pin a specific
Waydroid serial:

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

Success means `playerctl --list-all` contains `waydroid_mpris`, status matches
Apple Music, metadata contains the current title / artist, and doctor reports
PASS. Automatic recovery after a disruptive Waydroid restart needs a separate
live check that stops the Waydroid session; it is not required for initial setup
reproduction.

## 5. Optional Systemd User Service

Use this if you want the host daemon to start automatically in daily use.

Generate a service from this checkout path and start it:

```bash
./scripts/install-user-service.sh --enable-now
```

To pin a specific serial in the service:

```bash
./scripts/install-user-service.sh --device 192.168.240.112:5555 --enable-now
```

Use `--dry-run` to inspect the generated unit before installing it. The static
sample remains available at `packaging/systemd/waydroid-mpris.service`.

## 6. Development Workflow

Run the project checks before completing a change:

```bash
python -m unittest tests/test_protocol_mapping.py tests/test_adb_transport.py \
  tests/test_adb_recovery.py tests/test_live_failure_mapping.py \
  tests/test_position_projection.py tests/test_artwork_cache.py \
  tests/test_android_setup.py tests/test_doctor_json.py
```
