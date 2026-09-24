from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

from scripts.doctor import (
    DEFAULT_PROBE_PATH,
    LISTENER_COMPONENT,
    PACKAGE_NAME,
    Check,
    format_check_line,
    main,
    render_quiet_report,
)


def run_main(argv: list[str], which_result: str | None = None) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with mock.patch.object(sys, "argv", ["doctor.py", *argv]), mock.patch(
        "scripts.doctor.shutil.which", return_value=which_result
    ), mock.patch(
        "scripts.doctor.subprocess.run",
        side_effect=AssertionError("the unit test must not run external commands"),
    ), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main()
    return code, out.getvalue(), err.getvalue()


PROBE_SNAPSHOT = json.dumps(
    {
        "selectedAppleMusicSession": {
            "metadata": {"title": "t", "artist": "a", "artworkFile": {"present": True}},
            "playbackState": {"state": "paused"},
        }
    }
)


def completed(command: list[str], stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, 0, stdout, "")


def fake_command_result(command: list[str], timeout: float = 5.0) -> subprocess.CompletedProcess[str]:
    """Answer the doctor's commands so that one WARN is the only non-PASS check."""
    if command == ["waydroid", "status"]:
        return completed(command, "Session: RUNNING\nContainer: RUNNING\n")
    if command == ["playerctl", "--list-all"]:
        return completed(command, "")
    if command[-1] == PACKAGE_NAME:
        return completed(command, f"package:{PACKAGE_NAME}\n")
    if command[-1] == "enabled_notification_listeners":
        return completed(command, f"{LISTENER_COMPONENT}\n")
    if command[-2:] == ["cat", DEFAULT_PROBE_PATH]:
        return completed(command, PROBE_SNAPSHOT)
    raise AssertionError(f"unexpected command: {command}")


class RenderQuietReportTest(unittest.TestCase):
    def test_only_fail_and_warn_checks_are_rendered(self) -> None:
        checks = [
            Check("a", "PASS", "ok"),
            Check("b", "WARN", "degraded"),
            Check("c", "FAIL", "broken"),
        ]

        report = render_quiet_report(checks)

        self.assertEqual(report, "WARN b: degraded\nFAIL c: broken\n")
        self.assertNotIn("PASS ", report)

    def test_all_passed_is_a_single_line_that_starts_with_ok_and_carries_the_count(self) -> None:
        checks = [Check("a", "PASS", "ok"), Check("b", "PASS", "ok")]

        report = render_quiet_report(checks)

        # Only the fixed shape is asserted: one line, a leading OK, and the full count.
        lines = report.splitlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("OK"))
        self.assertIn(str(len(checks)), lines[0])

    def test_warn_suppresses_the_all_passed_line(self) -> None:
        report = render_quiet_report([Check("a", "PASS", "ok"), Check("b", "WARN", "degraded")])

        self.assertEqual(report, "WARN b: degraded\n")

    def test_rendered_lines_match_the_human_readable_format(self) -> None:
        check = Check("adb target", "FAIL", "1.2.3.4 is missing")

        self.assertEqual(render_quiet_report([check]), f"{format_check_line(check)}\n")


class MainQuietTest(unittest.TestCase):
    def test_quiet_stdout_is_the_fail_lines_of_the_human_readable_output(self) -> None:
        # No executable resolves, so every command check fails and no external command runs.
        human_code, human_stdout, _ = run_main([], which_result=None)
        quiet_code, quiet_stdout, _ = run_main(["--quiet"], which_result=None)

        human_lines = human_stdout.splitlines()
        quiet_lines = quiet_stdout.splitlines()
        self.assertEqual(quiet_code, human_code)
        self.assertEqual(quiet_code, 1)
        self.assertTrue(quiet_lines)
        self.assertNotIn("PASS ", quiet_stdout)
        self.assertEqual(quiet_lines, [line for line in human_lines if line.startswith("FAIL")])

    def test_quiet_exit_code_is_one_only_from_failures(self) -> None:
        quiet_code, _stdout, _ = run_main(["--quiet"], which_result=None)

        self.assertEqual(quiet_code, 1)

    def test_quiet_exit_code_is_zero_when_only_a_warn_is_present(self) -> None:
        # Every command is answered by a stub and the ADB manager is faked, so the
        # single WARN is the "host MPRIS player" check; no external command runs.
        out = io.StringIO()
        inspection = SimpleNamespace(target="192.168.240.112:5555", state="device", ready=True)
        with mock.patch.object(sys, "argv", ["doctor.py", "--quiet"]), mock.patch(
            "scripts.doctor.shutil.which", return_value="/usr/bin/stub"
        ), mock.patch(
            "scripts.doctor.run", side_effect=fake_command_result
        ), mock.patch(
            "scripts.doctor.AdbRecoveryManager"
        ) as manager, mock.patch(
            "scripts.doctor.subprocess.run",
            side_effect=AssertionError("the unit test must not run external commands"),
        ), contextlib.redirect_stdout(out):
            manager.return_value.inspect.return_value = inspection
            code = main()

        self.assertEqual(code, 0)
        self.assertEqual(
            out.getvalue(), "WARN host MPRIS player: host daemon is not currently running\n"
        )
        self.assertNotIn("FAIL", out.getvalue())

    def test_quiet_and_json_together_are_a_usage_error(self) -> None:
        for argv in (["--quiet", "--json"], ["--json", "--quiet"]):
            with self.subTest(argv=argv):
                with self.assertRaises(SystemExit) as raised:
                    run_main(argv, which_result=None)
                self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
