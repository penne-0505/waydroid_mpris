#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE="dev.penne.waydroidmpris.probe"
DEVICE=""
APK=""
ADB="${ADB:-adb}"
PYTHON_BIN="${PYTHON:-python}"

usage() {
  cat <<'EOF'
Usage: ./scripts/install-android-probe.sh [--device SERIAL] [--apk PATH]

Build and install the Android companion on the running Waydroid target.
Use --device to override Waydroid discovery, or --apk to install an existing APK.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --device) [[ $# -ge 2 ]] || { echo "error: --device requires a value" >&2; exit 2; }; DEVICE="$2"; shift 2 ;;
    --device=*) DEVICE="${1#--device=}"; shift ;;
    --apk) [[ $# -ge 2 ]] || { echo "error: --apk requires a value" >&2; exit 2; }; APK="$2"; shift 2 ;;
    --apk=*) APK="${1#--apk=}"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "error: unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$APK" ]]; then
  APK="$("$ROOT_DIR/scripts/build-android-probe.sh")"
fi
[[ -f "$APK" ]] || { echo "error: APK not found: $APK" >&2; exit 1; }

resolver=("$PYTHON_BIN" "$ROOT_DIR/scripts/resolve-waydroid-adb-target.py" --adb "$ADB")
if [[ -n "$DEVICE" ]]; then
  resolver+=(--device "$DEVICE")
fi
TARGET="$("${resolver[@]}")"

if ! install_output="$("$ADB" -s "$TARGET" install --no-incremental -r "$APK" 2>&1)"; then
  printf '%s\n' "$install_output" >&2
  # intent why-not: INV-004 (Core/reproducible-arch-setup) — uninstall would reset app state and notification-listener permission.
  if [[ "$install_output" == *INSTALL_FAILED_UPDATE_INCOMPATIBLE* ]]; then
    echo "error: the installed companion was signed with another debug key." >&2
    echo "Remove dev.penne.waydroidmpris.probe manually, reinstall, and enable notification-listener access again." >&2
  fi
  exit 1
fi
printf '%s\n' "$install_output"
"$ADB" -s "$TARGET" shell am start -n "$PACKAGE/.MainActivity"

echo "Installed and launched Waydroid MPRIS Probe on $TARGET."
echo "If the app reports notification listener disabled, open the settings button and allow Waydroid MPRIS Probe."
