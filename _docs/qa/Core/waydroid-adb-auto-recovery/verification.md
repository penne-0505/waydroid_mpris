---
title: "QA Verification: Waydroid ADB automatic recovery"
status: active
draft_status: n/a
qa_status: partial
risk: High
created_at: 2026-07-10
updated_at: 2026-07-10
references:
  - "_docs/qa/Core/waydroid-adb-auto-recovery/test-plan.md"
  - "_docs/intent/Core/waydroid-adb-auto-recovery/decision.md"
  - "_docs/plan/Core/waydroid-adb-auto-recovery/plan.md"
  - "_docs/qa/Core/waydroid-mpris-bridge/verification.md"
related_issues: []
related_prs: []
---

# QA Verification: `Waydroid ADB automatic recovery`

## Summary

2026-07-10 に automatic recovery implementation、diagnostics、bounded logging、
user-facing docs を非破壊的に検証した。既存 17 tests と追加 16 tests は全件通過し、
read-only live checks では現在の unavailable source が MPRIS `Stopped`、no-track
metadata、`CanControl=false` へ落ちていることを確認した。

installed user service は 10:08 JST から変更前 process のまま稼働しており、checkout の
新 code を読み直していない。明示的に禁止された service / Waydroid restart、ADB
disconnect、Android authorization 操作は実行していない。このため、実環境での
automatic reconnect、authorization transition、journal cadence は deferred である。

## Verification Verdict

Verdict: PARTIAL

自動化可能な AC / INV と current safe-state は確認済みで、failure はない。ただし Risk High
の live recovery path は未実行であり、実 restart / disconnect 後に manual `adb connect`
なしで戻ることを実測していない。未検証部分は `Core-Test-17` として追跡する。

## Commands Run

### Automated tests and static checks

```bash
python -m unittest tests/test_protocol_mapping.py tests/test_adb_transport.py tests/test_adb_recovery.py tests/test_live_failure_mapping.py tests/test_position_projection.py tests/test_artwork_cache.py
python -m py_compile host/waydroid_mpris/*.py scripts/run-host-mpris-live.py scripts/run-host-mpris-fixture.py scripts/doctor.py scripts/run-disruptive-waydroid-restart-qa.py
bash -n scripts/install-user-service.sh
./scripts/install-user-service.sh --dry-run > /tmp/waydroid-mpris-dry-run.service
systemd-analyze --user verify /tmp/waydroid-mpris-dry-run.service
./scripts/check-docs.sh
git diff --check
```

### Read-only live checks

```bash
waydroid status
adb devices -l
python scripts/doctor.py
playerctl --player=waydroid_mpris status
playerctl --player=waydroid_mpris metadata --format '{{title}}|{{artist}}|{{mpris:artUrl}}'
systemctl --user show waydroid-mpris.service -p ActiveState -p SubState -p ExecMainStartTimestamp -p ExecStart
busctl --user get-property org.mpris.MediaPlayer2.waydroid_mpris /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player PlaybackStatus
busctl --user get-property org.mpris.MediaPlayer2.waydroid_mpris /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player CanControl
busctl --user get-property org.mpris.MediaPlayer2.waydroid_mpris /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player Metadata
journalctl --user -u waydroid-mpris.service -n 8 --no-pager -o cat
```

`systemd-analyze` は最初に `.txt` suffix の一時ファイルを渡したため unit filename として
認識せず `Invalid argument` になった。`.service` suffix で同じ generated content を再検証し
PASS した。これは generated unit の failure ではない。

## Automated Test Results

- Unit tests: **PASS** — 33 tests、0 failures、0 errors。
  - baseline: 既存 17 tests。
  - added/updated: recovery / diagnostics / target-scoping の 16 tests。
- Python compile: **PASS**。
- Shell syntax: **PASS**。
- Generated user unit dry-run: **PASS**。runtime IP の固定値を含まず、既存 ExecStart のまま
  automatic discovery enabled daemon を起動する。
- `systemd-analyze --user verify`: **PASS**。
- Documentation validators: **PASS**。
- `git diff --check`: **PASS**。

## Manual QA Results

- `waydroid status`: session / container RUNNING、runtime IP `192.168.240.112`。
- `adb devices -l`: target absent。
- updated `doctor.py`: `192.168.240.112:5555 is missing; the daemon will retry adb connect with backoff`
  と診断し exit 1。doctor 自身は `adb connect` を実行していない。
- installed service: active / running。ただし変更前 process のため、journal は既知の
  `adb: no devices/emulators found` を毎 poll 出力している。新 logger の live result としては
  扱わない。
- MPRIS live safe state:
  - `PlaybackStatus`: `Stopped`。
  - `CanControl`: `false`。
  - `Metadata`: `mpris:trackid=/org/mpris/MediaPlayer2/TrackList/NoTrack` のみ。
  - `playerctl metadata`: empty/no active player response。doctor は Stopped 時の empty metadata を
    safety success として扱う。
- no host listener / Android code / installed unit file mutation: diff review で変更なし。

## Acceptance Criteria Coverage

- AC-001: **PARTIAL** — Waydroid IP discovery、missing/offline connect、recovery transition、
  1→configured max backoff は deterministic unit tests で確認。real ADB disconnect/restart は deferred。
- AC-002: **PARTIAL** — unauthorized で connect を呼ばず operator action を返すことと doctor 文言は
  unit verified。real Android prompt transition は deferred。
- AC-003: **PASS** — explicit target precedence、multiple device fail-closed、snapshot / command /
  artwork の `-s` target scope を unit verified。
- AC-004: **PASS** — regression tests と current live D-Bus state で Stopped / no-track /
  `CanControl=false` を確認。
- AC-005: **PARTIAL** — retry cap、identical log suppression、state-change / recovery log を fake clock で
  unit verified。installed new process の journal cadence は deferred。
- AC-006: **PASS** — `adb connect` 以外の mutation、network listener、`adb kill-server`、Waydroid
  lifecycle command を追加せず、Android selected-session code は unchanged。
- AC-007: **PASS** — AC / INV 対応 tests と test matrix を追加し、full suite / validators が通過。

## Invariant Coverage

- INV-001: **PASS** — explicit / discovered target と全 payload I/O の `-s` scope を tests / diff で確認。
- INV-002: **PASS** — missing/offline TCP target だけが connect 対象で、unauthorized / non-TCP は
  operator action になる。
- INV-003: **PASS** — Waydroid stopped 時に別の ready device を fallback にしない test が通過。
- INV-004: **PARTIAL** — bounded retry / logging algorithm は fake-clock verified。live journal は deferred。
- INV-005: **PASS** — recovery exception を含む unavailable source が empty snapshot / stopped state へ
  写像される。
- INV-006: **PASS** — no listener、no Waydroid lifecycle mutation、no global ADB reset を diff review。
- INV-007: **PASS** — Android source unchanged、existing protocol / command rejection tests PASS。

## Deferred / Not Covered

- installed user service を new daemon code で restart すること。
- `adb disconnect <resolved-target>` または Waydroid restart 後の automatic reconnect latency。
- Android が `unauthorized` を返す場合の prompt guidance と、approval 後の automatic recovery。
- new daemon process の journal が初回 / state change / 60-second reminder / recovery cadence になること。
- recovery 後の live Apple Music metadata / controls / artwork restoration。

## Residual Risks

- `waydroid status` text format が実環境差で変わる場合、unit fixture と現在の 1.6.3 output が通っても
  target discovery が失敗する可能性がある。その場合は doctor が fail closed し、別 ADB device は
  選ばない。
- ADB device table が `device` へ遷移する実時間と Android boot readiness により、復帰 latency が
  backoff 上限の 30 秒を超える可能性がある。
- user service の live process を更新していないため、現在の journal spam はこの worktree の
  implementation result を表していない。

## Follow-up TODOs

- `Core-Test-17`: 明示承認後に installed service / ADB / Waydroid を中断し、automatic reconnect、
  unauthorized guidance、journal cadence、MPRIS / Apple Music restoration を live verification する。
