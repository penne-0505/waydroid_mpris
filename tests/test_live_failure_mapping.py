from __future__ import annotations

import unittest

from host.waydroid_mpris import protocol
from host.waydroid_mpris.mpris_service import read_live_snapshot_or_empty


class FailingTransport:
    def read_snapshot(self):
        raise RuntimeError("device offline")


class LiveFailureMappingTest(unittest.TestCase):
    def test_adb_read_failure_returns_empty_stopped_snapshot(self) -> None:
        snapshot = read_live_snapshot_or_empty(FailingTransport())
        session = protocol.selected_session(snapshot)

        self.assertEqual(snapshot["reason"], "adb_probe_read_failed")
        self.assertEqual(snapshot["sessionCount"], 0)
        self.assertIsNone(session)
        self.assertEqual(protocol.playback_status(session), "Stopped")
        self.assertEqual(protocol.mpris_metadata(session)["mpris:trackid"], protocol.MPRIS_NO_TRACK)
        self.assertIn("device offline", snapshot["error"])


if __name__ == "__main__":
    unittest.main()
