from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from . import protocol


Clock = Callable[[], float]


class PositionProjector:
    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or time.monotonic
        self._track_id: str | None = None
        self._status = "Stopped"
        self._speed = 1.0
        self._duration_us = 0
        self._base_position_us = 0
        self._base_time = self._clock()
        self._last_raw_position_us = 0

    def update(self, session: dict[str, Any] | None) -> None:
        now = self._clock()
        track_id = self._track_id_for(session)
        if track_id is None:
            self._reset(now)
            return

        status = protocol.playback_status(session)
        raw_position_us = protocol.position_us(session)
        speed = protocol.playback_speed(session)
        duration_us = protocol.duration_us(session)
        same_track = track_id == self._track_id
        current_position_us = self.position_us(now)

        if not same_track:
            base_position_us = raw_position_us
        elif status == "Playing":
            if self._status == "Playing" and not self._raw_position_changed(raw_position_us):
                base_position_us = self._base_position_us
                now = self._base_time
            else:
                base_position_us = raw_position_us
        elif self._status == "Playing":
            base_position_us = max(raw_position_us, current_position_us)
        elif self._raw_position_changed(raw_position_us):
            base_position_us = raw_position_us
        else:
            base_position_us = self._base_position_us
            now = self._base_time

        self._track_id = track_id
        self._status = status
        self._speed = speed
        self._duration_us = duration_us
        self._base_position_us = self._clamp(base_position_us)
        self._base_time = now
        self._last_raw_position_us = raw_position_us

    def position_us(self, now: float | None = None) -> int:
        if self._track_id is None:
            return 0
        current_time = self._clock() if now is None else now
        position_us = self._base_position_us
        if self._status == "Playing":
            elapsed_seconds = max(0.0, current_time - self._base_time)
            position_us += int(elapsed_seconds * 1_000_000 * self._speed)
        return self._clamp(position_us)

    def _reset(self, now: float) -> None:
        self._track_id = None
        self._status = "Stopped"
        self._speed = 1.0
        self._duration_us = 0
        self._base_position_us = 0
        self._base_time = now
        self._last_raw_position_us = 0

    def _raw_position_changed(self, raw_position_us: int) -> bool:
        return abs(raw_position_us - self._last_raw_position_us) >= 500_000

    def _clamp(self, position_us: int) -> int:
        position_us = max(0, int(position_us))
        if self._duration_us > 0:
            position_us = min(position_us, self._duration_us)
        return position_us

    @staticmethod
    def _track_id_for(session: dict[str, Any] | None) -> str | None:
        if not protocol.has_current_track(session):
            return None
        track_id = protocol.mpris_metadata(session).get("mpris:trackid")
        return track_id if isinstance(track_id, str) else None
