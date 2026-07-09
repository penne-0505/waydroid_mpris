from pathlib import Path
import unittest

from host.waydroid_mpris import protocol


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/probe/apple-music-playing.sample.json"


class ProtocolMappingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = protocol.load_snapshot(FIXTURE)
        self.session = protocol.selected_session(self.snapshot)

    def test_selected_session_is_apple_music(self) -> None:
        self.assertIsNotNone(self.session)
        self.assertEqual(self.session["packageName"], "com.apple.android.music")

    def test_playback_status_maps_to_mpris(self) -> None:
        self.assertEqual(protocol.playback_status(self.session), "Playing")
        self.assertEqual(protocol.playback_speed(self.session), 1.0)
        self.assertEqual(protocol.duration_us(self.session), 151000000)
        self.assertTrue(protocol.can_pause(self.session))
        self.assertTrue(protocol.can_go_next(self.session))
        self.assertTrue(protocol.can_go_previous(self.session))
        self.assertTrue(protocol.can_seek(self.session))

    def test_metadata_maps_to_mpris_without_host_unreadable_art_url(self) -> None:
        metadata = protocol.mpris_metadata(self.session)
        self.assertEqual(metadata["xesam:title"], "Example Track")
        self.assertEqual(metadata["xesam:artist"], ["Example Artist"])
        self.assertEqual(metadata["xesam:album"], "Example Album")
        self.assertEqual(metadata["mpris:length"], 151000000)
        self.assertIn("mpris:trackid", metadata)
        self.assertNotIn("mpris:artUrl", metadata)

    def test_metadata_uses_host_readable_art_url_when_supplied(self) -> None:
        metadata = protocol.mpris_metadata(self.session, "file:///tmp/example.png")

        self.assertEqual(metadata["mpris:artUrl"], "file:///tmp/example.png")

    def test_missing_session_clears_state(self) -> None:
        self.assertEqual(protocol.playback_status(None), "Stopped")
        self.assertEqual(protocol.position_us(None), 0)
        self.assertEqual(protocol.mpris_metadata(None)["mpris:trackid"], protocol.MPRIS_NO_TRACK)


if __name__ == "__main__":
    unittest.main()
