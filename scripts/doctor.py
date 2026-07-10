#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "host"))

from waydroid_mpris.adb_recovery import (  # noqa: E402
    AdbRecoveryError,
    AdbRecoveryManager,
    ConnectionInspection,
)


DEFAULT_PROBE_PATH = "/sdcard/Android/data/dev.penne.waydroidmpris.probe/files/latest_probe.json"
LISTENER_COMPONENT = "dev.penne.waydroidmpris.probe/dev.penne.waydroidmpris.probe.ProbeNotificationListener"
PACKAGE_NAME = "dev.penne.waydroidmpris.probe"


@dataclass
class Check:
    name: str
    status: str
    detail: str


def run(command: list[str], timeout: float = 5.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose the Waydroid MPRIS bridge setup.")
    parser.add_argument("--adb", default="adb", help="adb executable path.")
    parser.add_argument("--waydroid", default="waydroid", help="waydroid executable path.")
    parser.add_argument(
        "--device",
        default=None,
        help="Inspect a pinned ADB serial instead of discovering the running Waydroid IP.",
    )
    parser.add_argument("--probe-path", default=DEFAULT_PROBE_PATH, help="Android path to latest_probe.json.")
    args = parser.parse_args()

    checks: list[Check] = []
    adb_args: list[str] | None = None

    command_paths = {
        "waydroid": args.waydroid,
        "adb": args.adb,
        "playerctl": "playerctl",
        "python": "python",
    }
    for command_name, executable in command_paths.items():
        path = shutil.which(executable)
        checks.append(Check(command_name, "PASS" if path else "FAIL", path or "not found in PATH"))

    if shutil.which(args.waydroid):
        result = run([args.waydroid, "status"])
        checks.append(check_from_process("waydroid status", result, expect_contains="RUNNING"))

    if shutil.which(args.adb):
        recovery = AdbRecoveryManager(
            adb_path=args.adb,
            waydroid_path=args.waydroid,
            device=args.device,
        )
        try:
            inspection = recovery.inspect()
        except AdbRecoveryError as ex:
            checks.append(check_from_recovery_error(ex))
        else:
            checks.append(check_from_inspection(inspection))
            if inspection.ready:
                adb_args = [args.adb, "-s", inspection.target]

    if adb_args is not None:
        package = run(adb_args + ["shell", "pm", "list", "packages", PACKAGE_NAME])
        checks.append(
            Check(
                "android companion package",
                "PASS" if PACKAGE_NAME in package.stdout else "FAIL",
                compact(package.stdout or package.stderr),
            )
        )

        listeners = run(adb_args + ["shell", "settings", "get", "secure", "enabled_notification_listeners"])
        checks.append(
            Check(
                "notification listener",
                "PASS" if LISTENER_COMPONENT in listeners.stdout else "FAIL",
                compact(listeners.stdout or listeners.stderr),
            )
        )

        probe = run(adb_args + ["shell", "cat", args.probe_path])
        if probe.returncode == 0:
            checks.extend(check_probe_snapshot(probe.stdout))
        else:
            checks.append(Check("latest probe", "FAIL", compact(probe.stderr or probe.stdout)))

    if shutil.which("playerctl"):
        players = run(["playerctl", "--list-all"])
        has_player = "waydroid_mpris" in players.stdout.split()
        checks.append(
            Check(
                "host MPRIS player",
                "PASS" if has_player else "WARN",
                "waydroid_mpris present" if has_player else "host daemon is not currently running",
            )
        )
        if has_player:
            status = run(["playerctl", "--player=waydroid_mpris", "status"])
            checks.append(check_from_process("playerctl status", status))
            metadata = run(
                [
                    "playerctl",
                    "--player=waydroid_mpris",
                    "metadata",
                    "--format",
                    "{{title}}|{{artist}}|{{mpris:artUrl}}",
                ]
            )
            checks.append(check_mpris_metadata(status, metadata))

    for check in checks:
        print(f"{check.status:<4} {check.name}: {check.detail}")

    return 1 if any(check.status == "FAIL" for check in checks) else 0


def check_from_process(name: str, result: subprocess.CompletedProcess[str], expect_contains: str | None = None) -> Check:
    detail = compact(result.stdout or result.stderr)
    ok = result.returncode == 0 and (expect_contains is None or expect_contains in result.stdout)
    return Check(name, "PASS" if ok else "FAIL", detail)


def check_from_inspection(inspection: ConnectionInspection) -> Check:
    target = inspection.target
    if inspection.ready:
        return Check("adb target", "PASS", f"{target} is device")
    if inspection.state == "unauthorized":
        return Check(
            "adb target",
            "FAIL",
            f"{target} is unauthorized; approve the debugging prompt inside Waydroid (operator action required)",
        )
    if inspection.state in {"missing", "offline"}:
        return Check(
            "adb target",
            "FAIL",
            f"{target} is {inspection.state}; the daemon will retry adb connect with backoff",
        )
    return Check("adb target", "FAIL", f"{target} has unsupported state {inspection.state}")


def check_from_recovery_error(error: AdbRecoveryError) -> Check:
    action = "; operator action required" if error.operator_action_required else ""
    return Check("adb target", "FAIL", f"{error}{action}")


def check_mpris_metadata(
    status: subprocess.CompletedProcess[str],
    metadata: subprocess.CompletedProcess[str],
) -> Check:
    if status.returncode == 0 and status.stdout.strip() == "Stopped":
        if metadata.stdout.strip():
            return Check("playerctl metadata", "FAIL", "metadata remained non-empty while Stopped")
        return Check("playerctl metadata", "PASS", "empty while Stopped")
    return check_from_process("playerctl metadata", metadata)


def check_probe_snapshot(raw: str) -> list[Check]:
    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as ex:
        return [Check("latest probe", "FAIL", f"invalid JSON: {ex}")]

    selected = data.get("selectedAppleMusicSession")
    if not isinstance(selected, dict):
        return [Check("latest probe", "FAIL", "Apple Music session is absent")]

    metadata = selected.get("metadata") or {}
    playback = selected.get("playbackState") or {}
    title = metadata.get("title") or "<missing title>"
    artist = metadata.get("artist") or "<missing artist>"
    state = playback.get("state") or "<missing state>"
    art = metadata.get("artworkFile") or {}
    art_detail = "artwork file present" if art.get("present") else "artwork file absent"
    return [
        Check("latest probe", "PASS", f"{title} / {artist} / {state}"),
        Check("latest probe artwork", "PASS" if art.get("present") else "WARN", art_detail),
    ]


def compact(value: str) -> str:
    single = " ".join(value.strip().split())
    return single[:240] if single else "<empty>"


if __name__ == "__main__":
    sys.exit(main())
