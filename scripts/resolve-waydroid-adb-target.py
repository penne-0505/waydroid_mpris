#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "host"))

from waydroid_mpris.adb_recovery import AdbRecoveryError, AdbRecoveryManager  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve one ready Waydroid ADB target.")
    parser.add_argument("--adb", default="adb", help="adb executable path.")
    parser.add_argument("--waydroid", default="waydroid", help="waydroid executable path.")
    parser.add_argument("--device", default=None, help="Explicit ADB serial instead of Waydroid discovery.")
    args = parser.parse_args()

    manager = AdbRecoveryManager(
        adb_path=args.adb,
        waydroid_path=args.waydroid,
        device=args.device,
    )
    try:
        print(manager.ensure_connected())
    except AdbRecoveryError as ex:
        print(f"error: {ex}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
