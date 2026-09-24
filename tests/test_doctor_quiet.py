from __future__ import annotations

import contextlib
import io
import sys
import unittest
from unittest import mock

from scripts.doctor import Check, format_check_line, main, render_quiet_report


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

    def test_all_passed_is_a_single_line_with_the_check_count(self) -> None:
        checks = [Check("a", "PASS", "ok"), Check("b", "PASS", "ok")]

        report = render_quiet_report(checks)

        # The wording is free; one line, the count, and no problem status are fixed.
        self.assertEqual(len(report.splitlines()), 1)
        self.assertIn("2", report)
        self.assertNotIn("FAIL", report)
        self.assertNotIn("WARN", report)

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

    def test_quiet_and_json_together_are_a_usage_error(self) -> None:
        for argv in (["--quiet", "--json"], ["--json", "--quiet"]):
            with self.subTest(argv=argv):
                with self.assertRaises(SystemExit) as raised:
                    run_main(argv, which_result=None)
                self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
