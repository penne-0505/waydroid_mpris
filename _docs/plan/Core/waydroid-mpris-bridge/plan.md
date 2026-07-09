---
title: Waydroid MPRIS bridge implementation plan
status: active
draft_status: n/a
created_at: 2026-07-09
updated_at: 2026-07-09
references:
  - "_docs/survey/Core/waydroid-mpris-bridge/survey.md"
  - "_docs/intent/Core/waydroid-mpris-bridge/decision.md"
  - "_docs/qa/Core/waydroid-mpris-bridge/test-plan.md"
  - "_docs/reference/Core/bridge-protocol/reference.md"
  - "../../../../fixtures/probe/apple-music-playing.sample.json"
related_issues: []
related_prs: []
---

# Waydroid MPRIS bridge implementation plan

## Overview

Waydroid 内の Android companion が Apple Music の MediaSession を読み、
host daemon がそれを MPRIS service として GNOME / `playerctl` へ公開する。
最低到達点は「操作 + 曲名」で、artwork は取得できる場合に追加する。

この計画は固定仕様ではない。probe や実装中の発見で Android / Waydroid /
MPRIS の前提が変わった場合は、TODO、plan、intent、QA を同期して更新する。

## Scope

- Android companion app:
  - notification listener permission を前提に active media sessions を読む。
  - Apple Music の session を選択し、metadata / playback state / capabilities を
    protocol event として host へ送る。
  - host からの command を選択中 session の `TransportControls` へ渡す。
- Host daemon:
  - `org.mpris.MediaPlayer2.waydroid_mpris` 相当の MPRIS service を公開する。
  - metadata-only fixture から `playerctl metadata` と GNOME 表示を確認できる。
  - `PlayPause`, `Play`, `Pause`, `Next`, `Previous` を Android 側へ送る。
- Bridge protocol:
  - JSON event/command schema と fixture を定義する。
  - M0 時点の draft は `_docs/reference/Core/bridge-protocol/reference.md` と
    `fixtures/probe/apple-music-playing.sample.json` に置く。
  - M1/M3 の最初の live transport は ADB とする。host は Android external app
    files の `latest_probe.json` を polling し、commands は explicit receiver へ
    `adb shell am broadcast` で送る。
  - この transport は host 側に network listener を開かない。将来 local
    TCP/WebSocket や Waydroid container IP へ変更する場合は INV-004 の再確認が必要。
- Documentation and QA:
  - 各 milestone の完了前に AC / INV coverage を verification に残す。
  - live Waydroid / Apple Music が必要な確認と、fixture で代替できる確認を分ける。

## Non-Goals

- Apple Music の再生音質、lossless、DRM、login、subscription 状態の変更。
- Waydroid 本体への MPRIS 実装 patch。
- GSConnect / KDE Connect 互換実装。
- 複数 Android media players の一般管理 UI。
- playlist / queue / lyrics / rating / shuffle / repeat の完全対応。
- public network 越しの remote control。
- Android 以外のモバイル端末や物理 Android phone の対応。

## Requirements

- **Functional**:
  - Host 側に MPRIS player が現れ、`playerctl --player=waydroid_mpris status`
    と metadata query が動く。
  - 曲名と artist が Apple Music session から host MPRIS metadata へ反映される。
  - `PlayPause`, `Play`, `Pause`, `Next`, `Previous` が選択中 Apple Music session
    へ送られる。
  - Android session が消えた場合、host MPRIS は stale track を `Playing` のまま
    残さない。
  - artwork が取得できる場合は `mpris:artUrl` として公開する。
- **Non-Functional**:
  - 通信は default で local-only とし、外部 network へ expose しない。
  - host daemon は fixture protocol input だけでテストできる。
  - Android companion は raw notification payload を host へ転送しない。
  - permission / privacy / failure modes は guide または reference に記録する。
  - 実装中に plan が変わった場合、TODO と QA matrix を同じ変更で更新する。

## Architecture

```text
Apple Music
  -> Android MediaSession
  -> Android companion
  -> local bridge protocol
  -> host daemon
  -> D-Bus MPRIS
  -> GNOME / playerctl / media keys
```

## Milestones

### M0: Capability probe and protocol draft

Goal: Apple Music の MediaSession から取れる情報と transport 候補を実測し、
host daemon が依存する protocol schema を固める。

- Android probe skeleton を作る。
- notification listener permission の手順を確認する。
- `packageName`, playback state, metadata keys, actions, artwork availability を
  log / fixture として保存する。
- JSON event/command schema の draft を作る。
- host fixture test の入力にできる sample events を用意する。

Exit criteria:

- Apple Music session を識別できるか、識別不能な理由が survey / plan に残る。
  - 2026-07-09: `com.apple.android.music` の active session を確認済み。
- 曲名と playback state の取得可否が実測されている。
  - 2026-07-09: title / artist / album / duration / playing state / actions を確認済み。
- artwork を M4 に進めるか、optional として扱うかの判断材料がある。
  - 2026-07-09: Android content URI と 315x315 bitmap metadata を確認済み。Host-readable URI 化は M4 の対象。

### M1: Android companion metadata service

Goal: Waydroid 内に install できる companion app が、選択中 Apple Music session の
metadata と playback state を host 向け event へ変換する。

- Android project scaffold を作る。
- `NotificationListenerService` と session callback を実装する。
- Apple Music package filtering を入れる。
- metadata normalization を実装する。
- session disappearance / pause / stop を explicit event として送る。

Exit criteria:

- live Waydroid 上で companion が Apple Music session を認識する。
- fixture と同じ shape の metadata event を出せる。
  - 2026-07-09: `latest_probe.json` を ADB 経由で host が読める live snapshot として確認済み。
- raw notification text や unrelated notifications を host へ送らない。
  - 2026-07-09: outbound snapshot は MediaSession metadata/state/capabilities に限定。

### M2: Host MPRIS daemon metadata MVP

Goal: Android がなくても fixture event から MPRIS player を公開し、GNOME /
`playerctl` で曲名と playback state を読める。

- host daemon scaffold を作る。
- D-Bus service name、MPRIS root interface、Player interface を実装する。
- fixture event reader を実装する。
- `PlaybackStatus`, `Metadata`, `CanControl`, core capability properties を出す。
- stale / disconnected state を `Stopped` と空 metadata に落とす。

Exit criteria:

- `playerctl --player=waydroid_mpris status` が fixture state を返す。
- `playerctl --player=waydroid_mpris metadata` が title / artist を返す。
- fixture test で stale state regression を検出できる。

### M3: Bidirectional command bridge

Goal: host MPRIS command が Android companion を通じて Apple Music の
`TransportControls` へ届く。

- command schema を実装する。
- `Play`, `Pause`, `PlayPause`, `Next`, `Previous` を route する。
- command の target session が stale でないことを確認する。
- command failure を host 側の log / status に残す。
- local-only transport と exposure boundary を明文化する。

Exit criteria:

- media key または `playerctl play-pause` で Apple Music を操作できる。
  - 2026-07-09: `playerctl play-pause` が `Paused -> Playing` を切り替えることを確認済み。
- `playerctl next` / `previous` が selected Apple Music session に届く。
  - 2026-07-09: `nameless -> うらみ交信 -> nameless` の往復で確認済み。
- session が失われた状態で command が誤配送されない。
  - 2026-07-09: command handler は active Apple Music controller absent を失敗扱いにする。live absent-session QA で `Stopped` / `CanControl=false` / command failure を確認済み。
- transport exposure が QA で確認される。
  - 2026-07-09: ADB transport は host network listener を開かないことを実装と手動 QA で確認済み。

### M4: Artwork pipeline

Goal: Apple Music から取得できる artwork を host MPRIS の `mpris:artUrl` として
公開する。取得できない場合でも core metadata/control を壊さない。

- Android metadata / notification icon / bitmap の取得経路を実測する。
- artwork cache の保存場所と lifecycle を決める。
- host から読める `file://` or local URI に変換する。
- artwork unavailable / decode failure を supported state として扱う。

Exit criteria:

- artwork が取れる環境では GNOME / `playerctl metadata mpris:artUrl` に URI が出る。
  - 2026-07-09: Android album art bitmap を PNG export し、host cache の `file://` URI が `playerctl metadata mpris:artUrl` に出ることを確認済み。
- artwork が取れない環境でも title / artist / controls は動く。
  - 2026-07-09: host mapping は artwork cache failure を metadata/control failure と分離する実装済み。
- cache cleanup と privacy boundary が documented。
  - 2026-07-09: cache path、ADB/file URI boundary、Android/host の atomic write と PNG completeness validation を bridge protocol reference に記録済み。

### M5: Packaging, operations, and daily-use hardening

Goal: daily use できる起動手順、診断、systemd user service、install guide を整える。

- Android APK build / install 手順を document する。
- host daemon install / systemd user service を用意する。
  - 2026-07-09: `scripts/install-user-service.sh` が current checkout path から systemd user service を生成する。static sample unit は manual inspection 用として残す。
- `doctor` 相当の診断 command を追加する。
- README / guide / reference を project-specific に更新する。
- live verification と fixture verification を分けて記録する。

Exit criteria:

- fresh checkout から build / install / run の手順が追える。
  - 2026-07-09: README / Quickstart / usage guide に build / install / run / verify 手順を記録済み。
- Waydroid 未起動、permission 未許可、transport unavailable の診断が出る。
  - 2026-07-09: `scripts/doctor.py` を追加し、daemon 未起動は WARN、daemon 起動中は full PASS を確認済み。
- README が template 説明ではなく本 project の入口になっている。
  - 2026-07-09: README / Quickstart を project-specific に更新済み。

### M6: Restart, absent-session, and MPRIS consumer compatibility hardening

Goal: daily-use 中に Waydroid / ADB / Apple Music session が揺れても、GNOME
や third-party MPRIS consumer が stale metadata、固定 position、不完全 artwork
を受け取り続けない状態にする。

- disruptive Waydroid restart / absent Apple Music session QA を実行する。
- ADB authorization failure と daily-use reauthorization 手順を document する。
- MPRIS `Position` を host 側で同一 track の `Playing` 中だけ projection する。
- Android artwork export と host artwork cache を atomic / complete PNG 前提にする。
- lyrics 表示 extension など、MPRIS polling consumer への現在の boundary を document する。

Exit criteria:

- Waydroid stop 中に MPRIS が stale `Playing` を残さない。
  - 2026-07-09: disruptive QA で `before_stop Playing -> during_stop Stopped` を確認済み。
- Apple Music session absent 時に command が成功扱いにならない。
  - 2026-07-09: restart 後の absent-session で `Stopped`、`CanControl=false`、`playerctl play-pause` exit 1 を確認済み。
- MPRIS `Position` が再生中に進み、pause / missing session で進み続けない。
  - 2026-07-09: unit test と live `busctl ... Position` の連続読みで確認済み。
- Published artwork が host-readable かつ complete PNG であり、truncated cache が再公開されない。
  - 2026-07-09: invalid prior cache を Android source から置換し、host cache と Dynamic Music Pill cache の IEND complete を確認済み。
- Bridge が lyrics provider そのものではないことが user-facing docs に残る。
  - 2026-07-09: usage guide の Current Limitations に記録済み。

## QA Plan

- QA document: `_docs/qa/Core/waydroid-mpris-bridge/test-plan.md`
- Risk level: High
- Test strategy:
  - Unit: protocol schema, metadata normalization, MPRIS state mapping,
    MPRIS position projection, stale session clearing, artwork cache validation.
  - Integration: host daemon fixture input to MPRIS query; command schema to
    Android companion command handler.
  - E2E: Waydroid + Apple Music + GNOME / `playerctl` manual QA.
  - Manual QA: notification listener permission, media key behavior, artwork
    visibility, disconnect/reconnect behavior.
  - Validator / static check: `scripts/check-docs.sh`, Android probe build,
    host unit tests, Python compile checks, generated systemd user service
    verification.
  - Security / privacy review: notification listener scope, local-only
    transport, stale command target, artwork cache.

## Deployment / Rollout

Development should roll out in order: M0 -> M1 -> M2 -> M3 -> M4 -> M5 -> M6.
M0-M6 now have an ADB-backed live path, artwork cache, projected MPRIS
position, project README, usage guide, doctor command, generated user-service
helper, static sample unit, disruptive restart QA, and absent-session QA in this
repo.

The current usable checkpoint is M6: metadata, playback controls, position,
artwork, daily-use entrypoints, restart/absent-session hardening, and
third-party MPRIS consumer compatibility hardening are verified for the current
local setup.
