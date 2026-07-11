from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AndroidSdkDiscoveryTest(unittest.TestCase):
    def make_sdk(self, root: Path, platform: str = "android-36", tools: str = "36.0.0") -> None:
        (root / "platforms" / platform).mkdir(parents=True)
        (root / "platforms" / platform / "android.jar").touch()
        tool_dir = root / "build-tools" / tools
        tool_dir.mkdir(parents=True)
        for name in ("aapt2", "d8", "zipalign", "apksigner"):
            (tool_dir / name).touch()

    def resolve(self, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        command = (
            "source scripts/android-sdk-env.sh; "
            "resolve_android_sdk || exit $?; "
            "printf '%s|%s|%s' \"$SDK_ROOT\" \"$PLATFORM_NAME\" \"$BUILD_TOOLS_NAME\""
        )
        return subprocess.run(
            ["bash", "-c", command],
            cwd=ROOT,
            env={**os.environ, **env},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_ac002_inv001_inv002_explicit_sdk_and_versions_win(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            sdk = Path(temp) / "sdk"
            self.make_sdk(sdk, "android-35", "35.0.1")
            self.make_sdk(sdk, "android-36", "36.0.0")
            result = self.resolve(
                {
                    "ANDROID_HOME": str(sdk),
                    "ANDROID_SDK_ROOT": "/must/not/win",
                    "ANDROID_PLATFORM": "android-35",
                    "ANDROID_BUILD_TOOLS": "35.0.1",
                }
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, f"{sdk}|android-35|35.0.1")

    def test_ac002_latest_installed_versions_are_selected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            sdk = Path(temp) / "sdk"
            self.make_sdk(sdk, "android-35", "35.0.1")
            self.make_sdk(sdk, "android-36", "36.0.0")
            result = self.resolve(
                {
                    "ANDROID_HOME": str(sdk),
                    "ANDROID_SDK_ROOT": "",
                    "ANDROID_PLATFORM": "",
                    "ANDROID_BUILD_TOOLS": "",
                }
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, f"{sdk}|android-36|36.0.0")
            self.assertIn("Android Build-Tools: 36.0.0", result.stderr)

    def test_ac002_missing_explicit_sdk_has_actionable_error(self) -> None:
        result = self.resolve({"ANDROID_HOME": "/missing/sdk", "ANDROID_SDK_ROOT": ""})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Set ANDROID_HOME or ANDROID_SDK_ROOT", result.stderr)


class AndroidInstallScriptTest(unittest.TestCase):
    def test_ac004_inv004_signature_mismatch_is_non_destructive(self) -> None:
        script = (ROOT / "scripts/install-android-probe.sh").read_text()
        self.assertIn("INSTALL_FAILED_UPDATE_INCOMPATIBLE", script)
        self.assertIn("Remove dev.penne.waydroidmpris.probe manually", script)
        self.assertNotIn("adb uninstall", script)
        self.assertNotIn("$ADB uninstall", script)

    def test_ac003_helpers_scope_adb_commands_to_resolved_target(self) -> None:
        install = (ROOT / "scripts/install-android-probe.sh").read_text()
        settings = (ROOT / "scripts/open-android-notification-listener-settings.sh").read_text()
        self.assertIn('-s "$TARGET" install', install)
        self.assertIn('-s "$TARGET" shell am start', install)
        self.assertIn('-s "$TARGET" shell am start', settings)


if __name__ == "__main__":
    unittest.main()
