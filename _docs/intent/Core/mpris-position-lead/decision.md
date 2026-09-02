---
title: MPRIS position lead offset
status: active
intent_schema: 3
draft_status: n/a
created_at: 2026-09-02
updated_at: 2026-09-02
references:
  - "_docs/qa/Core/mpris-position-lead/qa.md"
  - "_docs/intent/Core/waydroid-mpris-bridge/decision.md"
related_issues: []
related_prs: []
---

# MPRIS position lead offset

## Context

歌詞同期クライアント (GNOME 拡張 `dynamic-music-pill`) で、表示が体感で遅れるという申告があった。

bridge 側の位置精度を live 実測した結果、公開している `Position` は真の再生位置に対して
+11ms しかずれていなかった (Android probe の `updateTimeMs` を真値として突き合わせ、
アンカーから 278 秒外挿した時点での測定)。体感遅延の由来は bridge ではなく、

- 消費側の描画パイプライン (歌詞 tick 200ms 粒度、行のフェードイン時間)
- LRC のタイムスタンプが「発声が始まる瞬間」を指すという意味論

の側にある。そして当該クライアントには歌詞オフセットの設定が存在しない。つまり利用者が
時間軸を前へずらす手段は、bridge が公開する `Position` を動かすこと以外にない。

## Decisions

### DEC-007: 公開 Position にだけ効く lead offset を、既定無効の調整点として持つ

- **What**: MPRIS `Position` として読み出される値に、host 側で固定オフセット (lead) を
  加算できるようにする。既定は 0 で、無指定時の観測可能な挙動は導入前と同一である。
  加算は「D-Bus へ値を出す境界」でのみ行い、Android へ送る seek 位置には持ち込まない。
  逆向きに、`SetPosition` で受け取った絶対位置からは lead を差し引く。
- **Why**: 遅延の発生源は消費側にあるが、その消費側に補正点が無い。補正点を持てるのは
  bridge だけなので、ここに置く。一方 MPRIS の `Position` は本来「真の再生位置」であり、
  ずらすことは仕様からの意図的な逸脱である。既定を 0 に固定することで、逸脱を
  「利用者が明示的に要求したときにだけ発生する状態」に閉じ込め、bridge の既定の正しさと
  個人環境の可調整性を両立させる。`SetPosition` で lead を打ち消すのは、公開値を読んで
  そのまま書き戻す client が呼び出しのたびに再生位置を前方へ累積させるのを防ぐためである。
- **Change freedom**: オフセットの単位・許容範囲・設定経路 (CLI / systemd unit / 環境変数)、
  再生停止中に適用するかどうか、負値を許すかどうか。値そのものは体感に基づく調整対象であり、
  契約ではない。消費側にオフセット設定が実装されたら、この調整点自体を撤去してよい。
- **Why not**: `PositionProjector` の内部状態に lead を持たせる案。`Seek` は現在位置の取得に
  同じ projector を使うため、シークのたびに lead 分が実際の再生位置へ焼き込まれ、
  操作を繰り返すほど前方へずれていく。lead は表示のための値であってシークの基準ではない、
  という区別が実装から失われる。
- **Why not**: Android probe 側 (`positionMs`) で加算する案。probe は観測値であり、そこへ
  host の表示都合を混ぜると `updateTimeMs` との整合が崩れ、今回行ったような
  「遅延源が bridge か消費側か」の切り分けが以後できなくなる。

## Consequences / Impact

- 同一 bus を購読する他クライアント (例: Discord rich presence) の経過時間表示も同じだけずれる。
  lead は player 単位の設定であり、client ごとの出し分けはできない。
- 非 0 の lead を設定した状態では、公開 `Position` は MPRIS 仕様の意味での真値ではなくなる。
- 既定 0 のため、設定しない利用者に対する挙動変化はない。

## Quality Implications

- lead が Android へ送られる seek 位置へ漏れないこと。漏れると再生位置そのものが操作のたびに
  前方へドリフトし、可逆でない副作用になる。
- 0 と duration による clamp が lead 適用後にも成立すること。負値方向へ突き抜けた位置や
  duration 超過の位置を公開しないこと。
- 既定値で既存の projection 挙動が変化しないこと (回帰の主対象)。

## Intent-derived Invariants

- INV-008 (from DEC-007): lead offset は D-Bus へ公開する `Position` にのみ作用し、
  Android companion へ送出される seek 位置に作用してはならない。

## Rollback / Follow-ups

- Rollback: lead を 0 に戻す (または引数を外す) だけで導入前の挙動へ戻る。永続的な状態変更を伴わない。
- Follow-up: 消費側クライアントに歌詞オフセット設定が実装された場合、DEC-007 の Revisit 条件として
  この調整点の撤去を検討する。
