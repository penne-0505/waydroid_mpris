from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from host.waydroid_mpris.artwork import AdbArtworkCache


COMPLETE_PNG = b"\x89PNG\r\n\x1a\npayload\x00\x00\x00\x00IEND\xaeB`\x82"
TRUNCATED_PNG = b"\x89PNG\r\n\x1a\npayload"


class FakeTransport:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.reads = 0

    def read_file(self, android_path: str) -> bytes:
        self.reads += 1
        self.android_path = android_path
        return self.data


class ArtworkCacheTest(unittest.TestCase):
    def setUp(self) -> None:
        self.session = {
            "metadata": {
                "present": True,
                "mediaId": "example-media-id",
                "title": "Example Track",
                "artworkFile": {
                    "present": True,
                    "path": "/sdcard/Android/data/dev.penne.waydroidmpris.probe/files/artwork/example.png",
                },
            }
        }

    def test_invalid_existing_cache_is_replaced_atomically(self) -> None:
        with TemporaryDirectory() as tmp:
            transport = FakeTransport(COMPLETE_PNG)
            cache = AdbArtworkCache(transport, tmp)
            metadata = self.session["metadata"]
            cache_path = cache._cache_path(metadata, metadata["artworkFile"]["path"])
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(TRUNCATED_PNG)

            art_url = cache.art_url_for(self.session)

            self.assertEqual(transport.reads, 1)
            self.assertIsNotNone(art_url)
            self.assertEqual(cache_path.read_bytes(), COMPLETE_PNG)
            self.assertFalse(Path(str(cache_path) + ".tmp").exists())

    def test_complete_existing_cache_is_reused(self) -> None:
        with TemporaryDirectory() as tmp:
            transport = FakeTransport(b"unused")
            cache = AdbArtworkCache(transport, tmp)
            metadata = self.session["metadata"]
            cache_path = cache._cache_path(metadata, metadata["artworkFile"]["path"])
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(COMPLETE_PNG)

            art_url = cache.art_url_for(self.session)

            self.assertEqual(transport.reads, 0)
            self.assertIsNotNone(art_url)

    def test_invalid_download_is_not_published(self) -> None:
        with TemporaryDirectory() as tmp:
            transport = FakeTransport(TRUNCATED_PNG)
            cache = AdbArtworkCache(transport, tmp)
            metadata = self.session["metadata"]
            cache_path = cache._cache_path(metadata, metadata["artworkFile"]["path"])

            art_url = cache.art_url_for(self.session)

            self.assertIsNone(art_url)
            self.assertFalse(cache_path.exists())


if __name__ == "__main__":
    unittest.main()
