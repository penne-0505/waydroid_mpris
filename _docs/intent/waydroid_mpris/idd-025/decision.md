---
title: "MPRIS Position の opt-in lead offset — 設計判断"
status: active
intent_schema: 3
created_at: 2026-09-25
updated_at: 2026-09-25
references:
  - "_docs/qa/waydroid_mpris/idd-025/qa.md"
  - "_docs/reference/waydroid_mpris/idd-025/reference.md"
related_issues:
  - 9
related_prs: []
---

# MPRIS Position の opt-in lead offset — 設計判断

## Context

歌詞同期 client (GNOME 拡張 `dynamic-music-pill`) で歌詞が体感で遅れる。live 実測では、
bridge が公開する `Position` と真の再生位置のずれは約 +11 ms しかない。遅れの出どころは
client 側にある。歌詞の tick は 200 ms 刻みで、行はフェードインし、LRC のタイムスタンプは
発声の始まりを指す。その client には歌詞 offset の設定が無い。利用者が調整できる場所は、
bridge が公開する `Position` だけである。

lane の goal は次のとおりである。

- `run-host-mpris-live.py` と `install-user-service.sh` が `--position-lead-ms` (整数、既定 0) を受け付ける。
- lead は D-Bus に公開する `Position` だけに効く。Android へ送る seek 位置には入らない。
- `SetPosition` は lead を差し引く。
- 既定 0 の観測可能な挙動は現行 `main` と同一である。
- lead 適用後の公開値は 0 と曲の長さの範囲に収まる。
- 外部 command を呼ばない unit test で検査する。
- `docs/usage.md` に option を書く。

下調べで判明した前提は次のとおり。

- 実装は `origin/feat/mpris-position-lead` の commit `4aa08c6` (2026-09-02) に既にある。
  `main` には merge されていない。分岐元 `8308175` 以降、その commit がコードと test で
  触る 6 file は `main` で変わっていない。その部分の差分は現 HEAD に `git apply --check` で当たる。
- その commit は現行規約に合わない箇所を持つ。コードに `# intent: DEC-007` の行があり、
  test に `# Covers AC-xxx` の行がある。設計記録は旧 layout の `_docs/intent/Core/mpris-position-lead/`
  にあり、利用者向け説明は旧 `_docs/guide/Core/waydroid-mpris-bridge/usage.md` に書かれている。
- 常駐の user service は旧ブランチから `--position-lead-ms "485"` 付きで install された。
  現 `main` の `run-host-mpris-live.py` はこの引数を拒否し、journal には
  `unrecognized arguments` と status=2 の終了が記録されている。service は inactive である。
- `Seek` は `PositionProjector.position_us()` を基準に相対位置を計算する。
  `_player_fingerprint` は projector を経由せず probe の生の位置を使う。
- `4aa08c6` の `SetPosition` は `max(0, position - lead)` を送る。負の lead で公開値が 0 に
  clamp されている間にその 0 を書き戻すと、実位置より前へ seek する。一時停止・実位置 100 ms・
  lead -400 ms で `4aa08c6` の projector を動かし、公開値 0、送出 400 ms (+300 ms) を実測した。
  正の lead で曲の長さに clamp された値を書き戻すと、送出は実位置より 300 ms 後ろになり、前へは進まない。
- unit test の実行は 3 か所で test file を列挙している。CI (`.github/workflows/docs-ci.yml` の
  `Run host unit tests`)、`README.md`、`QUICKSTART.md` である。新しい test file はそこに足さないと
  CI で走らない。CI は `python3-dbus` を apt で入れている。

## Decisions

### DEC-121: lead は公開する Position にだけ加える

- **What**: lead を加えるのは、D-Bus の `Position` として読み出す値だけにする。
  projector の基準位置と `position_us()` には lead を入れない。`Seek` は従来どおり
  lead を含まない位置を基準にする。`SetPosition` は受け取った絶対位置から lead を
  差し引いてから Android に送る。ただし受け取った位置が 0 以下なら、lead に関係なく 0 を送る。
  lead を加えた後の公開値は 0 と曲の長さの範囲に収める。
  曲が無いときの公開値は lead に関係なく 0 である。
- **Why**: 遅れの出どころは client 側だが、調整できるのは bridge の公開値しかない。
  lead を projector の内部状態に入れると、`Seek` のたびに lead が実際の再生位置に
  焼き込まれ、操作を重ねるほど前へずれる。`SetPosition` で差し引かないと、公開値を
  読んでそのまま書き戻す client が呼ぶたびに再生位置を lead の分だけ進める。
  Android の probe 側で足す案は、probe の観測値と `updateTimeMs` の整合を崩す。
  そうなると、遅れが bridge 由来か client 由来かを以後切り分けられなくなる。
  以上は旧ブランチ DEC-007 の判断を引き継いだものである。
  受け取った位置が 0 以下のときに 0 を送る規則は plan review の指摘で足した。
  負の lead では曲頭付近の公開値が 0 に張り付く。単純に差し引くと、その 0 の書き戻しが
  |lead| 先へ seek し、再生位置を前へ進める。公開値の 0 は曲頭を表すので、曲頭へ seek する
  のが client の意図に合う。lead が 0 のときは現行の `max(0, position)` と同じ値になる。
  正の lead で曲の長さに張り付いた値の書き戻しは実位置より後ろへ seek するだけで、
  前へは進まないので特別扱いしない。
- **Change freedom**: 公開値を作る読み出し口の名前と形は自由。lead を µs と ms のどちらで
  保持するかも自由。`SetPosition` の送出に曲の長さでの上限を足さない。lead 0 で現行と
  挙動が変わるためである。`Seek` と `SetPosition` が Android に送る値の丸め方
  (µs から ms への切り捨て) は現行のまま変えない。`PropertiesChanged` を出す条件
  (`_player_fingerprint`) は変えない。
- **Anchors**: `host/waydroid_mpris/position.py` (`PositionProjector`)、
  `host/waydroid_mpris/mpris_service.py` (`WaydroidMprisObject.__init__` / `Seek` /
  `SetPosition` / `_player_properties`)

### DEC-122: lead は既定 0 で起動引数から渡す

- **What**: `run-host-mpris-live.py` に `--position-lead-ms` (int、既定 0) を足し、
  `serve_live` を経て `WaydroidMprisObject` に渡す。`install-user-service.sh` にも同名の
  option (`--position-lead-ms MS` と `--position-lead-ms=MS`) を足す。値は整数として
  検査し、整数でなければ unit を書かずにエラーで終わる。unit の `ExecStart` には
  lead が 0 以外のときだけ引数を書く。
- **Why**: MPRIS の `Position` は本来、真の再生位置である。lead は仕様からの意図的な
  逸脱なので、利用者が明示したときだけ起きるようにする。既定の `ExecStart` に引数を
  書かなければ、既定の install 結果が現行 `main` と byte 単位で一致する。
  既に install 済みの unit は `--position-lead-ms "485"` を持つので、同じ引数名を
  受け付ければ再 install なしで起動できるようになる。
- **Change freedom**: help 文言と usage の書き方は自由。環境変数など別の設定経路は
  足さない。fixture daemon (`run-host-mpris-fixture.py`) には lead を足さない。
- **Anchors**: `scripts/run-host-mpris-live.py`、`scripts/install-user-service.sh`、
  `host/waydroid_mpris/mpris_service.py` (`serve_live`)

### DEC-123: 負の lead も受け付け、再生状態に関係なく加える

- **What**: lead は負の整数も受け付ける。負の lead では公開値が実際より後ろになり、
  下限 0 で止まる。lead は再生中・一時停止中・停止中を問わず、曲がある限り公開値に加える。
  `SetPosition` も再生状態に関係なく lead を差し引く。
- **Why**: 0 と曲の長さに収める処理は負の値でも効くので、正負で分岐が要らない。
  旧ブランチのインストーラーも `^-?[0-9]+$` で負の値を許していた (質問 q1 の回答)。
  再生中だけ加えると、再生と一時停止を切り替えるたびに公開値が lead の分だけ跳ぶ。
  常に加えれば、公開値を読んで `SetPosition` に書き戻す往復が状態に関係なく打ち消し合う
  (質問 q2 の回答)。
- **Change freedom**: 許容範囲の上限や下限は設けない。負の値を拒否する検査を足さないこと。
  再生状態による分岐を足さないこと。負の lead の曲頭付近で起きる書き戻しの問題は、
  DEC-121 の「0 以下なら 0 を送る」規則で扱う。
- **Anchors**: `host/waydroid_mpris/position.py` (`PositionProjector`)、
  `scripts/install-user-service.sh`

### DEC-124: 旧ブランチのコードを移し、旧記録と注記は持ち込まない

- **What**: 実装は `4aa08c6` のうち `host/` / `scripts/` / `tests/` の差分を土台にする。
  コードの `# intent: DEC-007` 行と test の `# Covers AC-xxx` 行は外す。旧 layout の
  `_docs/intent/Core/mpris-position-lead/`、`_docs/qa/Core/mpris-position-lead/`、
  `_docs/intent/Core/conventions/decision.md` (candidate DEC-008) は持ち込まない。
  利用者向けの説明は旧 `_docs/guide/` ではなく `docs/usage.md` に書く。
  新しい test file `tests/test_mpris_position_lead.py` は、test file を列挙している
  CI (`.github/workflows/docs-ci.yml`)、`README.md`、`QUICKSTART.md` の unittest 行に足す。
- **Why**: その差分は分岐元から変わっていない 6 file に閉じ、現 HEAD に当たることを
  確かめた。現行規約はコードに DEC / INV / AC / intent を書くことを禁じ、統治対象は
  DEC の Anchors に、test との対応は qa.md の Checks に書く。設計判断は本文書の
  DEC-121〜DEC-123 が引き継ぐ。candidate DEC-008 は area 横断の原則で、本 lane の
  goal の外にある。
  列挙に足さないと、CI では新しい test が走らない (plan review の指摘)。
- **Change freedom**: cherry-pick するか手で書き直すかは自由。結果の diff に旧 layout の
  file と governance 注記が入らないこと。旧ブランチ自体は消さない。
  `AGENTS.md` の Unit checks 行は直さない。既に 3 file 分が欠けており、
  `AGENTS.override.md` の embed と同期が要るので、本 lane の scope 外とする。
- **Anchors**: `host/waydroid_mpris/position.py`、`host/waydroid_mpris/mpris_service.py`、
  `scripts/run-host-mpris-live.py`、`scripts/install-user-service.sh`、
  `tests/test_position_projection.py`、`tests/test_mpris_position_lead.py`、`docs/usage.md`、
  `.github/workflows/docs-ci.yml`、`README.md`、`QUICKSTART.md`

### DEC-125: lead の挙動は外部 command を呼ばない unit test で検査する

- **What**: 公開値のずれ、clamp、曲が無いときの 0、負の lead、一時停止中の lead を
  `tests/test_position_projection.py` で検査する。D-Bus 境界では、`Get("Position")` の差、
  `Seek` が送る位置が lead に依らないこと、公開値を `SetPosition` に書き戻すと実位置に
  seek することを `tests/test_mpris_position_lead.py` で検査する。bridge は
  `object.__new__` で bus に登録せずに作り、`command_handler` は送った値を記録する
  関数に差し替える。時刻は固定した clock で与える。
  この bridge は `__init__` を迂回するので、配線は別の test で検査する。
  `run-host-mpris-live.py` の `main()` は `serve_live` を差し替えて呼び、
  `--position-lead-ms 485` が `position_lead_ms=485` で渡ることを確かめる。
  `serve_live` は bus・adb・mainloop の依存を差し替えて呼び、`WaydroidMprisObject` に
  lead が渡ることを確かめる。`WaydroidMprisObject.__init__` は `dbus.service.BusName` と
  `dbus.service.Object.__init__` を差し替えて呼び、ms の lead が µs で projector に入る
  (公開値の差が lead × 1000 µs になる) ことを確かめる。
- **Why**: goal が外部 command を呼ばない unit test を求めている。旧ブランチの test は
  bus 登録と adb を避ける形を既に持つ。`/usr/bin/python3` で `dbus` 1.4.0 を import できる
  ことを確かめたので、`mpris_service` を import する test も required の unittest check で走る。
  `object.__new__` の bridge だけでは、ms から µs への換算忘れや `serve_live` での転送忘れが
  あっても test が緑のままになる (plan review の指摘)。配線の test は差し替えた依存ではなく、
  引数の受け渡しそのものを見るので、IDD-022 の DEC-043 が避けた「stub を検査する test」には当たらない。
- **Change freedom**: test 名と分割の細かさは自由。session bus への接続と adb / waydroid の
  実行を test に入れないこと。`run-host-mpris-live.py` は file 名に `-` を含むので、
  `importlib` で読み込んでよい。
- **Anchors**: `tests/test_position_projection.py`、`tests/test_mpris_position_lead.py`

## Consequences / Impact

- 非 0 の lead を設定すると、公開 `Position` は MPRIS 仕様の意味での真値ではなくなる。
- lead は player 単位で効く。同じ bus を読む他の client (rich presence 等) の経過時間表示も
  同じだけずれる。client ごとに出し分けることはできない。
- 一時停止中も公開値は lead の分だけずれたままになる。
- `SetPosition` の位置指定は lead の分だけずれた時間軸で解釈される。例外として、0 以下の
  指定は常に曲頭への seek になる。
- 既定 0 の利用者には、公開値・D-Bus 操作・生成される unit のどれにも変化が無い。
- `--position-lead-ms "485"` を持つ既存の unit は、この変更が入った checkout から再び起動できる。

## Quality Implications

- lead が Android へ送る seek 位置に漏れないこと。漏れると操作のたびに再生位置が前へ進み、
  元に戻せない副作用になる。
- lead 適用後も公開値が 0 未満や曲の長さ超過にならないこと。
- clamp された公開値を書き戻しても、再生位置が前へ進まないこと。
- CLI から projector まで lead が ms から µs に換算されて届くこと。
- 既定 0 で既存の projection の挙動と install 結果が変わらないこと (回帰の主対象)。
- 確認観点は `_docs/qa/waydroid_mpris/idd-025/qa.md` の Checks に対応付ける。

## Intent-derived Invariants

- INV-041 (from DEC-121): lead は Android へ送る seek 位置に入らない
- INV-042 (from DEC-121): 公開値を書き戻しても再生位置は前へ進まない
- INV-043 (from DEC-121): 公開値は lead 適用後も 0 と曲の長さに収まる
- INV-044 (from DEC-122): lead が 0 なら公開値と生成 unit は変わらない
- INV-045 (from DEC-125): lead の検査は外部 command を呼ばない
- INV-046 (from DEC-122): CLI の lead は ms のまま projector に µs で届く

## Rollback / Follow-ups

- 利用者側の rollback は、lead を 0 に戻すか引数を外すことで完結する。永続的な状態を持たない。
- コードの rollback は Anchors の file の差し戻しで完結する。その場合、`--position-lead-ms`
  付きで install 済みの unit は再び起動できなくなるので、`--force` で unit を再生成する。
- 常駐 service の再起動は本 lane の作業に含めない。main の checkout に変更が入った後、
  利用者が `systemctl --user restart waydroid-mpris` で戻す。
- client 側に歌詞 offset の設定が実装されたら、この調整点を撤去してよい。
