## 原則

- 日本語で会話する。
- 日付確認には`date`コマンドを使用する。
- tool や shell command を優先して使用する。
- **徹底的に現状実装・ドキュメントを参照、分析してから実装を行う。**
- **`git rm`や`rm`などの恒久削除は禁止**（ユーザーに提案し、実行は待つ）。ただし、archive checklist を満たす一時ドキュメントの移送に限り `mv` / `git mv` は許可。
- [documentation guidelines](_docs/standards/documentation_guidelines.md) と [documentation operations](_docs/standards/documentation_operations.md) を遵守して、積極的にドキュメントを更新する。skillsを積極活用してドキュメント更新と実装準備を行う。
- Size >= M または Risk >= Medium のタスクでは、実装前に QA test-plan を作成し、実装後に verification を残す。
- QA / テスト方針は [quality assurance standard](_docs/standards/quality_assurance.md) に従う。
- 設計判断を体現した非自明なコード（とくに why not・意図的な省略）には、`// intent: INV-00X (<Area>/<slug>) — ...` で intent への参照を残す。全コード義務ではなくターゲット型。詳細は [quality assurance standard](_docs/standards/quality_assurance.md) の intent ↔ code traceability に従う。
- 完了前には `qa-review` skill を使い、verification verdict を確認する。
- 安全性・権限・secret・外部入力の扱いは [security for agents](_docs/standards/security_for_agents.md) に従う。
- root 直下の Markdown は active project guidance として扱われる。一回限りの実装プロンプトを残す場合は `_evals/prompts/` 等へ移し、非運用の履歴資料として明記する。

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
- Docs checks: `./scripts/check-docs.sh`
