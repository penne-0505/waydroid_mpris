from __future__ import annotations

import ipaddress
import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any


Runner = Callable[[Sequence[str], float], Any]
Clock = Callable[[], float]


@dataclass(frozen=True)
class AdbDevice:
    serial: str
    state: str
    details: str = ""


@dataclass(frozen=True)
class ConnectionInspection:
    target: str
    state: str
    details: str = ""

    @property
    def ready(self) -> bool:
        return self.state == "device"


class AdbRecoveryError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        target: str | None = None,
        operator_action_required: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.target = target
        self.operator_action_required = operator_action_required

    @property
    def log_key(self) -> str:
        return f"{self.code}:{self.target or '-'}"


def parse_adb_devices(raw: str) -> dict[str, AdbDevice]:
    devices: dict[str, AdbDevice] = {}
    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("List of devices attached") or line.startswith("*"):
            continue
        fields = line.split(maxsplit=2)
        if len(fields) < 2:
            continue
        serial, state = fields[0], fields[1]
        details = fields[2] if len(fields) > 2 else ""
        devices[serial] = AdbDevice(serial=serial, state=state, details=details)
    return devices


def parse_waydroid_target(raw: str, port: int = 5555) -> str:
    values: dict[str, str] = {}
    for raw_line in raw.splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        values[key.strip().lower()] = value.strip()

    session = values.get("session", "")
    container = values.get("container", "")
    if session != "RUNNING" or container != "RUNNING":
        raise AdbRecoveryError(
            "waydroid_not_running",
            f"Waydroid is not fully running (session={session or 'unknown'}, container={container or 'unknown'})",
        )

    raw_ip = values.get("ip address", "")
    if not raw_ip or raw_ip.upper() == "UNKNOWN":
        raise AdbRecoveryError(
            "waydroid_ip_unknown",
            "Waydroid is running but its IP address is unavailable",
        )
    try:
        address = ipaddress.ip_address(raw_ip)
    except ValueError as ex:
        raise AdbRecoveryError(
            "waydroid_ip_invalid",
            f"Waydroid reported an invalid IP address: {raw_ip}",
        ) from ex
    if address.version == 6:
        return f"[{address.compressed}]:{port}"
    return f"{address.compressed}:{port}"


def is_tcp_serial(serial: str) -> bool:
    host = serial
    port = "5555"
    if serial.startswith("["):
        closing = serial.find("]")
        if closing < 0 or closing + 1 >= len(serial) or serial[closing + 1] != ":":
            return False
        host = serial[1:closing]
        port = serial[closing + 2 :]
    elif serial.count(":") == 1:
        host, port = serial.rsplit(":", 1)
    else:
        return False
    try:
        address = ipaddress.ip_address(host)
        parsed_port = int(port)
    except ValueError:
        return False
    return not address.is_unspecified and 1 <= parsed_port <= 65535


def inspection_error(inspection: ConnectionInspection) -> AdbRecoveryError:
    target = inspection.target
    if inspection.state == "unauthorized":
        return AdbRecoveryError(
            "adb_unauthorized",
            f"ADB target {target} is unauthorized; approve the debugging prompt inside Waydroid",
            target=target,
            operator_action_required=True,
        )
    if inspection.state == "offline":
        return AdbRecoveryError(
            "adb_offline",
            f"ADB target {target} is offline",
            target=target,
        )
    if inspection.state == "missing":
        return AdbRecoveryError(
            "adb_missing",
            f"ADB target {target} is not listed",
            target=target,
        )
    return AdbRecoveryError(
        "adb_state_unsupported",
        f"ADB target {target} has unsupported state {inspection.state}",
        target=target,
        operator_action_required=True,
    )


class AdbRecoveryManager:
    def __init__(
        self,
        *,
        adb_path: str = "adb",
        waydroid_path: str = "waydroid",
        device: str | None = None,
        timeout_seconds: float = 5.0,
        retry_initial_seconds: float = 1.0,
        retry_max_seconds: float = 30.0,
        runner: Runner | None = None,
        clock: Clock | None = None,
    ) -> None:
        if retry_initial_seconds <= 0:
            raise ValueError("retry_initial_seconds must be positive")
        if retry_max_seconds < retry_initial_seconds:
            raise ValueError("retry_max_seconds must be at least retry_initial_seconds")
        self.adb_path = adb_path
        self.waydroid_path = waydroid_path
        self.explicit_device = device
        self.timeout_seconds = timeout_seconds
        self.retry_initial_seconds = retry_initial_seconds
        self.retry_max_seconds = retry_max_seconds
        self._runner = runner or self._default_runner
        self._clock = clock or time.monotonic
        self._healthy_target: str | None = None
        self._next_attempt_at = 0.0
        self._retry_delay = retry_initial_seconds
        self._last_error: AdbRecoveryError | None = None

    def discover_target(self) -> str:
        if self.explicit_device:
            return self.explicit_device
        result = self._run([self.waydroid_path, "status"])
        if result.returncode != 0:
            detail = compact_process_output(result)
            raise AdbRecoveryError(
                "waydroid_status_failed",
                f"waydroid status failed: {detail}",
            )
        return parse_waydroid_target(result.stdout)

    def inspect(self) -> ConnectionInspection:
        target = self.discover_target()
        result = self._run([self.adb_path, "devices", "-l"])
        if result.returncode != 0:
            detail = compact_process_output(result)
            raise AdbRecoveryError(
                "adb_devices_failed",
                f"adb devices failed: {detail}",
                target=target,
            )
        device = parse_adb_devices(result.stdout).get(target)
        if device is None:
            return ConnectionInspection(target=target, state="missing")
        return ConnectionInspection(target=target, state=device.state, details=device.details)

    def ensure_connected(self) -> str:
        if self._healthy_target is not None:
            return self._healthy_target

        now = self._clock()
        if self._last_error is not None and now < self._next_attempt_at:
            raise self._last_error

        try:
            inspection = self.inspect()
        except AdbRecoveryError as ex:
            raise self._schedule_failure(ex) from ex

        if inspection.ready:
            self._mark_target_ready(inspection.target)
            return inspection.target

        unavailable = inspection_error(inspection)
        if unavailable.operator_action_required:
            raise self._schedule_failure(unavailable)
        if not is_tcp_serial(inspection.target):
            unsupported = AdbRecoveryError(
                "adb_target_not_connectable",
                f"ADB target {inspection.target} is not a TCP serial; reconnect it outside the bridge",
                target=inspection.target,
                operator_action_required=True,
            )
            raise self._schedule_failure(unsupported)

        # intent why-not: INV-006 (Core/waydroid-adb-auto-recovery) — keep recovery target-scoped; never reset the host ADB server or control Waydroid lifecycle here.
        connect = self._run([self.adb_path, "connect", inspection.target])
        try:
            after_connect = self.inspect()
        except AdbRecoveryError as ex:
            raise self._schedule_failure(ex) from ex
        if after_connect.ready:
            self._mark_target_ready(after_connect.target)
            return after_connect.target

        after_error = inspection_error(after_connect)
        if after_error.operator_action_required:
            raise self._schedule_failure(after_error)
        detail = compact_process_output(connect)
        connect_error = AdbRecoveryError(
            "adb_connect_failed",
            f"ADB target {inspection.target} did not become ready after adb connect: {detail}",
            target=inspection.target,
        )
        raise self._schedule_failure(connect_error)

    def record_success(self, target: str) -> None:
        self._healthy_target = target
        self._last_error = None
        self._next_attempt_at = 0.0
        self._retry_delay = self.retry_initial_seconds

    def _mark_target_ready(self, target: str) -> None:
        self._healthy_target = target
        self._last_error = None
        self._next_attempt_at = 0.0

    def record_transport_failure(
        self,
        error: BaseException,
        target: str | None = None,
    ) -> AdbRecoveryError:
        failed_target = target or self._healthy_target
        self._healthy_target = None
        return self._schedule_failure(
            AdbRecoveryError(
                "adb_transport_failed",
                str(error),
                target=failed_target,
            )
        )

    def _schedule_failure(self, error: AdbRecoveryError) -> AdbRecoveryError:
        self._healthy_target = None
        self._last_error = error
        self._next_attempt_at = self._clock() + self._retry_delay
        self._retry_delay = min(self.retry_max_seconds, self._retry_delay * 2)
        return error

    def _run(self, command: Sequence[str]) -> Any:
        try:
            return self._runner(command, self.timeout_seconds)
        except (OSError, subprocess.TimeoutExpired) as ex:
            executable = command[0] if command else "command"
            raise AdbRecoveryError(
                "recovery_command_failed",
                f"{executable} could not be executed: {ex}",
            ) from ex

    @staticmethod
    def _default_runner(command: Sequence[str], timeout_seconds: float) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(command),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
        )


def compact_process_output(result: Any) -> str:
    value = (getattr(result, "stderr", "") or getattr(result, "stdout", "") or "").strip()
    return " ".join(value.split()) or f"exit {getattr(result, 'returncode', 'unknown')}"


class FailureLogReporter:
    def __init__(
        self,
        logger: Callable[[str], None],
        *,
        reminder_seconds: float = 60.0,
        clock: Clock | None = None,
    ) -> None:
        if reminder_seconds <= 0:
            raise ValueError("reminder_seconds must be positive")
        self._logger = logger
        self._reminder_seconds = reminder_seconds
        self._clock = clock or time.monotonic
        self._active_key: str | None = None
        self._last_logged_at = 0.0
        self._suppressed = 0

    def report_failure(self, error: BaseException) -> None:
        now = self._clock()
        key = getattr(error, "log_key", f"{type(error).__name__}:{error}")
        changed = key != self._active_key
        reminder_due = self._active_key is not None and now - self._last_logged_at >= self._reminder_seconds
        if changed or reminder_due:
            prefix = "unavailable" if changed else "still unavailable"
            suppressed = f"; suppressed {self._suppressed} repeats" if self._suppressed else ""
            self._logger(f"waydroid-mpris: {prefix}: {error}{suppressed}")
            self._active_key = key
            self._last_logged_at = now
            self._suppressed = 0
            return
        self._suppressed += 1

    def report_recovery(self) -> None:
        if self._active_key is None:
            return
        suppressed = f" after suppressing {self._suppressed} repeats" if self._suppressed else ""
        self._logger(f"waydroid-mpris: live probe recovered{suppressed}")
        self._active_key = None
        self._last_logged_at = 0.0
        self._suppressed = 0
