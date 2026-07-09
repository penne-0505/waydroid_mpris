#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="waydroid-mpris"
POLL_INTERVAL="1.0"
DEVICE=""
ENABLE_NOW=0
DRY_RUN=0
FORCE=0

usage() {
  cat <<'EOF'
Usage: ./scripts/install-user-service.sh [options]

Generate and install a systemd user service for the Waydroid MPRIS host daemon.
This script does not use sudo and only writes under ~/.config/systemd/user.

Options:
  --device SERIAL          Pass a fixed ADB serial to the host daemon.
  --poll-interval SECONDS  Poll interval for ADB snapshot reads. Default: 1.0.
  --service-name NAME      systemd user service name without .service.
                           Default: waydroid-mpris.
  --enable-now            Enable and start the service after installing it.
  --force                 Overwrite an existing generated service file.
  --dry-run               Print the generated unit without writing it.
  -h, --help              Show this help.

Examples:
  ./scripts/install-user-service.sh --enable-now
  ./scripts/install-user-service.sh --device 192.168.240.112:5555 --enable-now
  ./scripts/install-user-service.sh --dry-run
EOF
}

die() {
  echo "error: $*" >&2
  exit 1
}

systemd_quote_arg() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//%/%%}"
  printf '"%s"' "$value"
}

systemd_literal_value() {
  local value="$1"
  value="${value//%/%%}"
  printf '%s' "$value"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --device)
      [[ $# -ge 2 ]] || die "--device requires a value"
      DEVICE="$2"
      shift 2
      ;;
    --device=*)
      DEVICE="${1#--device=}"
      shift
      ;;
    --poll-interval)
      [[ $# -ge 2 ]] || die "--poll-interval requires a value"
      POLL_INTERVAL="$2"
      shift 2
      ;;
    --poll-interval=*)
      POLL_INTERVAL="${1#--poll-interval=}"
      shift
      ;;
    --service-name)
      [[ $# -ge 2 ]] || die "--service-name requires a value"
      SERVICE_NAME="$2"
      shift 2
      ;;
    --service-name=*)
      SERVICE_NAME="${1#--service-name=}"
      shift
      ;;
    --enable-now)
      ENABLE_NOW=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown option: $1"
      ;;
  esac
done

SERVICE_NAME="${SERVICE_NAME%.service}"
[[ "$SERVICE_NAME" =~ ^[A-Za-z0-9_.@-]+$ ]] || die "invalid service name: $SERVICE_NAME"
[[ -n "$POLL_INTERVAL" ]] || die "--poll-interval must not be empty"

PYTHON_BIN="${PYTHON:-python}"
PYTHON_PATH="$(command -v "$PYTHON_BIN" || true)"
[[ -n "$PYTHON_PATH" ]] || die "python executable not found: $PYTHON_BIN"

HOST_SCRIPT="$ROOT_DIR/scripts/run-host-mpris-live.py"
[[ -f "$HOST_SCRIPT" ]] || die "host daemon script not found: $HOST_SCRIPT"

EXEC_START="$(systemd_quote_arg "$PYTHON_PATH") $(systemd_quote_arg "$HOST_SCRIPT") --poll-interval $(systemd_quote_arg "$POLL_INTERVAL")"
if [[ -n "$DEVICE" ]]; then
  EXEC_START="$EXEC_START --device $(systemd_quote_arg "$DEVICE")"
fi

UNIT_CONTENT="$(cat <<EOF
[Unit]
Description=Waydroid MPRIS bridge
Documentation=https://github.com/penne-0505/waydroid_mpris
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
WorkingDirectory=$(systemd_literal_value "$ROOT_DIR")
ExecStart=$EXEC_START
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
EOF
)"

if [[ "$DRY_RUN" -eq 1 ]]; then
  printf '%s\n' "$UNIT_CONTENT"
  exit 0
fi

command -v systemctl >/dev/null 2>&1 || die "systemctl not found"

if [[ -n "${XDG_CONFIG_HOME:-}" ]]; then
  USER_UNIT_DIR="$XDG_CONFIG_HOME/systemd/user"
else
  [[ -n "${HOME:-}" ]] || die "HOME is not set"
  USER_UNIT_DIR="$HOME/.config/systemd/user"
fi
UNIT_FILE="$USER_UNIT_DIR/$SERVICE_NAME.service"

mkdir -p "$USER_UNIT_DIR"

if [[ -e "$UNIT_FILE" && "$FORCE" -ne 1 ]]; then
  die "$UNIT_FILE already exists; rerun with --force to overwrite it"
fi

TMP_FILE="$(mktemp "$USER_UNIT_DIR/$SERVICE_NAME.service.XXXXXX")"
trap 'rm -f "$TMP_FILE"' EXIT
printf '%s\n' "$UNIT_CONTENT" > "$TMP_FILE"
mv "$TMP_FILE" "$UNIT_FILE"
trap - EXIT

systemctl --user daemon-reload

echo "Installed systemd user service: $UNIT_FILE"

if [[ "$ENABLE_NOW" -eq 1 ]]; then
  systemctl --user enable --now "$SERVICE_NAME.service"
  echo "Enabled and started: $SERVICE_NAME.service"
else
  echo "Next:"
  echo "  systemctl --user enable --now $SERVICE_NAME.service"
  echo "  systemctl --user status $SERVICE_NAME.service"
fi
