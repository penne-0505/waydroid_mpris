from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


MPRIS_NO_TRACK = "/org/mpris/MediaPlayer2/TrackList/NoTrack"


def empty_snapshot(reason: str, error: str | None = None) -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "schema": "dev.penne.waydroid_mpris.probe.v0",
        "reason": reason,
        "targetPackage": "com.apple.android.music",
        "notificationListenerEnabled": False,
        "sessionCount": 0,
        "sessions": [],
        "selectedAppleMusicSession": None,
    }
    if error:
        snapshot["error"] = error
    return snapshot


def load_snapshot(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("snapshot root must be an object")
    return data


def selected_session(snapshot: dict[str, Any]) -> dict[str, Any] | None:
    selected = snapshot.get("selectedAppleMusicSession")
    if isinstance(selected, dict):
        return selected
    return None


def playback_status(session: dict[str, Any] | None) -> str:
    if session is None:
        return "Stopped"
    state = (session.get("playbackState") or {}).get("state")
    if state == "playing":
        return "Playing"
    if state == "paused":
        return "Paused"
    return "Stopped"


def position_us(session: dict[str, Any] | None) -> int:
    if session is None:
        return 0
    position_ms = (session.get("playbackState") or {}).get("positionMs")
    if isinstance(position_ms, (int, float)) and position_ms > 0:
        return int(position_ms * 1000)
    return 0


def duration_us(session: dict[str, Any] | None) -> int:
    metadata = (session or {}).get("metadata") or {}
    duration_ms = metadata.get("durationMs")
    if isinstance(duration_ms, (int, float)) and duration_ms > 0:
        return int(duration_ms * 1000)
    return 0


def playback_speed(session: dict[str, Any] | None) -> float:
    if session is None:
        return 1.0
    speed = (session.get("playbackState") or {}).get("speed")
    if isinstance(speed, (int, float)) and speed > 0:
        return float(speed)
    return 1.0


def actions(session: dict[str, Any] | None) -> set[str]:
    if session is None:
        return set()
    raw = (session.get("playbackState") or {}).get("actions")
    if not isinstance(raw, list):
        return set()
    return {item for item in raw if isinstance(item, str)}


def can_go_next(session: dict[str, Any] | None) -> bool:
    return "next" in actions(session)


def can_go_previous(session: dict[str, Any] | None) -> bool:
    return "previous" in actions(session)


def can_pause(session: dict[str, Any] | None) -> bool:
    return "pause" in actions(session) or "playPause" in actions(session)


def can_seek(session: dict[str, Any] | None) -> bool:
    return "seekTo" in actions(session)


def has_current_track(session: dict[str, Any] | None) -> bool:
    metadata = (session or {}).get("metadata") or {}
    return bool(metadata.get("present") and (metadata.get("title") or metadata.get("mediaId")))


def mpris_metadata(session: dict[str, Any] | None, art_url: str | None = None) -> dict[str, Any]:
    if session is None:
        return {"mpris:trackid": MPRIS_NO_TRACK}

    metadata = session.get("metadata") or {}
    if not metadata.get("present"):
        return {"mpris:trackid": MPRIS_NO_TRACK}

    result: dict[str, Any] = {
        "mpris:trackid": track_id(metadata),
    }
    copy_string(metadata, result, "title", "xesam:title")
    copy_string(metadata, result, "album", "xesam:album")
    copy_string_array(metadata, result, "artist", "xesam:artist")
    copy_string_array(metadata, result, "albumArtist", "xesam:albumArtist")

    duration = duration_us(session)
    if duration > 0:
        result["mpris:length"] = duration

    if art_url:
        result["mpris:artUrl"] = art_url
    return result


def track_id(metadata: dict[str, Any]) -> str:
    raw = str(metadata.get("mediaId") or metadata.get("title") or "current")
    safe = re.sub(r"[^A-Za-z0-9_]", "_", raw).strip("_") or "current"
    return f"/org/mpris/MediaPlayer2/TrackList/{safe[:80]}"


def copy_string(source: dict[str, Any], target: dict[str, Any], source_key: str, target_key: str) -> None:
    value = source.get(source_key)
    if isinstance(value, str) and value:
        target[target_key] = value


def copy_string_array(source: dict[str, Any], target: dict[str, Any], source_key: str, target_key: str) -> None:
    value = source.get(source_key)
    if isinstance(value, str) and value:
        target[target_key] = [value]
