from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .adb_transport import AdbProbeTransport


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_IEND = b"\x00\x00\x00\x00IEND\xaeB`\x82"


class AdbArtworkCache:
    def __init__(self, transport: AdbProbeTransport, cache_dir: str | Path | None = None) -> None:
        self.transport = transport
        self.cache_dir = Path(cache_dir or Path.home() / ".cache/waydroid-mpris/artwork")

    def art_url_for(self, session: dict[str, Any] | None) -> str | None:
        if session is None:
            return None
        metadata = session.get("metadata") or {}
        artwork_file = metadata.get("artworkFile") or {}
        if not artwork_file.get("present"):
            return None
        android_path = artwork_file.get("path")
        if not isinstance(android_path, str) or not android_path:
            return None

        cache_path = self._cache_path(metadata, android_path)
        if not self._cache_file_valid(cache_path):
            data = self.transport.read_file(android_path)
            if not self._png_complete(data):
                return None
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = cache_path.with_name(cache_path.name + ".tmp")
            tmp_path.write_bytes(data)
            tmp_path.replace(cache_path)
        if not self._cache_file_valid(cache_path):
            return None
        return cache_path.resolve().as_uri()

    def _cache_path(self, metadata: dict[str, Any], android_path: str) -> Path:
        seed = str(metadata.get("mediaId") or metadata.get("title") or android_path)
        digest = hashlib.sha256(android_path.encode("utf-8")).hexdigest()[:12]
        safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in seed)[:80] or "current"
        return self.cache_dir / f"{safe}-{digest}.png"

    def _cache_file_valid(self, path: Path) -> bool:
        if not path.exists() or path.stat().st_size <= 0:
            return False
        try:
            return self._png_complete(path.read_bytes())
        except OSError:
            return False

    @staticmethod
    def _png_complete(data: bytes) -> bool:
        return data.startswith(PNG_SIGNATURE) and data.endswith(PNG_IEND)
