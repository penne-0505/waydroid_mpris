#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "host"))

from waydroid_mpris.adb_transport import DEFAULT_PROBE_PATH  # noqa: E402
from waydroid_mpris.mpris_service import serve_live  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Expose the live Waydroid Apple Music probe as MPRIS.")
    parser.add_argument("--adb", default="adb", help="adb executable path.")
    parser.add_argument(
        "--device",
        default=None,
        help="Pin an ADB device serial instead of discovering the running Waydroid IP.",
    )
    parser.add_argument("--probe-path", default=DEFAULT_PROBE_PATH, help="Android path to latest_probe.json.")
    parser.add_argument("--poll-interval", type=float, default=1.0, help="Polling interval in seconds.")
    parser.add_argument("--artwork-cache", default=None, help="Directory for cached artwork files.")
    args = parser.parse_args()
    serve_live(
        adb_path=args.adb,
        device=args.device,
        probe_path=args.probe_path,
        poll_interval_seconds=args.poll_interval,
        artwork_cache_dir=args.artwork_cache,
    )


if __name__ == "__main__":
    main()
