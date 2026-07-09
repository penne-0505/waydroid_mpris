from __future__ import annotations

import copy
from pathlib import Path
import unittest

from host.waydroid_mpris import protocol
from host.waydroid_mpris.position import PositionProjector


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/probe/apple-music-playing.sample.json"


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class PositionProjectionTest(unittest.TestCase):
    def setUp(self) -> None:
        snapshot = protocol.load_snapshot(FIXTURE)
        session = protocol.selected_session(snapshot)
        self.assertIsNotNone(session)
        self.session = copy.deepcopy(session)
        self.clock = FakeClock()
        self.projector = PositionProjector(clock=self.clock)

    def test_playing_position_advances_between_identical_snapshots(self) -> None:
        self.projector.update(self.session)
        initial = self.projector.position_us()

        self.clock.advance(2.0)
        self.projector.update(copy.deepcopy(self.session))

        self.assertEqual(initial, 119_099_000)
        self.assertEqual(self.projector.position_us(), 121_099_000)

    def test_position_is_clamped_to_track_duration(self) -> None:
        self.session["playbackState"]["positionMs"] = 150_500
        self.projector.update(self.session)

        self.clock.advance(3.0)

        self.assertEqual(self.projector.position_us(), 151_000_000)

    def test_pause_keeps_projected_position_when_android_raw_position_is_stale(self) -> None:
        self.projector.update(self.session)
        self.clock.advance(5.0)

        paused = copy.deepcopy(self.session)
        paused["playbackState"]["state"] = "paused"
        paused["playbackState"]["positionMs"] = 119_099
        self.projector.update(paused)

        held = self.projector.position_us()
        self.clock.advance(2.0)

        self.assertEqual(held, 124_099_000)
        self.assertEqual(self.projector.position_us(), held)

    def test_missing_session_resets_position(self) -> None:
        self.projector.update(self.session)
        self.clock.advance(1.0)

        self.projector.update(None)

        self.assertEqual(self.projector.position_us(), 0)


if __name__ == "__main__":
    unittest.main()
