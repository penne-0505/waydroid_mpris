---
title: Waydroid ADB automatic recovery implementation plan
status: active
draft_status: n/a
created_at: 2026-07-10
updated_at: 2026-07-10
references:
  - "_docs/intent/Core/waydroid-adb-auto-recovery/decision.md"
  - "_docs/qa/Core/waydroid-adb-auto-recovery/test-plan.md"
  - "_docs/qa/Core/waydroid-adb-auto-recovery/verification.md"
  - "_docs/intent/Core/waydroid-mpris-bridge/decision.md"
  - "_docs/guide/Core/waydroid-mpris-bridge/usage.md"
related_issues: []
related_prs: []
---

# Waydroid ADB automatic recovery implementation plan

## Overview

systemd user service として常駐する host daemon に、Waydroid の ADB target を
決定して connection を回復する lifecycle を追加する。source が利用不能な間は
既存どおり MPRIS を安全な stopped state へ落とし、同一 failure の retry と log は
bounded にする。

調査根拠:

- Waydroid 公式手順は Waydroid の IP に対する `adb connect <IP>:5555` を案内している。
  <https://docs.waydro.id/faq/using-adb-with-waydroid>
- Android 公式 ADB document は、connection 消失時に `adb connect` を再実行すること、
  複数 device 時は `-s serial` で target を指定すること、RSA debugging authorization は
  Android 上の利用者承認を必要とすることを定義している。
  <https://developer.android.com/tools/adb>
- 現在の Waydroid 1.6.3 は `waydroid status` に session / container state と
  `IP address` を出力する。2026-07-10 の対象は `192.168.240.112` だが、実装はこの値を
  固定しない。

## Scope

- host daemon 起動時と transport failure 後に Waydroid ADB target を解決する。
- explicit `--device` があればその serial を優先し、なければ `waydroid status` の
  running state と IP から `<IP>:5555` を作る。
- `adb devices -l` の target state を `device` / `offline` / `unauthorized` /
  missing として分類する。
- missing / offline は `adb connect <target>` を bounded exponential backoff で試す。
- `unauthorized` は connect の再実行で回避せず、operator action required とする。
- connection 不在中も live daemon と MPRIS D-Bus service は維持し、empty snapshot を
  publish する。
- 同一 failure log は初回と一定間隔だけ出し、state transition と recovery は即時に出す。
- `doctor.py` に resolved target と operator action を含む read-only 診断を追加する。
- README / usage guide / bridge protocol reference に default recovery と制約を反映する。

## Non-Goals

- Android の ADB authorization prompt を自動承認すること。
- `adb kill-server` によって他 device を含む host-wide ADB state を reset すること。
- Waydroid session / container / systemd user service を daemon が起動・停止・再起動すること。
- 非 TCP serial（USB / emulator）を任意の方法で再接続すること。
- ADB 以外の socket transport または host network listener を追加すること。
- Apple Music 以外の Android media session を fallback target にすること。

## Requirements

- **Functional**:
  - resolved target が ready なら既存 snapshot / artwork / command 操作を継続する。
  - target が missing / offline なら retry window 到達時だけ connect を試す。
  - target が unauthorized なら Android 側で承認する手順を明示する。
  - Waydroid が未起動または IP 不明なら connect を実行しない。
  - failure 後に target が `device` へ戻れば手動 daemon restart なしで再開する。
- **Non-Functional**:
  - default retry delay は 1 秒から開始し、最大 30 秒へ bounded exponential backoff する。
  - 同一 error の reminder log は最大 60 秒に 1 回とし、抑制件数を表示する。
  - subprocess は argument list で実行し、発見した IP は IP address として検証する。
  - explicit / discovered target の全 ADB payload 操作は `-s` を使う。
  - source unavailable 時の MPRIS safety と既存 privacy / routing invariant を維持する。

## Tasks

1. connection state parser と Waydroid target discovery を host module に追加する。
2. recovery manager に retry/backoff と authorization boundary を追加する。
3. live transport の snapshot / command / artwork read を recovery manager 経由にする。
4. live poll の repeated-failure logger と recovery log を追加する。
5. doctor を resolved target aware にし、unavailable 時の派生 check を skip する。
6. AC / INV に対応する deterministic unit tests を追加する。
7. user-facing docs と verification を更新する。

## QA Plan

- QA document: `_docs/qa/Core/waydroid-adb-auto-recovery/test-plan.md`
- Risk level: High
- Test strategy:
  - Unit: status / devices parsing、target precedence、state classification、retry schedule、
    unauthorized boundary、log suppression。
  - Integration: recovery-aware `AdbProbeTransport` command construction と
    empty stopped snapshot mapping。
  - E2E: user approval 後にのみ Waydroid / ADB restart からの recovery を確認する。
  - Manual QA: doctor output、journal cadence、MPRIS stopped/recovered transition。
  - Validator / static check: full unit suite、Python compile、shell syntax、service dry-run、
    docs validators、`git diff --check`。
  - Security review: no `adb kill-server`、no listener、explicit target、no authorization bypass。

## Deployment / Rollout

- code checkout 更新後、既存 installed service は自動では書き換えない。
- operator が差分と verification を受け入れた後、必要なら install helper を `--force` 付きで
  再実行し user service を restart する。unit の ExecStart は変わらないため、checkout を
  直接参照する現在の service は restart 後に新 daemon code を使う。
- rollback は service を止めずに prior checkout / commit の daemon code へ戻す。
- disruptive live E2E を実行しない場合は verification を `PARTIAL` とし、実再起動からの
  recovery latency と journal cadence を未検証 gap として残す。
