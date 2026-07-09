#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Any


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
    parser.add_argument("--device", default=None, help="adb device serial, if more than one device is connected.")
    parser.add_argument("--probe-path", default=DEFAULT_PROBE_PATH, help="Android path to latest_probe.json.")
    args = parser.parse_args()

    checks: list[Check] = []
    adb_args = ["adb"]
    if args.device:
        adb_args.extend(["-s", args.device])

    for command_name in ["waydroid", "adb", "playerctl", "python"]:
        path = shutil.which(command_name)
        checks.append(Check(command_name, "PASS" if path else "FAIL", path or "not found in PATH"))

    if shutil.which("waydroid"):
        result = run(["waydroid", "status"])
        checks.append(check_from_process("waydroid status", result, expect_contains="RUNNING"))

    if shutil.which("adb"):
        devices = run(["adb", "devices"])
        device_ok = any(line.strip().endswith("\tdevice") for line in devices.stdout.splitlines())
        checks.append(Check("adb device", "PASS" if device_ok else "FAIL", compact(devices.stdout or devices.stderr)))

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
            checks.append(check_from_process("playerctl metadata", metadata))

    for check in checks:
        print(f"{check.status:<4} {check.name}: {check.detail}")

    return 1 if any(check.status == "FAIL" for check in checks) else 0


def check_from_process(name: str, result: subprocess.CompletedProcess[str], expect_contains: str | None = None) -> Check:
    detail = compact(result.stdout or result.stderr)
    ok = result.returncode == 0 and (expect_contains is None or expect_contains in result.stdout)
    return Check(name, "PASS" if ok else "FAIL", detail)


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
