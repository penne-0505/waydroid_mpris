from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Sequence
from typing import Any

from .adb_recovery import AdbRecoveryManager


DEFAULT_PROBE_PATH = "/sdcard/Android/data/dev.penne.waydroidmpris.probe/files/latest_probe.json"
DEFAULT_COMMAND_RESULT_PATH = "/sdcard/Android/data/dev.penne.waydroidmpris.probe/files/latest_command_result.json"
COMMAND_ACTION = "dev.penne.waydroidmpris.probe.COMMAND"
COMMAND_RECEIVER = "dev.penne.waydroidmpris.probe/.BridgeCommandReceiver"


class AdbTransportError(RuntimeError):
    pass


Runner = Callable[[Sequence[str], float], Any]


class AdbProbeTransport:
    def __init__(
        self,
        adb_path: str = "adb",
        device: str | None = None,
        probe_path: str = DEFAULT_PROBE_PATH,
        command_result_path: str = DEFAULT_COMMAND_RESULT_PATH,
        timeout_seconds: float = 5.0,
        runner: Runner | None = None,
        recovery_manager: AdbRecoveryManager | None = None,
    ) -> None:
        self.adb_path = adb_path
        self.device = device
        self.probe_path = probe_path
        self.command_result_path = command_result_path
        self.timeout_seconds = timeout_seconds
        self._runner = runner or self._default_runner
        self.recovery_manager = recovery_manager

    def read_snapshot(self) -> dict[str, Any]:
        stdout = self._run(["shell", "cat", self.probe_path])
        data = json.loads(stdout)
        if not isinstance(data, dict):
            raise AdbTransportError("probe snapshot root must be an object")
        return data

    def send_command(self, command: str, position_ms: int | None = None) -> str:
        args = [
            "shell",
            "am",
            "broadcast",
            "-a",
            COMMAND_ACTION,
            "-n",
            COMMAND_RECEIVER,
            "--es",
            "command",
            command,
        ]
        if position_ms is not None:
            args.extend(["--el", "positionMs", str(position_ms)])
        broadcast_stdout = self._run(args)
        result = self.read_command_result()
        if result.get("ok") is not True:
            error = result.get("error") or "command rejected"
            raise AdbTransportError(str(error))
        return broadcast_stdout

    def read_command_result(self) -> dict[str, Any]:
        stdout = self._run(["shell", "cat", self.command_result_path])
        data = json.loads(stdout)
        if not isinstance(data, dict):
            raise AdbTransportError("command result root must be an object")
        return data

    def read_file(self, android_path: str) -> bytes:
        target = self._resolve_target()
        command = [self.adb_path]
        if target:
            command.extend(["-s", target])
        command.extend(["exec-out", "cat", android_path])
        try:
            result = subprocess.run(
                command,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as ex:
            error = AdbTransportError(str(ex))
            raise self._record_failure(error, target) from ex
        if result.returncode != 0:
            message = (result.stderr or result.stdout or b"").decode("utf-8", errors="replace").strip()
            error = AdbTransportError(message or f"adb exited with {result.returncode}")
            raise self._record_failure(error, target)
        self._record_success(target)
        return result.stdout

    def _run(self, args: Sequence[str]) -> str:
        target = self._resolve_target()
        command = [self.adb_path]
        if target:
            command.extend(["-s", target])
        command.extend(args)
        try:
            result = self._runner(command, self.timeout_seconds)
        except (OSError, subprocess.TimeoutExpired) as ex:
            error = AdbTransportError(str(ex))
            raise self._record_failure(error, target) from ex
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "").strip()
            error = AdbTransportError(message or f"adb exited with {result.returncode}")
            raise self._record_failure(error, target)
        self._record_success(target)
        return result.stdout

    def _resolve_target(self) -> str | None:
        if self.recovery_manager is not None:
            return self.recovery_manager.ensure_connected()
        return self.device

    def _record_failure(self, error: BaseException, target: str | None) -> BaseException:
        if self.recovery_manager is not None:
            return self.recovery_manager.record_transport_failure(error, target)
        return error

    def _record_success(self, target: str | None) -> None:
        if self.recovery_manager is not None and target is not None:
            self.recovery_manager.record_success(target)

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
