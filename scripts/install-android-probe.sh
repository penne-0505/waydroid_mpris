#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APK="$("$ROOT_DIR/scripts/build-android-probe.sh")"
PACKAGE="dev.penne.waydroidmpris.probe"

adb install --no-incremental -r "$APK"
adb shell am start -n "$PACKAGE/.MainActivity"

echo "Installed and launched Waydroid MPRIS Probe."
echo "If the app reports notification listener disabled, open the settings button and allow Waydroid MPRIS Probe."
