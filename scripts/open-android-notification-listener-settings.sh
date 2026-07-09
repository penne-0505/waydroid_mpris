#!/usr/bin/env bash
set -euo pipefail

adb shell am start -a android.settings.ACTION_NOTIFICATION_LISTENER_SETTINGS
