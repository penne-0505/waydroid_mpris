# Project Task Management Rules

## 0. System Metadata

- **Current Max ID**: `Next ID No: 25` (タスク追加時にインクリメント必須)
- **ID Source of Truth**: このファイルの `Next ID No` 行が、全プロジェクトにおける唯一の ID 発番元である。

## 1. Task Lifecycle (State Machine)

タスクは以下の順序で単方向に遷移する。逆行は原則禁止とする。

### Phase 0: Inbox (Human Write-only)

- **Location**: `## Inbox` セクション
- **Description**: 人間がアイデアや依頼を書き殴る場所。フォーマット不問。ID 未付与。
- **Exit Condition**: LLM が内容を解析し、ID を付与して `Backlog` へ構造化移動する。

### Phase 1: Backlog (Structured)

- **Location**: `## Backlog` セクション
- **Status**: タスクとして認識済みだが、着手準備未完了。
- **Entry Criteria**:
  - ID が一意に採番されている。
  - 必須フィールドがすべて埋まっている。
- **Exit Condition**: `Ready` の要件を満たす。

### Phase 2: Ready (Actionable)

- **Location**: `## Ready` セクション
- **Status**: いつでも着手可能な状態。
- **Entry Criteria**:
  - `Size >= M` の場合、Plan が作成済みである。
  - `Risk >= Medium` の場合、QA 文書が `qa_status: planned` で作成済みである。
  - Dependencies が解決済み、または未解決理由が明確である。
  - Steps が具体的、または Plan / QA への進行管理ポインタとして機能している。
- **Exit Condition**: 作業者がタスクに着手する。

### Phase 3: In Progress

- **Location**: `## In Progress` セクション
- **Status**: 現在実行中。

### Phase 4: Completed

- **Location**: なし。完了タスクは `TODO.md` から削除する。
- **Exit Action**: Acceptance Criteria の達成と、QA round の verdict を確認後に削除する。
- **History**: 完了履歴の正典は QA round (`qa.md` / `maintenance.md`) である。`TODO.md` に Done / Archived セクションは作らない。

## 2. Schema & Validation

各タスクは以下のフィールドを必須とする。

| Field | Type | Constraint / Value Set |
| --- | --- | --- |
| **Title** | `String` | `[Category] Title` 形式。Category は後述の Enum 参照。 |
| **ID** | `String` | `<Area>-<Category>-<Number>` 形式。不変の一意キー。 |
| **Priority** | `Enum` | `P0` / `P1` / `P2` / `P3` |
| **Size** | `Enum` | `XS` / `S` / `M` / `L` / `XL` |
| **Risk** | `Enum` | `Low` / `Medium` / `High` / `Critical` |
| **Area** | `String` | タスクの論理領域。各 canonical path の `<Area>` と一致させる。 |
| **Dependencies** | `List<ID>` | 依存タスク ID の配列。なしは `[]`。 |
| **Goal** | `String` | 完了後に成り立つ状態を一文で書く。 |
| **Acceptance Criteria** | `Markdown` | `AC-001` 形式で、検証可能な条件を書く。 |
| **Steps** | `Markdown` | 進行管理用チェックリスト。 |
| **Description** | `Markdown` | Context / Notes を含める。 |
| **Plan** | `Path` | `None` または `_docs/plan/<Area>/<slug>/plan.md`。`Size >= M` で必須。 |
| **Intent** | `Path` | `None` または `_docs/intent/<Area>/<slug>/decision.md`。DEC を作ったら埋める。 |
| **QA** | `Path` | `_docs/qa/<Area>/<slug>/qa.md` または `_docs/qa/<Area>/maintenance.md`。`None` 不可。 |

推奨形式:

```markdown
### <ID>: [<Category>] <Title>

- **Title**: [<Category>] <Title>
- **ID**: <Area>-<Category>-<Number>
- **Priority**: P0 | P1 | P2 | P3
- **Size**: XS | S | M | L | XL
- **Risk**: Low | Medium | High | Critical
- **Area**: <Area>
- **Dependencies**: []
- **Goal**: <one sentence>
- **Acceptance Criteria**:
  - AC-001:
  - AC-002:
- **Steps**:
  1. [ ] Step 1
  2. [ ] Step 2
- **Description**:
  - Context:
  - Notes:
- **Plan**: None | _docs/plan/<Area>/<slug>/plan.md
- **Intent**: None | _docs/intent/<Area>/<slug>/decision.md
- **QA**: _docs/qa/<Area>/<slug>/qa.md | _docs/qa/<Area>/maintenance.md
```

## 3. Required Depth

すべてのタスクは完了時に Intent Delta の宣言と QA round を持つ (常時 ON ループ)。省略できるのは
深さであって、存在ではない。詳細は `_docs/standards/workflow.md` を参照。

| Condition | Requirement |
| --- | --- |
| すべてのタスク | 完了時に QA round (Intent Delta / verdict を含む)。微小変更は `maintenance.md` へ追記。 |
| `Size >= M` | Plan が必須。QA は専用の `qa.md` を作る。 |
| `Risk >= Medium` | `qa.md` を実装前に `qa_status: planned` で作る。 |
| `Risk High / Critical` | rollback / recovery / security / data safety の確認と、完了前の verdict が必須。 |
| DEC 新設 / `Size >= M` / `Risk High` | R2 再構成テストが発動する。`R2: PENDING` を round に書き、R2 タスクを積む。 |
| `Category Bug` | Acceptance Criteria に再発防止条件を含め、regression test または no-test rationale を残す。 |
| `Category Refactor` | behavior-preservation checks を残す。 |
| Agent workflow / validator / CI / Skill / documentation rule 変更 | 自動的に `Risk High` (パスベース下限)。agent misbehavior checks を含める。 |

## 4. Completion Rules

タスクを `TODO.md` から削除できるのは、以下を満たす場合のみ。

1. Steps が完了している。
2. Acceptance Criteria が満たされている。
3. QA round が記録され、Intent Delta が宣言されている (DEC 新設 / applied / 理由付き None)。
4. verdict が `PASS` である。`PARTIAL` の場合は、残リスクと follow-up TODO が明記されている。
5. `FAIL` / `BLOCKED` の場合は完了扱いにしない。
6. R2 発動タスクは、`R2: PENDING` の記録と R2 タスクの追加が済んでいる。
7. Plan があれば `_docs/archives/plan/` へ移送し、参照を更新している。

## 5. Canonical Document Paths

```text
_docs/plan/<Area>/<slug>/plan.md
_docs/intent/<Area>/<slug>/decision.md
_docs/intent/<Area>/conventions/decision.md
_docs/qa/<Area>/<slug>/qa.md
_docs/qa/<Area>/maintenance.md
_docs/guide/<Area>/<slug>/usage.md
_docs/reference/<Area>/<slug>/reference.md
_docs/archives/plan/<Area>/<slug>/plan.md
```

`<Area>` はタスクの `Area` と一致させる。`<slug>` は機能・変更単位の kebab-case 名にする。`intent` / `qa` / `guide` / `reference` は archive 対象にしない。

## 6. Defined Enums

### Categories (Title & ID)

- `Feat` (New Feature)
- `Enhance` (Improvement)
- `Bug` (Fix)
- `Refactor` (Code Structuring)
- `Perf` (Performance)
- `Doc` (Documentation)
- `Test` (Testing)
- `Chore` (Maintenance/Misc)
- `R2` (Reconstruction Test)

### Priorities

- `P0`: Critical / immediate
- `P1`: High
- `P2`: Medium
- `P3`: Low

### Sizes

- `XS`: 0.5 day 未満
- `S`: 1 day 程度
- `M`: 2-3 days 程度
- `L`: 1 week 程度
- `XL`: 2 weeks 以上

### Risk

Risk の詳細とパスベースの自動下限は `_docs/standards/workflow.md` を参照する。

- `Low`: 局所的で失敗影響が小さい変更。
- `Medium`: 機能挙動、ワークフロー、validator、ドキュメント規約、agent skill に影響する変更。
- `High`: 互換性、データ損失、認証、権限、セキュリティ、課金、外部 API、CI/CD、migration に関わる変更。
- `Critical`: 本番障害、secret 漏洩、重大なデータ破壊、ユーザー影響の大きい破壊的変更につながり得る変更。

## 7. Operational Workflows (for LLM)

### Create Task from Inbox

1. `Next ID No` を読み取り、割り当て予定の ID を決定する。
2. `Next ID No` をインクリメントしてファイルを更新する。
3. Inbox の内容を解析し、最適な `Area` / `Category` / `Risk` を決定する。
4. ID を生成し、Acceptance Criteria を `AC-001` 形式で書く。
5. 深さ条件に従い、Plan / Intent / QA を埋める (QA は `None` 不可)。
6. タスクを `Backlog` の末尾に追加し、元の Inbox 行を削除する。

### Promote to Ready

1. `Size >= M` なら Plan が存在することを確認する。
2. `Risk >= Medium` なら `qa.md` が `qa_status: planned` で存在し、Checks が主要 AC を確認手段へ
   割り当てていることを確認する。
3. Dependencies が解決済みか確認する。
4. 全てクリアした場合のみ `Ready` セクションへ移動する。

### Complete Task

1. Steps と Acceptance Criteria を確認する。
2. QA round を記録する (Intent Delta / verdict 必須)。R1 review を行い、発動条件を満たすなら
   `R2: PENDING` と R2 タスクを積む。
3. verdict が `PASS`、または許容済み `PARTIAL` であることを確認する。
4. `FAIL` / `BLOCKED` の場合は、タスクを残すか follow-up を追加する。
5. 完了可能な場合のみ `TODO.md` から削除する。

### R2 Task

R2 タスクを拾った agent は、対象 diff とリポジトリ内の docs だけを読んで
`_docs/standards/workflow.md` の固定設問 4 つに答え、結果と gap を該当 QA 文書の
round に追記する。gap があれば DEC 修繕タスクを積む。

## 8. Task Definition Examples

### Case A: 微小タスク (XS + Low)

```markdown
### Docs-Chore-10: [Chore] Update project display name

- **Title**: [Chore] Update project display name
- **ID**: Docs-Chore-10
- **Priority**: P2
- **Size**: XS
- **Risk**: Low
- **Area**: Docs
- **Dependencies**: []
- **Goal**: README と Quickstart の表示名がプロジェクト名に置き換わっている。
- **Acceptance Criteria**:
  - AC-001: README の旧テンプレート名が新しいプロジェクト名に置き換わっている。
- **Steps**:
  1. [ ] README.md と QUICKSTART.md を更新する
- **Description**:
  - Context: 新規プロジェクト作成直後の軽量カスタマイズ。
  - Notes: 完了時に maintenance.md へ round を 1 つ追記する (Intent Delta: None 想定)。
- **Plan**: None
- **Intent**: None
- **QA**: _docs/qa/Docs/maintenance.md
```

### Case B: Size M + Medium Risk Task

```markdown
### Core-Enhance-11: [Enhance] Add onboarding command

- **Title**: [Enhance] Add onboarding command
- **ID**: Core-Enhance-11
- **Priority**: P1
- **Size**: M
- **Risk**: Medium
- **Area**: Core
- **Dependencies**: []
- **Goal**: 新規メンバーが onboarding command で初期診断を実行できる。
- **Acceptance Criteria**:
  - AC-001: command が環境診断を実行し、結果を標準出力に表示する。
  - AC-002: 採用した設計判断が DEC として記録され、該当箇所にポインタコメントが置かれている。
- **Steps**:
  1. [ ] Plan の Scope / Non-Goals を確認する
  2. [ ] qa.md の Checks に従って実装と検証を進める
- **Description**:
  - Context: ユーザー向け workflow が増えるため Medium risk とする。
  - Notes: Size M のため R2 が発動する。
- **Plan**: _docs/plan/Core/onboarding-command/plan.md
- **Intent**: _docs/intent/Core/onboarding-command/decision.md
- **QA**: _docs/qa/Core/onboarding-command/qa.md
```

### Case C: Agent Workflow / Validator / Skill Task

```markdown
### Workflow-Chore-12: [Chore] Tighten TODO validator

- **Title**: [Chore] Tighten TODO validator
- **ID**: Workflow-Chore-12
- **Priority**: P1
- **Size**: M
- **Risk**: High
- **Area**: Workflow
- **Dependencies**: []
- **Goal**: TODO validator が新 schema と QA 必須条件を検出できる。
- **Acceptance Criteria**:
  - AC-001: validator が Risk / QA 欠落を error として検出する。
  - AC-002: agent misbehavior checks が QA round に残っている。
- **Steps**:
  1. [ ] Plan / Intent / QA を読む
  2. [ ] validator を更新する
- **Description**:
  - Context: scripts/ に触れるためパスベース下限により Risk High。R2 が発動する。
  - Notes: `validate-todo` と `validate-qa` の両方を実行する。
- **Plan**: _docs/plan/Workflow/todo-validator/plan.md
- **Intent**: _docs/intent/Workflow/todo-validator/decision.md
- **QA**: _docs/qa/Workflow/todo-validator/qa.md
```

---

## Inbox

-

---

## Backlog

### Core-Test-17: [Test] Verify automatic ADB recovery against live Waydroid

- **Title**: [Test] Verify automatic ADB recovery against live Waydroid
- **ID**: Core-Test-17
- **Priority**: P1
- **Size**: S
- **Risk**: High
- **Area**: Core
- **Dependencies**: []
- **Goal**: installed user service が実際の ADB disconnect / Waydroid restart / authorization transition から manual `adb connect` なしで復帰することを live evidence で確認する。
- **Acceptance Criteria**:
  - AC-001: new daemon code で稼働する installed service が ADB target 消失後に bounded retry で `device` へ戻り、manual `adb connect` なしで snapshot polling を再開する。
  - AC-002: live `unauthorized` state が operator action required と診断され、approval 前は stopped state、approval 後は自動復帰になる。
  - AC-003: journal が同一 failure を毎 poll 出さず、初回・状態変化・60 秒 reminder・recovery を観測できる。
  - AC-004: recovery 前は MPRIS `Stopped` / no-track / `CanControl=false`、recovery 後は selected Apple Music session の metadata / controls / artwork が戻る。
- **Steps**:
  1. [ ] service restart、ADB disconnect、Waydroid restart、authorization prompt 操作の承認を得る
  2. [ ] installed service を new checkout code で restart する
  3. [ ] ADB disconnect と Waydroid restart の recovery latency / journal / MPRIS transition を採取する
  4. [ ] unauthorized が発生した場合は operator guidance と approval 後 recovery を採取する
  5. [ ] qa.md の Rounds に verdict と R2 発動の記録を追記する
- **Description**:
  - Context: `Core-Enhance-16` は非破壊 unit/static/read-only verification まで PARTIAL で完了した。
  - Notes: この task は playback と Waydroid / ADB / user service を中断する。ユーザーの明示承認なしに実行しない。Risk High のため R2 が発動する。
- **Plan**: _docs/plan/Core/waydroid-adb-auto-recovery/plan.md
- **Intent**: _docs/intent/Core/waydroid-adb-auto-recovery/decision.md
- **QA**: _docs/qa/Core/waydroid-adb-auto-recovery/qa.md

### Workflow-R2-21: [R2] Reconstruct why for docs template v1.0.0 → v2.5.3 migration

- **Title**: [R2] Reconstruct why for docs template v1.0.0 → v2.5.3 migration
- **ID**: Workflow-R2-21
- **Priority**: P2
- **Size**: XS
- **Risk**: High
- **Area**: Workflow
- **Dependencies**: []
- **Goal**: 次 session が `docs-template.lock.json` 変更と関連 diff、`_docs/standards/workflow.md` 固定 4 問への回答から migration の why を再構成し、gap があれば DEC 修繕タスクを積む。
- **Acceptance Criteria**:
  - AC-001: R2 agent が固定 4 問に回答し、`_docs/qa/Workflow/docs-template-v2-5-3-migration/qa.md` に Round 2 として追記する。
  - AC-002: gap が特定された場合、DEC 修繕タスクを新規 TODO として積む。
- **Steps**:
  1. [ ] `_docs/qa/Workflow/docs-template-v2-5-3-migration/qa.md` と related diff を読む
  2. [ ] `_docs/standards/workflow.md` § R2 の固定 4 問に回答する
  3. [ ] gap を Round 2 として追記する
  4. [ ] 必要に応じて DEC 修繕タスクを積む
- **Description**:
  - Context: 直前 session の migration では Risk High (path 自動下限) で R2 が発動した。`R2: PENDING` を該当 qa.md に記録し、本タスクを積んでいる。
  - Notes: 実装 agent の context を持たない fresh session が拾うべきタスク。
- **Plan**: None
- **Intent**: None
- **QA**: _docs/qa/Workflow/docs-template-v2-5-3-migration/qa.md

### Workflow-Chore-22: [Chore] Retreat or remove legacy template files after v2.5.3 migration

- **Title**: [Chore] Retreat or remove legacy template files after v2.5.3 migration
- **ID**: Workflow-Chore-22
- **Priority**: P2
- **Size**: XS
- **Risk**: High
- **Area**: Workflow
- **Dependencies**: []
- **Goal**: v1.0.0 由来で v2.5.3 に統合された standards / templates / skills / mjs validators / markdownlint / security_for_agents を、owner authority で `git rm` するか、`_meta/` 配下に退避する。
- **Acceptance Criteria**:
  - AC-001: 削除承認済みの 34+ files が、`git rm` または `git mv` によって project 運用対象から除外され、check-docs.sh が引き続き 0 error で PASS する。
  - AC-002: 削除 / 移送は owner 実行 or 明示承認による agent 実行のいずれかで、AGENTS.md rule と rm 禁止 hook を bypass しない。
- **Steps**:
  1. [ ] `_docs/qa/Workflow/docs-template-v2-5-3-migration/qa.md` Round 1 の removal 候補 list を確認する
  2. [ ] owner が rm ワンライナーを実行 (提示済み) するか、退避パスへ agent が `git mv` する
  3. [ ] check-docs.sh を再実行して 0 error を確認
- **Description**:
  - Context: hook が rm を block するため、通常の agent 操作では removal を完了できない。owner の明示実行 or 段階的な `git mv` retreat が必要。
  - Notes: 削除対象 list は `_docs/qa/Workflow/docs-template-v2-5-3-migration/qa.md` および migration report を参照。
- **Plan**: None
- **Intent**: None
- **QA**: _docs/qa/Workflow/docs-template-v2-5-3-migration/qa.md

### Core-R2-24: [R2] Reconstruct why for the MPRIS position lead offset

- **Title**: [R2] Reconstruct why for the MPRIS position lead offset
- **ID**: Core-R2-24
- **Priority**: P2
- **Size**: XS
- **Risk**: High
- **Area**: Core
- **Dependencies**: []
- **Goal**: 次 session が `Core-Enhance-23` の diff とリポジトリ内 docs だけから、公開 Position をずらす判断の why を再構成し、gap があれば DEC 修繕タスクを積む。
- **Acceptance Criteria**:
  - AC-001: R2 agent が `_docs/standards/workflow.md` § R2 の固定 4 問に回答し、`_docs/qa/Core/mpris-position-lead/qa.md` に Round 2 として追記する。
  - AC-002: gap が特定された場合、DEC-007 の修繕タスクを新規 TODO として積む。
- **Steps**:
  1. [ ] `_docs/qa/Core/mpris-position-lead/qa.md` と対象 diff を読む
  2. [ ] 固定 4 問に回答する
  3. [ ] gap を Round 2 として追記する
  4. [ ] 必要に応じて DEC 修繕タスクを積む
- **Description**:
  - Context: DEC-007 新設 かつ `scripts/` への変更による Risk High 下限で R2 が発動した。Round 1 に `R2: PENDING` を記録済み。
  - Notes: 実装 agent の context を持たない fresh session が拾うべきタスク。特に「なぜ lead を projector 内部ではなく読み出し境界に置いたか」が docs だけから再構成できるかを見る。
- **Plan**: None
- **Intent**: _docs/intent/Core/mpris-position-lead/decision.md
- **QA**: _docs/qa/Core/mpris-position-lead/qa.md

### Workflow-Chore-20: [Chore] Review strict docs schema adoption

- **Title**: [Chore] Review strict docs schema adoption
- **ID**: Workflow-Chore-20
- **Priority**: P2
- **Size**: S
- **Risk**: Low
- **Area**: Workflow
- **Dependencies**: []
- **Goal**: legacy intent / QA records を semantic 単位で棚卸しし、strict schema (intent_schema 3 / qa_schema 4) への移行順と旧 workflow 参照の扱いが記録される。
- **Acceptance Criteria**:
  - AC-001: schema marker が旧値または欠落の project intent / QA records が列挙され、現行 / superseded history / fixture に分類されている。
  - AC-002: incremental-adoption / intentional-omission records の active 参照を保ったまま、retention または supersession 方針が maintenance round に記録されている。
  - AC-003: 意味の review なしに frontmatter marker だけを一括追加しない。
- **Steps**:
  1. [ ] legacy intent / QA records と参照元を inventory する
  2. [ ] current decision ごとに新 schema へ移す必要性と順序を決める
  3. [ ] future template release の compatibility boundary を確認する
- **Description**:
  - Context: v1.0.0 → v2.5.3 migration の閉じ後、残る legacy schema docs の semantic migration を段階的に進める。
  - Notes: docs-only review。bulk marker edit や runtime 変更は行わない。
- **Plan**: None
- **Intent**: None
- **QA**: _docs/qa/Workflow/maintenance.md

---

## Ready

---

## In Progress
