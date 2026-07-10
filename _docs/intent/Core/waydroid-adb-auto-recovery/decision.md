---
title: Waydroid ADB automatic recovery decision
status: active
draft_status: n/a
created_at: 2026-07-10
updated_at: 2026-07-10
references:
  - "_docs/plan/Core/waydroid-adb-auto-recovery/plan.md"
  - "_docs/qa/Core/waydroid-adb-auto-recovery/test-plan.md"
  - "_docs/qa/Core/waydroid-adb-auto-recovery/verification.md"
  - "_docs/intent/Core/waydroid-mpris-bridge/decision.md"
related_issues: []
related_prs: []
---

# Waydroid ADB automatic recovery decision

## Context

host daemon は ADB snapshot read を poll するだけで connection lifecycle を持たない。
Waydroid / ADB restart 後に `adb devices` が空になると、MPRIS の stale-state safety は
働く一方、利用者が `adb connect` するまで復帰せず、journal へ同じ read failure を
poll interval ごとに記録する。

Waydroid の IP は runtime state であり固定値として扱えない。ADB server は複数 device を
管理できるため、target 未指定の `adb shell` は誤配送または `more than one device` failure
になり得る。さらに `unauthorized` は Android の RSA authorization boundary であり、daemon
が成功扱いまたは自動回避してはならない。

## Decision

- live daemon 専用の recovery manager を導入し、plain `AdbProbeTransport` の fixture / unit
  利用は connection side effect なしのまま保つ。
- target selection は次の優先順位にする。
  1. explicit `--device` serial。
  2. `waydroid status` が session / container RUNNING と報告したときの validated IP と port 5555。
- target が `device` なら `-s <target>` を付けて bridge I/O を行う。
- target が missing / offline の場合だけ `adb connect <target>` を試し、failure 後は 1 秒から
  30 秒まで exponential backoff する。
- target が `unauthorized` の場合は connect retry で状態を隠さず、operator action required
  error を返す。定期的な read-only state recheck によって、利用者が承認した後は自動復帰する。
- Waydroid stopped / IP unknown / unsupported explicit serial では外部 target を推測しない。
- host-wide `adb kill-server`、Waydroid restart、authorization 操作は自動 recovery に含めない。
- MPRIS object は source unavailable 中も生存し、既存 empty snapshot mapping を使う。
- failure logging は error class / target を stable key として抑制し、初回・状態変化・60 秒 reminder・
  recovery を記録する。

## Alternatives

- **systemd の service restart に任せる**: daemon 自体は正常で source だけが unavailable なため
  `Restart=on-failure` は起動せず、restart loop にしても ADB connection は確立されない。
- **毎 poll `adb connect` する**: 復帰 latency は短いが、毎秒 subprocess と log を発生させ、
  unauthorized / stopped state でも無意味な retry を続ける。
- **`adb kill-server` してから接続する**: connection cache を reset できるが、同一 user の他 device
  と開発作業を巻き込み、bridge の target scope を越える。
- **unique な ADB device を暗黙採用する**: Waydroid 以外の phone / emulator を Apple Music bridge
  target にする可能性があり、selected Waydroid boundary を保証できない。
- **Waydroid 固定 IP を設定に埋め込む**: 現在の環境では動くが、DHCP lease と環境差を無視する。
- **Waydroid session を daemon が起動する**: user service の責務を超え、意図しない UI / container
  lifecycle mutation を起こす。

## Rationale

ADB の再接続は transport availability の回復であり、MPRIS service や Waydroid lifecycle の
restart とは分離すべきである。runtime IP と ADB device table を使って target を明示すれば、
複数 device があっても bridge I/O を Waydroid に限定できる。bounded retry は日常利用の自動復帰と
journal の可読性を両立し、authorization は Android 上の user consent として残る。

## Consequences / Impact

- daemon は `waydroid status` と `adb devices -l` を補助 subprocess として実行する。
- source failure 後の retry latency は最大 30 秒になる。
- `unauthorized` の自動復帰は、利用者が prompt を承認した後の state recheck に限られる。
- `--device` に非 TCP serial を指定した場合、missing target を connect できず診断だけを返す。
- ADB server は client command により自動起動し得るが、daemon は server kill / global reset をしない。

## Quality Implications

- target resolution と ADB state classification は subprocess output fixture で deterministic に
  テストできなければならない。
- recovery path が失敗しても既存 stale-state mapping を迂回してはならない。
- authorization required と retryable unavailable を operator に同じ failure として見せてはならない。
- multiple device test は target に `-s` が付くことと unrelated device を採用しないことを確認する。
- logging test は real sleep を使わず monotonic clock injection で cadence を確認する。

## Intent-derived Invariants

- INV-001: explicit `--device` は Waydroid IP discovery より常に優先され、全 bridge ADB I/O は resolved target へ `-s` 付きで送られなければならない。
- INV-002: automatic recovery は missing / offline の TCP target にだけ `adb connect` を行い、`unauthorized` を user consent なしに回避または ready 扱いしてはならない。
- INV-003: Waydroid stopped、IP unknown、unsupported target のとき、daemon は unrelated ADB device を fallback target として採用してはならない。
- INV-004: recovery retry は bounded exponential backoff に従い、同一 failure log は毎 poll 出力せず、状態変化と recovery を観測可能にしなければならない。
- INV-005: recovery failure 中も Android source unavailable は MPRIS `Stopped` / empty metadata / `CanControl=false` に写像され、stale `Playing` を残してはならない。
- INV-006: automatic recovery は ADB client connection だけを変更し、host network listener、Waydroid lifecycle mutation、host-wide ADB server reset を追加してはならない。
- INV-007: command routing と Android payload は既存 bridge の selected Apple Music session only / MediaSession-derived data only の境界を維持しなければならない。

## Enforced in (optional)

- INV-001〜003: connection discovery / state manager と `tests/test_adb_recovery.py`。
- INV-004: recovery manager / failure reporter と deterministic clock tests。
- INV-005: `read_live_snapshot_or_empty` と `tests/test_live_failure_mapping.py`。
- INV-006〜007: diff review、existing transport / Android command tests、docs verification。

## Rollback / Follow-ups

- Recovery manager を live daemon から外せば、connection side effect のない従来 polling へ戻せる。
- Waydroid CLI が将来 machine-readable status を提供する場合、text parser をその interface へ置き換える。
- live restart E2E は明示承認後に実行し、実測 recovery latency と journal cadence を verification に追記する。
