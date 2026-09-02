from __future__ import annotations

import copy
from pathlib import Path
import unittest

from host.waydroid_mpris import protocol
from host.waydroid_mpris.mpris_service import WaydroidMprisObject
from host.waydroid_mpris.position import PositionProjector


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/probe/apple-music-playing.sample.json"
LEAD_MS = 400


class FrozenClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def build_bridge(snapshot: dict, lead_ms: int) -> tuple[WaydroidMprisObject, list[tuple[str, int | None]]]:
    dispatched: list[tuple[str, int | None]] = []
    bridge = object.__new__(WaydroidMprisObject)
    bridge.snapshot = snapshot
    bridge.session = protocol.selected_session(snapshot)
    bridge.command_handler = lambda command, position_ms=None: dispatched.append((command, position_ms))
    bridge.artwork_provider = None
    bridge.art_url = None
    bridge.position_projector = PositionProjector(clock=FrozenClock(), lead_us=lead_ms * 1000)
    bridge.position_projector.update(bridge.session)
    return bridge, dispatched


class MprisPositionLeadTest(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = protocol.load_snapshot(FIXTURE)

    def test_published_position_carries_lead(self) -> None:
        # Covers AC-002
        leading, _ = build_bridge(copy.deepcopy(self.snapshot), LEAD_MS)
        plain, _ = build_bridge(copy.deepcopy(self.snapshot), 0)

        difference = int(leading.Get(
            "org.mpris.MediaPlayer2.Player", "Position"
        )) - int(plain.Get("org.mpris.MediaPlayer2.Player", "Position"))

        self.assertEqual(difference, LEAD_MS * 1000)

    def test_seek_base_excludes_lead(self) -> None:
        # Covers AC-003 / INV-008
        leading, leading_dispatched = build_bridge(copy.deepcopy(self.snapshot), LEAD_MS)
        plain, plain_dispatched = build_bridge(copy.deepcopy(self.snapshot), 0)

        leading.Seek(5_000_000)
        plain.Seek(5_000_000)

        self.assertEqual(leading_dispatched, plain_dispatched)

    def test_set_position_round_trip_cancels_lead(self) -> None:
        # Covers AC-003 / INV-008
        bridge, dispatched = build_bridge(copy.deepcopy(self.snapshot), LEAD_MS)
        track_id = protocol.mpris_metadata(bridge.session)["mpris:trackid"]
        published = int(bridge.Get("org.mpris.MediaPlayer2.Player", "Position"))

        bridge.SetPosition(track_id, published)

        self.assertEqual(
            dispatched,
            [("seekTo", int(bridge.position_projector.position_us() / 1000))],
        )


if __name__ == "__main__":
    unittest.main()
