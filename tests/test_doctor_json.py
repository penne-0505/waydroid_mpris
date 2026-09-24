from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from unittest import mock

from scripts.doctor import Check, has_failure, main, render_json_report


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


class NonAsciiDetailTest(unittest.TestCase):
    non_ascii_detail = "日本語 / アーティスト / Playing"

    def test_report_with_non_ascii_detail_is_ascii_and_parsable(self) -> None:
        report = render_json_report([Check("latest probe", "PASS", self.non_ascii_detail)])

        self.assertTrue(report.isascii())
        parsed = json.loads(report)
        self.assertTrue(parsed["ok"])
        self.assertEqual(parsed["checks"][0]["detail"], self.non_ascii_detail)

    def test_report_with_non_ascii_detail_survives_ascii_stdout(self) -> None:
        report = render_json_report([Check("latest probe", "PASS", self.non_ascii_detail)])

        buffer = io.BytesIO()
        stream = io.TextIOWrapper(buffer, encoding="ascii")
        stream.write(report)
        stream.flush()

        parsed = json.loads(buffer.getvalue().decode("ascii"))
        self.assertTrue(parsed["ok"])
        self.assertEqual(parsed["checks"][0]["detail"], self.non_ascii_detail)


class FailureAggregationTest(unittest.TestCase):
    def test_has_failure_ignores_pass_and_warn(self) -> None:
        self.assertFalse(has_failure([Check("a", "PASS", "x"), Check("b", "WARN", "y")]))
        self.assertTrue(has_failure([Check("a", "WARN", "x"), Check("b", "FAIL", "y")]))

    def test_ok_ignores_warn_in_mixed_column(self) -> None:
        report = json.loads(
            render_json_report(
                [Check("a", "PASS", "x"), Check("b", "WARN", "y"), Check("c", "PASS", "z")]
            )
        )

        self.assertTrue(report["ok"])

    def test_ok_is_false_when_mixed_column_contains_fail(self) -> None:
        report = json.loads(
            render_json_report(
                [Check("a", "PASS", "x"), Check("b", "WARN", "y"), Check("c", "FAIL", "z")]
            )
        )

        self.assertFalse(report["ok"])


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
