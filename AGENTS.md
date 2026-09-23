## 原則

- 日本語で会話する。
- 日付確認には`date`コマンドを使用する。
- tool や shell command を優先して使用する。
- **徹底的に現状実装・ドキュメントを参照、分析してから実装を行う。**
- **`git rm`や`rm`などの恒久削除は禁止**（ユーザーに提案し、実行は待つ）。

## Project Commands

- Android companion build: `./scripts/build-android-probe.sh`
- Android companion install: `./scripts/install-android-probe.sh`
- Permission settings: `./scripts/open-android-notification-listener-settings.sh`
- Host fixture daemon: `python scripts/run-host-mpris-fixture.py fixtures/probe/apple-music-playing.sample.json`
- Host live daemon: `python scripts/run-host-mpris-live.py --poll-interval 1.0`
- User service install: `./scripts/install-user-service.sh --enable-now`
- User service dry-run: `./scripts/install-user-service.sh --dry-run`
- Diagnostics: `python scripts/doctor.py`
- Disruptive restart QA: `python scripts/run-disruptive-waydroid-restart-qa.py --i-understand-this-stops-waydroid --device <adb-serial>`
- Unit checks: `python -m unittest tests/test_protocol_mapping.py tests/test_adb_transport.py tests/test_adb_recovery.py tests/test_live_failure_mapping.py tests/test_position_projection.py tests/test_artwork_cache.py`
