from __future__ import annotations

import unittest
from types import SimpleNamespace

from host.waydroid_mpris.adb_recovery import (
    AdbRecoveryError,
    AdbRecoveryManager,
    FailureLogReporter,
    parse_adb_devices,
    parse_waydroid_target,
)
from host.waydroid_mpris.adb_transport import AdbProbeTransport
from scripts.doctor import check_from_inspection, check_mpris_metadata


RUNNING_STATUS = """\
Session:\tRUNNING
Container:\tRUNNING
Vendor type:\tMAINLINE
IP address:\t192.168.240.112
"""


def completed(stdout: str = "", stderr: str = "", returncode: int = 0):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class AdbRecoveryParsingTest(unittest.TestCase):
    def test_ac001_parse_running_waydroid_target(self) -> None:
        self.assertEqual(parse_waydroid_target(RUNNING_STATUS), "192.168.240.112:5555")

    def test_inv003_stopped_waydroid_has_no_target(self) -> None:
        with self.assertRaisesRegex(AdbRecoveryError, "not fully running"):
            parse_waydroid_target("Session:\tSTOPPED\nVendor type:\tMAINLINE\n")

    def test_ac002_parse_device_states(self) -> None:
        devices = parse_adb_devices(
            """\
List of devices attached
192.168.240.112:5555\tunauthorized transport_id:1
emulator-5554\tdevice product:sdk model:Android
192.168.240.113:5555\toffline
"""
        )

        self.assertEqual(devices["192.168.240.112:5555"].state, "unauthorized")
        self.assertEqual(devices["emulator-5554"].state, "device")
        self.assertEqual(devices["192.168.240.113:5555"].state, "offline")


class AdbRecoveryManagerTest(unittest.TestCase):
    def test_ac001_missing_waydroid_connects_and_becomes_ready(self) -> None:
        calls: list[list[str]] = []
        devices_calls = 0

        def runner(command, timeout):
            nonlocal devices_calls
            command = list(command)
            calls.append(command)
            if command == ["waydroid", "status"]:
                return completed(RUNNING_STATUS)
            if command == ["adb", "devices", "-l"]:
                devices_calls += 1
                if devices_calls == 1:
                    return completed("List of devices attached\n")
                return completed("List of devices attached\n192.168.240.112:5555\tdevice\n")
            if command == ["adb", "connect", "192.168.240.112:5555"]:
                return completed("connected to 192.168.240.112:5555\n")
            self.fail(f"unexpected command: {command}")

        manager = AdbRecoveryManager(runner=runner)

        self.assertEqual(manager.ensure_connected(), "192.168.240.112:5555")
        self.assertIn(["adb", "connect", "192.168.240.112:5555"], calls)

    def test_inv001_explicit_device_wins_with_multiple_devices_and_scopes_io(self) -> None:
        calls: list[list[str]] = []

        def runner(command, timeout):
            command = list(command)
            calls.append(command)
            if command == ["adb", "devices", "-l"]:
                return completed(
                    "List of devices attached\n"
                    "192.168.240.112:5555\tdevice\n"
                    "emulator-5554\tdevice\n"
                )
            if command == [
                "adb",
                "-s",
                "192.168.240.112:5555",
                "shell",
                "cat",
                "/probe.json",
            ]:
                return completed('{"selectedAppleMusicSession": null}')
            self.fail(f"unexpected command: {command}")

        manager = AdbRecoveryManager(device="192.168.240.112:5555", runner=runner)
        transport = AdbProbeTransport(
            device="192.168.240.112:5555",
            probe_path="/probe.json",
            runner=runner,
            recovery_manager=manager,
        )

        self.assertIsNone(transport.read_snapshot()["selectedAppleMusicSession"])
        self.assertNotIn(["waydroid", "status"], calls)
        self.assertEqual(calls[-1][1:3], ["-s", "192.168.240.112:5555"])

    def test_ac002_inv002_unauthorized_requires_operator_and_does_not_connect(self) -> None:
        calls: list[list[str]] = []

        def runner(command, timeout):
            command = list(command)
            calls.append(command)
            if command == ["waydroid", "status"]:
                return completed(RUNNING_STATUS)
            if command == ["adb", "devices", "-l"]:
                return completed("List of devices attached\n192.168.240.112:5555\tunauthorized\n")
            self.fail(f"unexpected command: {command}")

        manager = AdbRecoveryManager(runner=runner)

        with self.assertRaises(AdbRecoveryError) as caught:
            manager.ensure_connected()

        self.assertEqual(caught.exception.code, "adb_unauthorized")
        self.assertTrue(caught.exception.operator_action_required)
        self.assertIn("approve the debugging prompt", str(caught.exception))
        self.assertFalse(any(command[1:2] == ["connect"] for command in calls))

    def test_inv003_other_ready_device_is_not_used_when_waydroid_is_stopped(self) -> None:
        calls: list[list[str]] = []

        def runner(command, timeout):
            command = list(command)
            calls.append(command)
            if command == ["waydroid", "status"]:
                return completed("Session:\tSTOPPED\nVendor type:\tMAINLINE\n")
            self.fail(f"unexpected command: {command}")

        manager = AdbRecoveryManager(runner=runner)

        with self.assertRaises(AdbRecoveryError) as caught:
            manager.ensure_connected()

        self.assertEqual(caught.exception.code, "waydroid_not_running")
        self.assertEqual(calls, [["waydroid", "status"]])

    def test_inv002_non_tcp_explicit_target_is_not_auto_connected(self) -> None:
        calls: list[list[str]] = []

        def runner(command, timeout):
            command = list(command)
            calls.append(command)
            if command == ["adb", "devices", "-l"]:
                return completed("List of devices attached\n")
            self.fail(f"unexpected command: {command}")

        manager = AdbRecoveryManager(device="emulator-5554", runner=runner)

        with self.assertRaises(AdbRecoveryError) as caught:
            manager.ensure_connected()

        self.assertEqual(caught.exception.code, "adb_target_not_connectable")
        self.assertTrue(caught.exception.operator_action_required)
        self.assertFalse(any(command[1:2] == ["connect"] for command in calls))

    def test_ac005_inv004_offline_retry_uses_exponential_backoff(self) -> None:
        clock = FakeClock()
        calls: list[list[str]] = []

        def runner(command, timeout):
            command = list(command)
            calls.append(command)
            if command == ["waydroid", "status"]:
                return completed(RUNNING_STATUS)
            if command == ["adb", "devices", "-l"]:
                return completed("List of devices attached\n192.168.240.112:5555\toffline\n")
            if command == ["adb", "connect", "192.168.240.112:5555"]:
                return completed("already connected", returncode=0)
            self.fail(f"unexpected command: {command}")

        manager = AdbRecoveryManager(runner=runner, clock=clock, retry_max_seconds=2.0)

        with self.assertRaises(AdbRecoveryError):
            manager.ensure_connected()
        first_call_count = len(calls)

        with self.assertRaises(AdbRecoveryError):
            manager.ensure_connected()
        self.assertEqual(len(calls), first_call_count)

        clock.advance(1.0)
        with self.assertRaises(AdbRecoveryError):
            manager.ensure_connected()
        second_call_count = len(calls)
        clock.advance(1.9)
        with self.assertRaises(AdbRecoveryError):
            manager.ensure_connected()
        self.assertEqual(len(calls), second_call_count)

        clock.advance(0.1)
        with self.assertRaises(AdbRecoveryError):
            manager.ensure_connected()
        connect_calls = [command for command in calls if command[1:2] == ["connect"]]
        self.assertEqual(len(connect_calls), 3)

        third_call_count = len(calls)
        clock.advance(1.9)
        with self.assertRaises(AdbRecoveryError):
            manager.ensure_connected()
        self.assertEqual(len(calls), third_call_count)
        clock.advance(0.1)
        with self.assertRaises(AdbRecoveryError):
            manager.ensure_connected()
        connect_calls = [command for command in calls if command[1:2] == ["connect"]]
        self.assertEqual(len(connect_calls), 4)

    def test_ac004_ac005_transport_failure_enters_stable_backoff_state(self) -> None:
        clock = FakeClock()
        calls: list[list[str]] = []

        def runner(command, timeout):
            command = list(command)
            calls.append(command)
            if command == ["adb", "devices", "-l"]:
                return completed("List of devices attached\n192.168.240.112:5555\tdevice\n")
            if command == [
                "adb",
                "-s",
                "192.168.240.112:5555",
                "shell",
                "cat",
                "/probe.json",
            ]:
                return completed("", "device offline", returncode=1)
            self.fail(f"unexpected command: {command}")

        manager = AdbRecoveryManager(
            device="192.168.240.112:5555",
            runner=runner,
            clock=clock,
        )
        transport = AdbProbeTransport(
            device="192.168.240.112:5555",
            probe_path="/probe.json",
            runner=runner,
            recovery_manager=manager,
        )

        with self.assertRaises(AdbRecoveryError) as first:
            transport.read_snapshot()
        first_call_count = len(calls)
        with self.assertRaises(AdbRecoveryError) as second:
            transport.read_snapshot()

        self.assertEqual(first.exception.code, "adb_transport_failed")
        self.assertEqual(first.exception.log_key, second.exception.log_key)
        self.assertEqual(len(calls), first_call_count)


class FailureLogReporterTest(unittest.TestCase):
    def test_ac005_inv004_suppresses_repeats_and_reports_recovery(self) -> None:
        clock = FakeClock()
        messages: list[str] = []
        reporter = FailureLogReporter(messages.append, reminder_seconds=60.0, clock=clock)
        error = AdbRecoveryError("adb_missing", "target is missing", target="192.168.240.112:5555")

        reporter.report_failure(error)
        reporter.report_failure(error)
        clock.advance(59.0)
        reporter.report_failure(error)
        self.assertEqual(len(messages), 1)

        clock.advance(1.0)
        reporter.report_failure(error)
        self.assertEqual(len(messages), 2)
        self.assertIn("suppressed 2 repeats", messages[-1])

        reporter.report_recovery()
        reporter.report_recovery()
        self.assertEqual(len(messages), 3)
        self.assertIn("live probe recovered", messages[-1])

    def test_inv004_state_change_logs_immediately(self) -> None:
        clock = FakeClock()
        messages: list[str] = []
        reporter = FailureLogReporter(messages.append, reminder_seconds=60.0, clock=clock)

        reporter.report_failure(AdbRecoveryError("adb_missing", "missing", target="target:5555"))
        reporter.report_failure(
            AdbRecoveryError(
                "adb_unauthorized",
                "unauthorized",
                target="target:5555",
                operator_action_required=True,
            )
        )

        self.assertEqual(len(messages), 2)
        self.assertIn("unauthorized", messages[-1])


class DoctorRecoveryDiagnosisTest(unittest.TestCase):
    def test_ac002_unauthorized_diagnosis_requires_operator_action(self) -> None:
        check = check_from_inspection(
            SimpleNamespace(target="192.168.240.112:5555", state="unauthorized", ready=False)
        )

        self.assertEqual(check.status, "FAIL")
        self.assertIn("operator action required", check.detail)
        self.assertIn("approve the debugging prompt", check.detail)

    def test_ac001_missing_diagnosis_describes_automatic_retry(self) -> None:
        check = check_from_inspection(
            SimpleNamespace(target="192.168.240.112:5555", state="missing", ready=False)
        )

        self.assertEqual(check.status, "FAIL")
        self.assertIn("retry adb connect with backoff", check.detail)

    def test_ac004_stopped_player_accepts_empty_metadata(self) -> None:
        status = completed("Stopped\n")
        metadata = completed("", "No player could handle this command\n", returncode=1)

        check = check_mpris_metadata(status, metadata)

        self.assertEqual(check.status, "PASS")
        self.assertEqual(check.detail, "empty while Stopped")


if __name__ == "__main__":
    unittest.main()
