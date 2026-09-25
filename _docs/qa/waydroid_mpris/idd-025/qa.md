---
title: "QA: MPRIS Position の opt-in lead offset"
status: active
qa_schema: 5
qa_status: partial
risk: High
created_at: 2026-09-25
updated_at: 2026-09-25
references:
  - "_docs/intent/waydroid_mpris/idd-025/decision.md"
  - "_docs/reference/waydroid_mpris/idd-025/reference.md"
related_issues:
  - 9
related_prs: []
---

# QA: MPRIS Position の opt-in lead offset

risk は High とする。変更先に `scripts/` を含み、`validate-intent-delta.ts` のパス下限が
High を要求するためである。DEC 新設と risk High により R2 再構成テストが発動する。

## Acceptance Criteria

- AC-001: 既定 0 の公開 Position が変更前と同じ値になる
- AC-002: lead を指定すると公開 Position がその分だけ前へずれる
- AC-003: lead 適用後の公開値が 0 と曲の長さに収まる
- AC-004: 曲が無いとき公開値は lead に関係なく 0 である
- AC-005: 負の lead で公開値が後ろへずれ 0 で止まる
- AC-006: 一時停止中も公開値に lead が加わる
- AC-007: Seek で Android に送る位置が lead の有無で変わらない
- AC-008: clamp 外の公開値を書き戻すと実位置へ seek する
- AC-009: 起動スクリプトが --position-lead-ms を整数で受ける
- AC-010: installer は lead が 0 以外のときだけ unit に書く
- AC-011: installer は整数でない lead をエラーで拒む
- AC-012: 既定の install dry-run 出力が変更前と同一である
- AC-013: docs/usage.md に lead の使い方と副作用が書かれている
- AC-014: コードと test に governance 注記が残らない
- AC-015: 新しい test は外部 command を呼ばずに discover で通る
- AC-016: clamp された公開値を書き戻しても前へ seek しない
- AC-017: CLI の lead が µs に換算されて projector に届く
- AC-018: 新しい test file が CI と文書の unittest 行に載る

## Checks

| ID | Source | Requirement / Invariant | Check Type | Command / File | Status |
| --- | --- | --- | --- | --- | --- |
| AC-001 | DEC-122, INV-044 | 既定 0 で公開値が `position_us()` と一致 | command | `tests/test_position_projection.py` の既定 lead の test | verified |
| AC-002 | DEC-121 | 公開値が lead の分だけ前へずれる | command | `tests/test_position_projection.py` と `tests/test_mpris_position_lead.py` の `Get("Position")` 差分の test | verified |
| AC-003 | DEC-121, INV-043 | lead 適用後の clamp | command | `tests/test_position_projection.py` の曲の長さ付近で大きな lead を与える test | verified |
| AC-004 | DEC-121 | 曲が無いときの公開値 0 | command | `tests/test_position_projection.py` の `update(None)` の test | verified |
| AC-005 | DEC-123, INV-043 | 負の lead の後退と下限 0 | command | `tests/test_position_projection.py` に足す負の lead の test (曲頭付近で 0 に止まる) | verified |
| AC-006 | DEC-123 | 一時停止中の lead 適用 | command | `tests/test_position_projection.py` に足す Paused の session での test | verified |
| AC-007 | DEC-121, INV-041 | Seek の送出位置が lead に依らない | command | `tests/test_mpris_position_lead.py` の lead 有無で `Seek` の送出を比べる test | verified |
| AC-008 | DEC-121, DEC-123, INV-042 | 公開値の書き戻しで前進しない | command | `tests/test_mpris_position_lead.py` の `SetPosition` 往復の test | verified |
| AC-009 | DEC-122 | CLI 引数の受理と既定 0 | command | `/usr/bin/python3 scripts/run-host-mpris-live.py --help` に `--position-lead-ms` が出ること。`--position-lead-ms abc` が argparse エラーになること | verified |
| AC-010 | DEC-122, DEC-123 | 非 0 のときだけ `ExecStart` に付く | command | `PYTHON=/usr/bin/python3 ./scripts/install-user-service.sh --dry-run --position-lead-ms 485` と `--position-lead-ms=-100` の `ExecStart` 目視 | verified |
| AC-011 | DEC-122 | 整数でない値の拒否 | command | `PYTHON=/usr/bin/python3 ./scripts/install-user-service.sh --dry-run --position-lead-ms 1.5` が非 0 で終わり unit を出さないこと | verified |
| AC-012 | DEC-122, INV-044 | 既定の install 結果の非変化 | command | 実装前後の `PYTHON=/usr/bin/python3 ./scripts/install-user-service.sh --dry-run` の出力 diff | verified |
| AC-013 | DEC-124 | 利用者向け説明 | diff-review | `docs/usage.md` の diff 目視 (起動例、installer 例、既定 0、他 client にも効くこと) | verified |
| AC-014 | DEC-124 | governance 注記と旧 layout 記録の不在 | command | `grep -n -e 'intent:' -e 'Covers AC' -e 'Covers INV' host/waydroid_mpris/position.py host/waydroid_mpris/mpris_service.py scripts/run-host-mpris-live.py scripts/install-user-service.sh tests/test_position_projection.py tests/test_mpris_position_lead.py` が 0 件であること (実装前の HEAD c8c471f で 0 件)。`_docs/intent/Core/mpris-position-lead`、`_docs/qa/Core/mpris-position-lead`、`_docs/intent/Core/conventions` が存在しないこと | verified |
| AC-015 | DEC-125, INV-045 | 外部 command を使わない unit test | command | `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py'` と test 本体の目視 | verified |
| AC-016 | DEC-121, DEC-123, INV-042 | clamp 境界の書き戻し | command | `tests/test_mpris_position_lead.py` に足す 2 test。一時停止・実位置 100 ms・lead -400 ms で公開値 0 を書き戻すと `seekTo` 0 が送られること。曲の長さの 100 ms 手前・lead 400 ms で公開値を書き戻すと送出が実位置以下であること | verified |
| AC-017 | DEC-122, DEC-125, INV-046 | CLI から projector までの配線 | command | `tests/test_mpris_position_lead.py` に足す 3 test。`main()` が `serve_live` に `position_lead_ms=485` を渡すこと。`serve_live` が `WaydroidMprisObject` に lead を渡すこと。`__init__` 経由の bridge で公開値の差が lead × 1000 µs になること | verified |
| AC-018 | DEC-124 | test の列挙への登録 | command | `.github/workflows/docs-ci.yml` の `Run host unit tests`、`README.md`、`QUICKSTART.md` の unittest 行に `tests/test_mpris_position_lead.py` があること。列挙形の実行と `unittest discover` の test 数が一致すること | verified |
| AGENT-001 | DEC-125, INV-045 | agent misbehavior: test が session bus・adb・waydroid を使わない | diff-review | `tests/test_mpris_position_lead.py` が `object.__new__` で bus 登録を避け、`command_handler` を記録関数に差し替えていることの目視 | verified |
| ROLLBACK-001 | DEC-122 | rollback / recovery: lead 0 か差し戻しで変更前の挙動に戻る | diff-review | AC-012 の diff と、差し戻し時に `--force` で unit を再生成する手順の記録 | verified |
| R2-001 | DEC-121, DEC-122, DEC-123, DEC-124, DEC-125 | 記録のみから設計判断を再構成できる | diff-review | Issue lane の S3 で実施する R2 タスク (DEC 新設かつ risk High で発動) | planned |

public の 4 check (unittest / py_compile / shell syntax / install dry-run) は、上表とは別に
実装後の round で全件の結果を記録する。required の unittest check は `discover` だが、CI は
test file を列挙して走らせるので、AC-018 で両者の test 数を突き合わせる。

## Rounds

<!-- 追記専用。実装後に Round を追記する。 -->

### Round 1 (2026-09-25)

- **Intent Delta**: 新設: DEC-121, DEC-122, DEC-123, DEC-124, DEC-125
- **R2**: PENDING（Issue lane の S3 で実施）
- **Verdict**: PARTIAL (R2 再構成テストが未実施。残リスクは本 round に記録)

実施内容:

- `PositionProjector` に `lead_us` と読み出し口 `published_position_us()` を足した (DEC-121 / DEC-123)。`position_us()` は seek の基準のままで lead を含めず、公開値だけを `0` と曲の長さに clamp する。曲が無いときは lead に関係なく `0` を返す (AC-001 / AC-003 / AC-004 / AC-005)。
- `WaydroidMprisObject` に `position_lead_ms` を足し、ms から µs へ換算して projector に入れた (DEC-122 / INV-046)。`Position` だけを `published_position_us()` から作り、`Seek` は従来どおり `position_us()` を基準にする (AC-002 / AC-007 / AC-017)。
- `SetPosition` は受け取った位置が `0` 以下なら lead に関係なく `0` を送り、正の値では lead を引いてから送る (DEC-121)。負の lead の曲頭で公開値 `0` を書き戻しても前へ seek せず、曲の長さに clamp された値の書き戻しも実位置より後ろへ seek する (AC-008 / AC-016 / INV-041 / INV-042)。
- lead は再生状態で分岐せず、一時停止中も公開値に加える (DEC-123 / AC-006)。
- `run-host-mpris-live.py` に `--position-lead-ms` (int、既定 0) を足し、`serve_live` 経由で bridge へ渡した (DEC-122 / AC-009)。
- `install-user-service.sh` に `--position-lead-ms` を足した (DEC-122)。`^-?[0-9]+$` で整数を検査し、`0` 以外のときだけ `ExecStart` に書く (AC-010 / AC-011 / AC-012 / INV-044)。
- `tests/test_position_projection.py` に lead の 7 test を足し、`tests/test_mpris_position_lead.py` を新設した (DEC-125)。bridge は `object.__new__` で bus に登録せず作り、`command_handler` を記録関数へ差し替え、clock を固定する (AGENT-001)。配線は `main()` / `serve_live` / `__init__` の 3 test で検査する (AC-017)。
- `docs/usage.md` に起動例・installer 例・既定 0・他 client への副作用を書いた (DEC-124 / AC-013)。`README.md` / `QUICKSTART.md` / `.github/workflows/docs-ci.yml` の unittest 列挙へ `tests/test_mpris_position_lead.py` を足した (AC-018)。
- 検証: AC-001〜AC-008 / AC-016 / AC-017 は unit test で確認した。AC-009 は `--help` の表示と `--position-lead-ms abc` の rc=2、AC-010 は lead `485` / `-100` の `ExecStart`、AC-011 は `1.5` が rc=1 で unit を出さないこと、AC-012 は既定 dry-run の出力が実装前 (`/tmp/idd025/dryrun-before.txt`) と byte-identical であることを diff で確認した。AC-014 は対象 6 file の grep が 0 件で、旧 layout の 3 path が存在しないことを確認した。AC-015 は外部 command を呼ばず `discover` が緑であることを確認した。AC-018 は列挙形の実行と `discover` がどちらも 72 tests で一致することを確認した。
- public 4 check (unittest 72 tests / py_compile / shell syntax / install dry-run) は緑である。
- records 検査: `check-docs.sh` は既知の TODO.md 赤 (Core-Test-17) のみで、本 lane の記録 3 file と変更は緑である。
- agent misbehavior の確認: 新 test は session bus へ接続せず、adb / waydroid / playerctl を実行しない。`serve_live` と `__init__` の test は `dbus` と依存クラスを `unittest.mock` で差し替える (AGENT-001 / INV-045)。
- rollback / recovery の確認: 変更はコード 4 file・test 2 file・docs 1 file・列挙 3 file に閉じ、runtime state / migration / data を持たない。lead を `0` に戻すか差し戻すと、AC-012 の byte-identical な既定出力と実装前の公開値に戻る。`--position-lead-ms` 付きで install 済みの unit は `--force` で再生成する (ROLLBACK-001)。
- review fix (1 巡目): F-1 は Verdict 行の `PARTIAL` の直後が全角括弧で、`validate-qa.ts` が `PARTIAL（R2` を Verdict として読み、`check-docs.sh` の qa 段が赤になっていた。半角空白と半角括弧に直し、本 round の「records 検査は緑」の記述を実際の結果に合わせた。F-2 は `SetPosition` の写像が公開値の書き戻しと clamp 両端しか検査しておらず、前方への絶対 seek の退行を検出できなかった。lead 非 0 で実位置より 5 秒前方の絶対位置を渡す test を足し、`requested − lead` の位置が送られ、実位置で頭打ちにならないことを検査した (AC-008)。F-4 は本 lane の規範に従い TODO を立てず、理由を result の side_findings に記録した。

残リスク:

- R2 再構成テストが未実施である。Issue lane の S3 で隔離して行う。
- 常駐 service の再起動と live の `Position` 実測は本 lane の scope 外に残る。
