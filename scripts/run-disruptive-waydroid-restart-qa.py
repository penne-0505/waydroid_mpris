#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run disruptive Waydroid stop/restart QA for the MPRIS bridge.",
    )
    parser.add_argument(
        "--i-understand-this-stops-waydroid",
        action="store_true",
        help="Required. This stops the current Waydroid session and interrupts playback.",
    )
    parser.add_argument("--device", default=None, help="ADB device serial.")
    parser.add_argument("--poll-interval", type=float, default=0.5, help="Host daemon poll interval.")
    parser.add_argument("--settle-seconds", type=float, default=3.0, help="Seconds to wait after stop/start transitions.")
    parser.add_argument(
        "--restart-mode",
        choices=["session", "container-service"],
        default="session",
        help="Restart method. container-service requires passwordless sudo in non-interactive runs.",
    )
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON report path.")
    args = parser.parse_args()

    if not args.i_understand_this_stops_waydroid:
        print(
            "Refusing to run: pass --i-understand-this-stops-waydroid to stop/restart Waydroid.",
            file=sys.stderr,
        )
        return 2

    report: dict[str, Any] = {"checks": []}
    host = start_host_daemon(args.device, args.poll_interval)
    stopped = False
    try:
        wait_for_mpris(report)
        report["before_stop"] = collect_player_state()

        for name, command in stop_commands(args.restart_mode):
            append_check(report, name, run(command, timeout=30))
        stopped = True
        time.sleep(args.settle_seconds)
        stopped_state = collect_player_state(allow_failure=True)
        report["during_stop"] = stopped_state
        append_bool(
            report,
            "stale Playing cleared while Waydroid stopped",
            stopped_state.get("status") != "Playing",
            json.dumps(stopped_state, ensure_ascii=False),
        )

        for name, command in start_commands(args.restart_mode):
            append_check(report, name, run(command, timeout=60))
        stopped = False
        time.sleep(args.settle_seconds)
        wait_for_waydroid(report)
        wait_for_adb(report, args.device)

        # Open the companion once to refresh the notification listener probe after restart.
        adb = ["adb"]
        if args.device:
            adb.extend(["-s", args.device])
        append_check(
            report,
            "start companion activity",
            run(adb + ["shell", "am", "start", "-n", "dev.penne.waydroidmpris.probe/.MainActivity"], timeout=10),
        )
        time.sleep(args.settle_seconds)
        report["after_restart"] = collect_player_state(allow_failure=True)
        append_check(report, "doctor after restart", run([sys.executable, "scripts/doctor.py"], timeout=20))

    finally:
        if stopped:
            for _name, command in start_commands(args.restart_mode):
                run(command, timeout=60)
        terminate(host)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if any(check["status"] == "FAIL" for check in report["checks"]) else 0


def start_host_daemon(device: str | None, poll_interval: float) -> subprocess.Popen[str]:
    command = [
        sys.executable,
        "scripts/run-host-mpris-live.py",
        "--poll-interval",
        str(poll_interval),
    ]
    if device:
        command.extend(["--device", device])
    return subprocess.Popen(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def terminate(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def stop_commands(restart_mode: str) -> list[tuple[str, list[str]]]:
    if restart_mode == "container-service":
        return [
            ("waydroid container stop", ["sudo", "-n", "waydroid", "container", "stop"]),
            ("waydroid-container service stop", ["sudo", "-n", "systemctl", "stop", "waydroid-container.service"]),
        ]
    return [("waydroid session stop", ["waydroid", "session", "stop"])]


def start_commands(restart_mode: str) -> list[tuple[str, list[str]]]:
    if restart_mode == "container-service":
        return [
            ("waydroid-container service start", ["sudo", "-n", "systemctl", "start", "waydroid-container.service"]),
            ("waydroid session start", ["waydroid", "session", "start"]),
        ]
    return [("waydroid session start", ["waydroid", "session", "start"])]


def wait_for_mpris(report: dict[str, Any], timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    last = ""
    while time.monotonic() < deadline:
        result = run(["playerctl", "--list-all"], timeout=5)
        last = result.stdout or result.stderr
        if result.returncode == 0 and "waydroid_mpris" in result.stdout.split():
            append_bool(report, "host MPRIS appears", True, "waydroid_mpris present")
            return
        time.sleep(0.5)
    append_bool(report, "host MPRIS appears", False, compact(last))


def wait_for_waydroid(report: dict[str, Any], timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    last = ""
    while time.monotonic() < deadline:
        result = run(["waydroid", "status"], timeout=5)
        last = result.stdout or result.stderr
        if result.returncode == 0 and "Session:\tRUNNING" in result.stdout and "Container:\tRUNNING" in result.stdout:
            append_bool(report, "Waydroid restarted", True, compact(result.stdout))
            return
        time.sleep(1.0)
    append_bool(report, "Waydroid restarted", False, compact(last))


def wait_for_adb(report: dict[str, Any], device: str | None, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    last = ""
    while time.monotonic() < deadline:
        result = run(["adb", "devices"], timeout=5)
        last = result.stdout or result.stderr
        for line in result.stdout.splitlines():
            if line.strip().endswith("\tdevice") and (device is None or line.startswith(device)):
                append_bool(report, "ADB reconnected", True, compact(result.stdout))
                return
        time.sleep(1.0)
    append_bool(report, "ADB reconnected", False, compact(last))


def collect_player_state(allow_failure: bool = False) -> dict[str, Any]:
    status = run(["playerctl", "--player=waydroid_mpris", "status"], timeout=5)
    metadata = run(
        [
            "playerctl",
            "--player=waydroid_mpris",
            "metadata",
            "--format",
            "{{title}}|{{artist}}|{{mpris:artUrl}}",
        ],
        timeout=5,
    )
    state = {
        "status_returncode": status.returncode,
        "status": status.stdout.strip(),
        "status_error": compact(status.stderr),
        "metadata_returncode": metadata.returncode,
        "metadata": metadata.stdout.strip(),
        "metadata_error": compact(metadata.stderr),
    }
    if not allow_failure and status.returncode != 0:
        state["error"] = "playerctl status failed"
    return state


def run(command: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as ex:
        stdout = decode_timeout_stream(ex.stdout)
        stderr = decode_timeout_stream(ex.stderr)
        detail = f"timed out after {timeout} seconds"
        if stderr:
            detail = f"{detail}; stderr: {stderr}"
        if stdout:
            detail = f"{detail}; stdout: {stdout}"
        return subprocess.CompletedProcess(command, 124, stdout="", stderr=detail)


def decode_timeout_stream(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip()
    return value.strip()


def append_check(report: dict[str, Any], name: str, result: subprocess.CompletedProcess[str]) -> None:
    append_bool(report, name, result.returncode == 0, compact(result.stdout or result.stderr))


def append_bool(report: dict[str, Any], name: str, ok: bool, detail: str) -> None:
    report["checks"].append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})


def compact(value: str) -> str:
    single = " ".join(value.strip().split())
    return single[:400] if single else "<empty>"


if __name__ == "__main__":
    sys.exit(main())
