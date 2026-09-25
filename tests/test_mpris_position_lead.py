from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock

import dbus

from host.waydroid_mpris import mpris_service, protocol
from host.waydroid_mpris.mpris_service import WaydroidMprisObject
from host.waydroid_mpris.position import PositionProjector


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/probe/apple-music-playing.sample.json"
LIVE_SCRIPT = ROOT / "scripts/run-host-mpris-live.py"
PLAYER = "org.mpris.MediaPlayer2.Player"
LEAD_MS = 400


class FrozenClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def load_live_script():
    spec = importlib.util.spec_from_file_location("run_host_mpris_live", LIVE_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_bridge(snapshot: dict, lead_ms: int):
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
        leading, _ = build_bridge(copy.deepcopy(self.snapshot), LEAD_MS)
        plain, _ = build_bridge(copy.deepcopy(self.snapshot), 0)

        difference = int(leading.Get(PLAYER, "Position")) - int(plain.Get(PLAYER, "Position"))

        self.assertEqual(difference, LEAD_MS * 1000)

    def test_seek_dispatch_ignores_lead(self) -> None:
        leading, leading_dispatched = build_bridge(copy.deepcopy(self.snapshot), LEAD_MS)
        plain, plain_dispatched = build_bridge(copy.deepcopy(self.snapshot), 0)

        leading.Seek(5_000_000)
        plain.Seek(5_000_000)

        self.assertTrue(leading_dispatched)
        self.assertEqual(leading_dispatched, plain_dispatched)

    def test_set_position_round_trip_lands_on_real_position(self) -> None:
        bridge, dispatched = build_bridge(copy.deepcopy(self.snapshot), LEAD_MS)
        track_id = protocol.mpris_metadata(bridge.session)["mpris:trackid"]
        published = int(bridge.Get(PLAYER, "Position"))

        bridge.SetPosition(track_id, published)

        self.assertEqual(
            dispatched,
            [("seekTo", int(bridge.position_projector.position_us() / 1000))],
        )

    def test_set_position_forwards_absolute_seek_offset_by_lead(self) -> None:
        bridge, dispatched = build_bridge(copy.deepcopy(self.snapshot), LEAD_MS)
        track_id = protocol.mpris_metadata(bridge.session)["mpris:trackid"]
        real_us = bridge.position_projector.position_us()
        requested_us = real_us + 5_000_000

        bridge.SetPosition(track_id, requested_us)

        self.assertEqual(dispatched, [("seekTo", int((requested_us - LEAD_MS * 1000) / 1000))])
        self.assertGreater(dispatched[0][1], int(real_us / 1000))

    def test_clamped_public_write_back_at_track_start_stays_at_zero(self) -> None:
        paused = copy.deepcopy(self.snapshot)
        session = paused["selectedAppleMusicSession"]
        session["playbackState"]["state"] = "paused"
        session["playbackState"]["positionMs"] = 100
        bridge, dispatched = build_bridge(paused, -LEAD_MS)
        track_id = protocol.mpris_metadata(bridge.session)["mpris:trackid"]
        published = int(bridge.Get(PLAYER, "Position"))

        bridge.SetPosition(track_id, published)

        self.assertEqual(published, 0)
        self.assertEqual(dispatched, [("seekTo", 0)])

    def test_clamped_public_write_back_at_track_end_does_not_seek_forward(self) -> None:
        near_end = copy.deepcopy(self.snapshot)
        session = near_end["selectedAppleMusicSession"]
        duration_ms = session["metadata"]["durationMs"]
        session["playbackState"]["positionMs"] = duration_ms - 100
        bridge, dispatched = build_bridge(near_end, LEAD_MS)
        track_id = protocol.mpris_metadata(bridge.session)["mpris:trackid"]
        published = int(bridge.Get(PLAYER, "Position"))
        real_ms = int(bridge.position_projector.position_us() / 1000)

        bridge.SetPosition(track_id, published)

        self.assertEqual(published, duration_ms * 1000)
        self.assertLessEqual(dispatched[0][1], real_ms)
        self.assertEqual(dispatched, [("seekTo", duration_ms - LEAD_MS)])

    def test_main_forwards_position_lead_to_serve_live(self) -> None:
        module = load_live_script()

        with mock.patch.object(module, "serve_live") as serve_live_mock:
            with mock.patch.object(sys, "argv", ["run-host-mpris-live.py", "--position-lead-ms", "485"]):
                module.main()

        self.assertEqual(serve_live_mock.call_args.kwargs["position_lead_ms"], 485)

    def test_serve_live_forwards_position_lead_to_bridge(self) -> None:
        snapshot = protocol.load_snapshot(FIXTURE)

        with (
            mock.patch.object(mpris_service.dbus.mainloop.glib, "DBusGMainLoop"),
            mock.patch.object(mpris_service.dbus, "SessionBus"),
            mock.patch.object(mpris_service, "AdbRecoveryManager"),
            mock.patch.object(mpris_service, "AdbProbeTransport"),
            mock.patch.object(mpris_service, "AdbArtworkCache"),
            mock.patch.object(mpris_service, "read_live_snapshot_or_empty", return_value=snapshot),
            mock.patch.object(mpris_service, "WaydroidMprisObject") as bridge_mock,
            mock.patch.object(mpris_service.GLib, "timeout_add"),
            mock.patch.object(mpris_service, "run_mainloop"),
        ):
            mpris_service.serve_live(position_lead_ms=485)

        self.assertEqual(bridge_mock.call_args.kwargs["position_lead_ms"], 485)

    def test_constructor_scales_position_lead_from_ms_to_us(self) -> None:
        snapshot = protocol.load_snapshot(FIXTURE)

        with (
            mock.patch.object(dbus.service, "BusName"),
            mock.patch.object(dbus.service.Object, "__init__", lambda self, *args, **kwargs: None),
            mock.patch("time.monotonic", return_value=1000.0),
        ):
            leading = WaydroidMprisObject(mock.Mock(), copy.deepcopy(snapshot), position_lead_ms=485)
            plain = WaydroidMprisObject(mock.Mock(), copy.deepcopy(snapshot), position_lead_ms=0)

        difference = int(leading.Get(PLAYER, "Position")) - int(plain.Get(PLAYER, "Position"))

        self.assertEqual(difference, 485_000)


if __name__ == "__main__":
    unittest.main()
