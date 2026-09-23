from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from unittest import mock

from scripts.doctor import Check, main, render_json_report


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


def parse_human_readable(raw: str) -> list[tuple[str, str, str]]:
    parsed = []
    for line in raw.splitlines():
        status, rest = line[:4].strip(), line[5:]
        name, detail = rest.split(": ", 1)
        parsed.append((name, status, detail))
    return parsed


class RenderJsonReportTest(unittest.TestCase):
    def test_report_has_ok_and_checks_keys_only(self) -> None:
        report = json.loads(render_json_report([Check("adb target", "PASS", "1.2.3.4 is device")]))

        self.assertEqual(set(report), {"ok", "checks"})
        self.assertEqual(
            report["checks"],
            [{"name": "adb target", "status": "PASS", "detail": "1.2.3.4 is device"}],
        )

    def test_ok_is_true_without_fail_even_with_warn(self) -> None:
        report = json.loads(
            render_json_report([Check("a", "PASS", "x"), Check("b", "WARN", "y")])
        )

        self.assertTrue(report["ok"])

    def test_ok_is_false_with_fail(self) -> None:
        report = json.loads(
            render_json_report([Check("a", "WARN", "x"), Check("b", "FAIL", "y")])
        )

        self.assertFalse(report["ok"])

    def test_report_ends_with_newline(self) -> None:
        self.assertTrue(render_json_report([Check("a", "PASS", "x")]).endswith("\n"))


class MainJsonTest(unittest.TestCase):
    def test_json_stdout_is_single_object_without_human_readable_lines(self) -> None:
        # No executable resolves, so every command check fails and no external command runs.
        code, stdout, _stderr = run_main(["--json"], which_result=None)

        report = json.loads(stdout)
        self.assertEqual(code, 1)
        self.assertFalse(report["ok"])
        self.assertTrue(report["checks"])
        self.assertNotIn("PASS ", stdout)
        self.assertEqual(set(report["checks"][0]), {"name", "status", "detail"})

    def test_json_checks_mirror_human_readable_output(self) -> None:
        human_code, human_stdout, _ = run_main([], which_result=None)
        json_code, json_stdout, _ = run_main(["--json"], which_result=None)

        report = json.loads(json_stdout)
        mirrored = [(check["name"], check["status"], check["detail"]) for check in report["checks"]]
        self.assertEqual(mirrored, parse_human_readable(human_stdout))
        self.assertEqual(json_code, human_code)


if __name__ == "__main__":
    unittest.main()
