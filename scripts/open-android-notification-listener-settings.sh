#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEVICE=""
ADB="${ADB:-adb}"
PYTHON_BIN="${PYTHON:-python}"

if [[ $# -gt 0 ]]; then
  case "$1" in
    --device) [[ $# -eq 2 ]] || { echo "error: --device requires one value" >&2; exit 2; }; DEVICE="$2" ;;
    --device=*) [[ $# -eq 1 ]] || { echo "error: unexpected arguments" >&2; exit 2; }; DEVICE="${1#--device=}" ;;
    -h|--help) echo "Usage: ./scripts/open-android-notification-listener-settings.sh [--device SERIAL]"; exit 0 ;;
    *) echo "error: unknown option: $1" >&2; exit 2 ;;
  esac
fi

resolver=("$PYTHON_BIN" "$ROOT_DIR/scripts/resolve-waydroid-adb-target.py" --adb "$ADB")
if [[ -n "$DEVICE" ]]; then
  resolver+=(--device "$DEVICE")
fi
TARGET="$("${resolver[@]}")"
"$ADB" -s "$TARGET" shell am start -a android.settings.ACTION_NOTIFICATION_LISTENER_SETTINGS
