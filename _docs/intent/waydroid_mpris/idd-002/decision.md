---
title: 公開ファイルを開発記録から独立させる — 設計判断
status: active
intent_schema: 3
created_at: 2026-09-23
updated_at: 2026-09-23
references:
  - "_docs/qa/waydroid_mpris/idd-002/qa.md"
  - "_docs/reference/waydroid_mpris/idd-002/reference.md"
related_issues:
  - 1
related_prs: []
---

# 公開ファイルを開発記録から独立させる — 設計判断

## Context

開発記録 (`_docs/`, `_evals/`, `scripts/` 配下の documentation validators, `.agents/` / `.claude/` / `.codex/`) は
この repository から移出される。一方、public files はまだそれらを link したり実行したりしている。
下調べで洗い出した現状は次のとおり。

- `AGENTS.md`: documentation standards への 3 link, docs-inventory / docs-template-migration /
  qa-review の skill 規則, QA standard と QA test-plan 規則, intent comment 規則, security standard,
  root Markdown 規則, `./scripts/check-docs.sh` コマンドが records に依存する。
- `README.md`: verification record 2 link を含む段落, `_docs/guide/Core/waydroid-mpris-bridge/usage.md`
  への link, Development Checks の `check-docs.sh` と docs workflow 段落が依存する。
- `QUICKSTART.md`: §1 の usage guide 言及, §4 の「separate PARTIAL verification」文言, §6 の
  docs 検査 / skills / template 節が依存する。
- `.github/workflows/docs-ci.yml`: lint job の markdownlint globs が `_docs` / `_evals` / `TODO.md` を
  含み、Deno で `check-docs.sh` を実行している。
- usage guide 本体 (`_docs/guide/Core/waydroid-mpris-bridge/usage.md`) は user-facing だが records 配下にあり、
  frontmatter と本文が `_docs/qa/...` と `Core-Test-17` を参照している。
- 画像 `assets/adb-authorization-timeout-setting.png` が usage guide と同じ directory にある。

下調べで判明した構造的な衝突が 1 件ある。本 lane の成果物 3 file
(`_docs/intent/waydroid_mpris/idd-002/decision.md`, `_docs/qa/waydroid_mpris/idd-002/qa.md`,
`_docs/reference/waydroid_mpris/idd-002/reference.md`) は、この repo の現行 validator
(template v1.0.0) の規則に合わない。area 名 `waydroid_mpris` の underscore が path 正規表現を破り、
`qa.md` という file 名と `qa_schema: 5` も現行の `validate-intent.mjs` / `validate-qa.mjs` /
`validate-doc-links.mjs` に拒否される。そのため records 検査 (`scripts/check-docs.sh`) が赤になる。
docs CI は DEC-32 が validator step を削除するため、この件では赤にならない。
下調べ中の質問回答: q1 = 赤を許容し validator には触らない。validators 自体も records として
移出されるので、赤は records 移出までの期間だけ許容する。

## Decisions

### DEC-21: 変更対象は公開面の記述と CI lint だけにする

- **What**: host / android / tests / fixtures / packaging と runtime 系 scripts には触れない。変更は
  `AGENTS.md` / `README.md` / `QUICKSTART.md` / 新設 `docs/` / `.github/workflows/docs-ci.yml` と、
  移動で切れる records 参照の最小更新 (DEC-33) に限る。
- **Why**: lane は docs と CI lint の整理が目的で、runtime 挙動の変更は明示的に禁止されている。
  触る範囲を先に固定すると、検証を public 側 4 check (unittest / py_compile / shell syntax /
  install dry-run) に絞れる。
- **Change freedom**: 記述の文言は自由。runtime code への diff が 0 であることだけが不変。
- **Anchors**: `README.md`, `QUICKSTART.md`, `AGENTS.md`, `docs/`, `.github/workflows/docs-ci.yml`

### DEC-22: AGENTS.md は運用原則とコマンドだけを残す

- **What**: documentation guidelines / documentation operations への link, docs-inventory /
  docs-template-migration / qa-review の skill 規則, QA standard への従属, Size >= M / Risk >= Medium
  の QA test-plan・verification 規則, `// intent: DEC-00X` の comment 規則, security standard への
  従属, root Markdown / `_evals/prompts` の規則,「Docs checks: `./scripts/check-docs.sh`」の行を削除
  する。残すのは日本語での会話, 日付確認, tool 優先, 現状参照の原則と、records を参照しない Project
  Commands である。編集後は `AGENTS.override.md` 上段の embed を新しい AGENTS.md と一致させる。
- **Why**: AGENTS.md は public guidance であり、records 移出後に `_docs` や skill への参照が残ると
  すべて link 切れになる。原則と commands は repo に残るものだけを対象にして成立する。
  `AGENTS.override.md` の embed は workspace が読む規範の写しで、再生成 tooling が idd init にしか
  無いため、AGENTS.md の編集に合わせて手で更新する。
- **Change freedom**: 残す原則の文言と並び順は自由。参照先が移出後も repo に残ることだけが不変。
- **Anchors**: `AGENTS.md`, `AGENTS.override.md`

### DEC-23: 恒久削除の禁止は但し書きを外して残す

- **What**: 「`git rm` や `rm` などの恒久削除は禁止」を残す。「archive checklist を満たす一時
  ドキュメントの移送に限り `mv` を許可」の但し書きは外す。
- **Why**: 恒久削除の禁止は records に依存しない agent 安全の運用原則で、records 移出後も成立する。
  但し書きは records workflow の規則で、移出後に実行できなくなる。
- **Change freedom**: 但し書きを一般の文言に置き換えるのは自由。削除前に user へ提案を待つ規則として
  成立することだけが不変。
- **Anchors**: `AGENTS.md`

### DEC-24: usage guide と画像は docs/ へ移す

- **What**: `mkdir -p docs/assets` してから、`_docs/guide/Core/waydroid-mpris-bridge/usage.md` を
  `docs/usage.md` に、同 directory の `assets/adb-authorization-timeout-setting.png` を
  `docs/assets/` に `git mv` で移す。`git mv` は移動先 directory が無いと失敗するため、作成を先に行う。
- **Why**: usage guide は user-facing だが `_docs` 配下は records として移出される。public の置き場に
  移さないと records 移出で一緒に消える。
- **Change freedom**: `docs/` 内の構成と frontmatter の扱いは自由。本文の内容と画像への相対参照が
  壊れないことだけが不変。
- **Anchors**: `docs/usage.md`, `docs/assets/adb-authorization-timeout-setting.png`, `README.md`

### DEC-25: docs/usage.md から records への言及を外す

- **What**: records の frontmatter (references 一式) を外す。本文の
  `_docs/qa/Core/waydroid-adb-auto-recovery/verification.md` への言及と `Core-Test-17` の記述を、
  disruptive な実機検証が未実施で実行には明示的な承認が要る、という平文に置き換える。
- **Why**: records の path は移出後に存在しなくなる。検証状況という事実は user に関係するが、
  記録の所在は user に関係しない。
- **Change freedom**: 置き換えの文言は自由。records の path と task ID が出ないことだけが不変。
- **Anchors**: `docs/usage.md`

### DEC-26: QUICKSTART の検証文言は平文に置き換える

- **What**: §4 の「Automatic recovery ... has separate PARTIAL verification」を records を参照しない
  文言に置き換える。§1 の「the usage guide's "ADB authorization timeout" section」に `docs/usage.md`
  への link を足す。
- **Why**: 「PARTIAL verification」は records の verdict を指す内部語で、移出後に参照先がなくなる。
  §1 の言及は guide の移動後も置き場所へ誘導できる必要がある。
- **Change freedom**: 文言と link の形式は自由。初期セットアップの再現手順が変わらないことだけが不変。
- **Anchors**: `QUICKSTART.md`

### DEC-27: README の verification record 段落は削除する

- **What**: Current Status 節の verification record 2 link を含む段落を削除する。直前の bullet list
  (Live metadata / Controls / Artwork / ...) は残す。
- **Why**: この段落の役割は records への案内だけなので、link を外すと残す意味がなくなる。現状の要約は
  bullet list のみで読める。
- **Change freedom**: 段落の代わりに records を参照しない 1 文を足すのは自由。records への link が
  残らないことだけが不変。
- **Anchors**: `README.md`

### DEC-28: README の guide 参照は docs/usage.md に向ける

- **What**: Diagnostics 節末尾の usage guide link を `docs/usage.md` に向ける。§Run / Requirements の
  「the usage guide」言及も `docs/usage.md` を指す文言に揃える。
- **Why**: DEC-24 で guide が移動するため、旧 path の link は移動と同時に link 切れになる。
- **Change freedom**: link の書式 (inline / reference) は自由。`docs/usage.md` へ到達できることだけが
  不変。
- **Anchors**: `README.md`

### DEC-29: README の Development Checks から docs 検査を外す

- **What**: `./scripts/check-docs.sh` の行と、docs workflow / docs-inventory / docs-template-migration /
  `docs-template.lock.json` / `DD_SCOPE_BASE` を含む段落を削除する。unittest / py_compile / `bash -n` /
  install dry-run / Android build / `git diff --check` は残す。
- **Why**: `check-docs.sh` は records script で、移出後に README から実行できなくなる。public file が
  案内する検査は repo に残るものだけに限るべきだからである。
- **Change freedom**: 残す検査の並びと説明の詳細は自由。案内する検査が移出後も実行できることだけが不変。
- **Anchors**: `README.md`

### DEC-30: QUICKSTART から docs workflow の説明を外す

- **What**: §6 から `./scripts/check-docs.sh` の行, docs-inventory / implementation-prep / qa-review の
  説明, 「Template の継続更新」節 (`docs-template.lock.json` / docs-template-migration / `DD_SCOPE_BASE`)
  を削除する。unittest の command block は残す。
- **Why**: これらの説明はすべて records workflow であり、移出後に手順として成立しない。unittest は
  repo に残る検査なので QUICKSTART の読者にもそのまま使える。
- **Change freedom**: unittest block を残すか README の Development Checks への誘導に置き換えるかは
  自由。records workflow の記述が残らないことだけが不変。
- **Anchors**: `QUICKSTART.md`

### DEC-31: docs CI の markdownlint は public markdown に限る

- **What**: lint job の markdownlint globs を `README.md` / `AGENTS.md` / `QUICKSTART.md` /
  `docs/**/*.md` にする。`_docs/**/*.md` / `_evals/**/*.md` / `TODO.md` と 2 つの除外行を外す。
- **Why**: `_docs` / `_evals` / `TODO.md` は records 側で、移出後に glob が空の directory を走査する
  だけになる。public markdown だけが lint の意味を持つ。
- **Change freedom**: globs の書き方は自由。public markdown が lint 対象から漏れないことだけが不変。
- **Anchors**: `.github/workflows/docs-ci.yml`

### DEC-32: docs CI から documentation validator を外す

- **What**: lint job から「Setup Deno」と「Run documentation validators」(`./scripts/check-docs.sh`) の
  step を削除する。`fetch-depth: 0` は validator の diff scope 用なので `1` に戻してよい。runtime job は
  変更しない。
- **Why**: validator scripts は records で、移出後に CI から実行できなくなる。workflow が赤になる前に
  呼び出しを外す。
- **Change freedom**: `fetch-depth` 等の同時整理は自由。runtime job が変わらないことだけが不変。
- **Anchors**: `.github/workflows/docs-ci.yml`

### DEC-33: 移動で切れる records 参照は最小限更新する

- **What**: `_docs/plan/Core/waydroid-adb-auto-recovery/plan.md` の frontmatter reference から
  `_docs/guide/Core/waydroid-mpris-bridge/usage.md` を削除する。他の records 側の手入れは本 lane
  ではしない。
- **Why**: usage guide の移動で records 側の frontmatter reference が 1 件だけ切れる。放置すると
  records 検証が移出までの間ずっとこの件で赤になる。差し替えは選ばない。doc-links validator は
  `docs/` を root 相対として解決しないため、`docs/usage.md` への差し替えは plan.md の directory
  相対の壊れた参照になるからである。
- **Change freedom**: 削除の形式は自由。参照を残さないことと、差し替えないことだけが不変。
- **Anchors**: `_docs/plan/Core/waydroid-adb-auto-recovery/plan.md`

### DEC-34: validator との非互換は本 lane では解消しない

- **What**: 本 lane の成果物 3 file (underscore area `waydroid_mpris`, `qa.md`, `qa_schema: 5`) が
  現行 validator に拒否される件は、本 lane では解消しない。`scripts/` の validators には触らず、
  records 検査 (`check-docs.sh`) の赤は validator を入れ替えるまで許容する (質問 q1 の回答)。
- **Why**: 記録と validator は公開側から外れるが、work 側には残り、records 検査はそこで走り続ける。
  非互換の原因は、導入時に旧 template の validator を残したことにあり、本 lane の範囲 (公開面の記述)
  の外にある。validator の入れ替えは別の作業として扱う。records 検査は必須ではなく提出を止めない。
  docs CI は DEC-32 が validator step を削除するため影響を受けず、public 側の検査にも影響しない。
- **Change freedom**: 赤の示し方 (PR description 等での注記) は自由。validators への変更が 0 である
  ことだけが不変。
- **Anchors**: `scripts/validate-intent.mjs`, `scripts/validate-qa.mjs`, `scripts/validate-doc-links.mjs`

## Consequences / Impact

- public files から records への参照が消え、`README.md` / `QUICKSTART.md` / `AGENTS.md` は移出後も
  すべての link と command が有効になる。
- usage guide と画像が `docs/` に移り、`_docs/guide/` 配下からは消える。guide は repo の規約上
  archive しない恒久記録だが、本 lane では移動 (移出) として扱い、git 履歴に残す。
- docs CI の lint job が public markdown の lint だけになり、documentation validator の実行は
  workflow から消える。
- 本 lane の成果物が現行 validator に拒否されるため、records 検査 (`check-docs.sh`) は records
  移出までの間、この件で赤くなる。docs CI は DEC-32 が validator step を削除するため影響しない。
  本 lane では validators に触らない (質問 q1 の回答)。
- AGENTS.md から QA / security / intent comment の規則が消えるため、public 側だけを見る
  contributor はそれらの規則を知る手段を失う。規則の正典は records の移出先にある。

## Quality Implications

- 利用者の手順 (`README.md` / `QUICKSTART.md` / `docs/usage.md`) について、records 移出後に link と
  command がすべて有効であること。
- runtime 挙動が変わらないこと。public 側 4 check (unittest / py_compile / shell syntax /
  install dry-run) が実装前後で緑のままであること。
- docs CI の lint 対象に public markdown が漏れないこと。
- `docs/usage.md` の画像参照が移動後も切れていないこと。
- `.markdownlint.jsonc` の `ignores` (`_docs/archives/**`) と `.gitattributes` の
  `scripts/*.mjs linguist-vendored` は INV-011 の対象外 (link でも手順案内でもない dead 設定) で、
  records 移出時の follow-up として削除する。
- 確認観点は `_docs/qa/waydroid_mpris/idd-002/qa.md` の Checks に対応付ける。

## Intent-derived Invariants

- INV-008 (from DEC-21): 本 lane の diff は runtime code (host / android / tests / fixtures / packaging / runtime scripts) に触れない
- INV-009 (from DEC-22): AGENTS.md の参照先はすべて records 移出後も repo に残る
- INV-010 (from DEC-24): user-facing の usage guide とその画像は docs/ 配下にだけ置く
- INV-011 (from DEC-25): public files は records の path と task ID を link と手順案内に使わない
- INV-012 (from DEC-31): docs CI の markdownlint 対象は public markdown に限る
- INV-013 (from DEC-32): docs CI は records の script を実行しない

## Rollback / Follow-ups

- Rollback は対象 file の差し戻しと `docs/` から `_docs/guide/` への移し戻しで完結する。runtime への
  影響はない。
- `.markdownlint.jsonc` の `ignores` (`_docs/archives/**`) と `.gitattributes` の
  `scripts/*.mjs linguist-vendored` は records 移出後に無効になる。本 lane の scope 外とし、
  移出時の削除に含める。
- `scripts/agent-workflow-hook.mjs` の docs 判定は `docs/` prefix を含まず、`docs/usage.md` の編集が
  docs stop を発火しない。hook は records 側の optional な増幅なので本 lane では触らず、records
  移出に合わせて扱う。
- records 移出の作業で `_docs` / `_evals` / `.agents` / `.claude` / `.codex` / validators / overlay
  系 file を移出し、docs CI と `overlay.manifest` を最終化する。これにより本 lane 成果物由来の
  records 検査の赤も解消される (質問 q1 の回答)。
