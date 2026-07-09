from __future__ import annotations

import argparse
import json
import signal
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

from .adb_transport import DEFAULT_PROBE_PATH, AdbProbeTransport
from .artwork import AdbArtworkCache
from .position import PositionProjector
from . import protocol


MPRIS_OBJECT_PATH = "/org/mpris/MediaPlayer2"
BUS_NAME = "org.mpris.MediaPlayer2.waydroid_mpris"
ROOT_IFACE = "org.mpris.MediaPlayer2"
PLAYER_IFACE = "org.mpris.MediaPlayer2.Player"
PROPS_IFACE = "org.freedesktop.DBus.Properties"
CommandHandler = Callable[[str, int | None], None]
ArtworkProvider = Callable[[dict[str, Any] | None], str | None]


class WaydroidMprisObject(dbus.service.Object):
    def __init__(
        self,
        bus: dbus.SessionBus,
        snapshot: dict[str, Any],
        command_handler: CommandHandler | None = None,
        artwork_provider: ArtworkProvider | None = None,
    ) -> None:
        self.snapshot = snapshot
        self.session = protocol.selected_session(snapshot)
        self.command_handler = command_handler
        self.artwork_provider = artwork_provider
        self.position_projector = PositionProjector()
        self.position_projector.update(self.session)
        self.art_url = self._load_art_url(self.session)
        bus_name = dbus.service.BusName(BUS_NAME, bus=bus)
        super().__init__(bus_name, MPRIS_OBJECT_PATH)

    @dbus.service.method(ROOT_IFACE, in_signature="", out_signature="")
    def Raise(self) -> None:
        return None

    @dbus.service.method(ROOT_IFACE, in_signature="", out_signature="")
    def Quit(self) -> None:
        return None

    @dbus.service.method(PLAYER_IFACE, in_signature="", out_signature="")
    def Next(self) -> None:
        self._dispatch("next")

    @dbus.service.method(PLAYER_IFACE, in_signature="", out_signature="")
    def Previous(self) -> None:
        self._dispatch("previous")

    @dbus.service.method(PLAYER_IFACE, in_signature="", out_signature="")
    def Pause(self) -> None:
        self._dispatch("pause")

    @dbus.service.method(PLAYER_IFACE, in_signature="", out_signature="")
    def PlayPause(self) -> None:
        self._dispatch("playPause")

    @dbus.service.method(PLAYER_IFACE, in_signature="", out_signature="")
    def Stop(self) -> None:
        self._dispatch("stop")

    @dbus.service.method(PLAYER_IFACE, in_signature="", out_signature="")
    def Play(self) -> None:
        self._dispatch("play")

    @dbus.service.method(PLAYER_IFACE, in_signature="x", out_signature="")
    def Seek(self, offset: int) -> None:
        position_ms = max(0, int((self.position_projector.position_us() + int(offset)) / 1000))
        self._dispatch("seekTo", position_ms)

    @dbus.service.method(PLAYER_IFACE, in_signature="ox", out_signature="")
    def SetPosition(self, track_id: dbus.ObjectPath, position: int) -> None:
        current_track = protocol.mpris_metadata(self.session).get("mpris:trackid")
        if str(track_id) == current_track:
            self._dispatch("seekTo", max(0, int(position / 1000)))

    @dbus.service.method(PLAYER_IFACE, in_signature="s", out_signature="")
    def OpenUri(self, uri: str) -> None:
        return None

    @dbus.service.method(PROPS_IFACE, in_signature="ss", out_signature="v")
    def Get(self, interface_name: str, property_name: str) -> dbus.Variant:
        props = self._properties_for(interface_name)
        if property_name not in props:
            raise dbus.exceptions.DBusException(
                f"Unknown property {interface_name}.{property_name}",
                name="org.freedesktop.DBus.Error.UnknownProperty",
            )
        return props[property_name]

    @dbus.service.method(PROPS_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface_name: str) -> dbus.Dictionary:
        return dbus.Dictionary(self._properties_for(interface_name), signature="sv")

    @dbus.service.method(PROPS_IFACE, in_signature="ssv", out_signature="")
    def Set(self, interface_name: str, property_name: str, value: dbus.Variant) -> None:
        raise dbus.exceptions.DBusException(
            f"Read-only property {interface_name}.{property_name}",
            name="org.freedesktop.DBus.Error.PropertyReadOnly",
        )

    @dbus.service.signal(PROPS_IFACE, signature="sa{sv}as")
    def PropertiesChanged(
        self,
        interface_name: str,
        changed_properties: dbus.Dictionary,
        invalidated_properties: dbus.Array,
    ) -> None:
        return None

    def update_snapshot(self, snapshot: dict[str, Any]) -> None:
        before = self._player_fingerprint()
        self.snapshot = snapshot
        self.session = protocol.selected_session(snapshot)
        self.position_projector.update(self.session)
        self.art_url = self._load_art_url(self.session)
        if self._player_fingerprint() != before:
            self.PropertiesChanged(
                PLAYER_IFACE,
                dbus.Dictionary(self._player_properties(), signature="sv"),
                dbus.Array([], signature="s"),
            )

    def _properties_for(self, interface_name: str) -> dict[str, Any]:
        if interface_name == ROOT_IFACE:
            return self._root_properties()
        if interface_name == PLAYER_IFACE:
            return self._player_properties()
        raise dbus.exceptions.DBusException(
            f"Unknown interface {interface_name}",
            name="org.freedesktop.DBus.Error.UnknownInterface",
        )

    def _root_properties(self) -> dict[str, Any]:
        return {
            "CanQuit": dbus.Boolean(False),
            "Fullscreen": dbus.Boolean(False),
            "CanSetFullscreen": dbus.Boolean(False),
            "CanRaise": dbus.Boolean(False),
            "HasTrackList": dbus.Boolean(False),
            "Identity": dbus.String("Waydroid MPRIS"),
            "DesktopEntry": dbus.String(""),
            "SupportedUriSchemes": dbus.Array([], signature="s"),
            "SupportedMimeTypes": dbus.Array([], signature="s"),
        }

    def _player_properties(self) -> dict[str, Any]:
        session = self.session
        metadata = to_dbus_metadata(protocol.mpris_metadata(session, self.art_url))
        return {
            "PlaybackStatus": dbus.String(protocol.playback_status(session)),
            "LoopStatus": dbus.String("None"),
            "Rate": dbus.Double(1.0),
            "Shuffle": dbus.Boolean(False),
            "Metadata": metadata,
            "Volume": dbus.Double(1.0),
            "Position": dbus.Int64(self.position_projector.position_us()),
            "MinimumRate": dbus.Double(1.0),
            "MaximumRate": dbus.Double(1.0),
            "CanGoNext": dbus.Boolean(protocol.can_go_next(session)),
            "CanGoPrevious": dbus.Boolean(protocol.can_go_previous(session)),
            "CanPlay": dbus.Boolean(protocol.has_current_track(session)),
            "CanPause": dbus.Boolean(protocol.can_pause(session)),
            "CanSeek": dbus.Boolean(protocol.can_seek(session)),
            "CanControl": dbus.Boolean(session is not None),
        }

    def _dispatch(self, command: str, position_ms: int | None = None) -> None:
        if self.command_handler is None:
            return None
        try:
            self.command_handler(command, position_ms)
        except Exception as ex:
            raise dbus.exceptions.DBusException(
                str(ex),
                name="dev.penne.waydroid_mpris.CommandFailed",
            )

    def _player_fingerprint(self) -> str:
        session = self.session
        data = {
            "status": protocol.playback_status(session),
            "positionUs": protocol.position_us(session),
            "metadata": protocol.mpris_metadata(session, self.art_url),
            "canGoNext": protocol.can_go_next(session),
            "canGoPrevious": protocol.can_go_previous(session),
            "canPause": protocol.can_pause(session),
            "canSeek": protocol.can_seek(session),
            "canControl": session is not None,
        }
        return json.dumps(data, sort_keys=True)

    def _load_art_url(self, session: dict[str, Any] | None) -> str | None:
        if self.artwork_provider is None:
            return None
        try:
            return self.artwork_provider(session)
        except Exception as ex:
            print(f"waydroid-mpris: failed to cache artwork: {ex}", file=sys.stderr)
            return None


def to_dbus_metadata(metadata: dict[str, Any]) -> dbus.Dictionary:
    converted: dict[str, Any] = {}
    for key, value in metadata.items():
        if key == "mpris:trackid":
            converted[key] = dbus.ObjectPath(value)
        elif key == "mpris:length":
            converted[key] = dbus.Int64(value)
        elif isinstance(value, list):
            converted[key] = dbus.Array([dbus.String(item) for item in value], signature="s")
        elif isinstance(value, str):
            converted[key] = dbus.String(value)
        else:
            converted[key] = value
    return dbus.Dictionary(converted, signature="sv")


def serve_fixture(fixture_path: str | Path) -> None:
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    snapshot = protocol.load_snapshot(fixture_path)
    WaydroidMprisObject(bus, snapshot)
    run_mainloop()


def serve_live(
    adb_path: str = "adb",
    device: str | None = None,
    probe_path: str | None = None,
    poll_interval_seconds: float = 1.0,
    artwork_cache_dir: str | Path | None = None,
) -> None:
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    transport = AdbProbeTransport(
        adb_path=adb_path,
        device=device,
        probe_path=probe_path or DEFAULT_PROBE_PATH,
    )
    snapshot = read_live_snapshot_or_empty(transport)
    artwork_cache = AdbArtworkCache(transport, artwork_cache_dir)
    mpris = WaydroidMprisObject(
        bus,
        snapshot,
        command_handler=transport.send_command,
        artwork_provider=artwork_cache.art_url_for,
    )

    def poll() -> bool:
        mpris.update_snapshot(read_live_snapshot_or_empty(transport))
        return True

    GLib.timeout_add(max(250, int(poll_interval_seconds * 1000)), poll)
    run_mainloop()


def read_live_snapshot_or_empty(transport: AdbProbeTransport) -> dict[str, Any]:
    try:
        return transport.read_snapshot()
    except Exception as ex:
        print(f"waydroid-mpris: failed to read live probe: {ex}", file=sys.stderr)
        return protocol.empty_snapshot("adb_probe_read_failed", str(ex))


def run_mainloop() -> None:
    mainloop = GLib.MainLoop()

    def stop(*_args: object) -> None:
        mainloop.quit()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    mainloop.run()


def main() -> None:
    parser = argparse.ArgumentParser(description="Expose a probe fixture as a minimal MPRIS player.")
    parser.add_argument("fixture", type=Path, help="Path to a probe snapshot JSON fixture.")
    args = parser.parse_args()
    serve_fixture(args.fixture)


if __name__ == "__main__":
    main()
