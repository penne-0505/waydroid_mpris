from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from host.waydroid_mpris.adb_transport import AdbProbeTransport, AdbTransportError


class AdbProbeTransportTest(unittest.TestCase):
    def test_read_snapshot_uses_configured_device_and_path(self) -> None:
        calls = []

        def runner(command, timeout):
            calls.append((list(command), timeout))
            return SimpleNamespace(returncode=0, stdout='{"selectedAppleMusicSession": null}', stderr="")

        transport = AdbProbeTransport(
            adb_path="/usr/bin/adb",
            device="waydroid:5555",
            probe_path="/tmp/latest_probe.json",
            timeout_seconds=7.0,
            runner=runner,
        )

        snapshot = transport.read_snapshot()

        self.assertIsNone(snapshot["selectedAppleMusicSession"])
        self.assertEqual(
            calls[0][0],
            ["/usr/bin/adb", "-s", "waydroid:5555", "shell", "cat", "/tmp/latest_probe.json"],
        )
        self.assertEqual(calls[0][1], 7.0)

    def test_send_command_broadcasts_to_companion_receiver(self) -> None:
        calls = []

        def runner(command, timeout):
            calls.append(list(command))
            if any("latest_command_result.json" in item for item in command):
                return SimpleNamespace(returncode=0, stdout='{"ok": true}', stderr="")
            return SimpleNamespace(returncode=0, stdout="Broadcast completed", stderr="")

        transport = AdbProbeTransport(device="waydroid:5555", runner=runner)
        transport.send_command("playPause", position_ms=1234)

        broadcast = calls[0]
        command_result_read = calls[1]
        self.assertEqual(broadcast[:3], ["adb", "-s", "waydroid:5555"])
        self.assertIn("dev.penne.waydroidmpris.probe.COMMAND", broadcast)
        self.assertIn("dev.penne.waydroidmpris.probe/.BridgeCommandReceiver", broadcast)
        self.assertIn("playPause", broadcast)
        self.assertIn("1234", broadcast)
        self.assertTrue(any("latest_command_result.json" in item for item in command_result_read))

    def test_send_command_raises_when_android_rejects_command(self) -> None:
        def runner(command, timeout):
            if any("latest_command_result.json" in item for item in command):
                return SimpleNamespace(
                    returncode=0,
                    stdout='{"ok": false, "error": "apple_music_session_absent"}',
                    stderr="",
                )
            return SimpleNamespace(returncode=0, stdout="Broadcast completed", stderr="")

        transport = AdbProbeTransport(runner=runner)

        with self.assertRaisesRegex(AdbTransportError, "apple_music_session_absent"):
            transport.send_command("playPause")

    def test_nonzero_adb_exit_raises_transport_error(self) -> None:
        def runner(command, timeout):
            return SimpleNamespace(returncode=1, stdout="", stderr="device offline")

        transport = AdbProbeTransport(runner=runner)

        with self.assertRaisesRegex(AdbTransportError, "device offline"):
            transport.read_snapshot()

    @patch("host.waydroid_mpris.adb_transport.subprocess.run")
    def test_inv001_artwork_read_uses_configured_target(self, run) -> None:
        run.return_value = SimpleNamespace(returncode=0, stdout=b"png", stderr=b"")
        transport = AdbProbeTransport(adb_path="/usr/bin/adb", device="192.168.240.112:5555")

        self.assertEqual(transport.read_file("/artwork.png"), b"png")

        command = run.call_args.args[0]
        self.assertEqual(
            command,
            [
                "/usr/bin/adb",
                "-s",
                "192.168.240.112:5555",
                "exec-out",
                "cat",
                "/artwork.png",
            ],
        )


if __name__ == "__main__":
    unittest.main()
