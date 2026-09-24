---
title: "QA rounds: Workflow maintenance"
status: active
qa_status: verified
risk: High
qa_schema: 5
created_at: 2026-09-24
updated_at: 2026-09-24
references: []
related_issues: []
related_prs: []
---

# QA rounds: Workflow maintenance

## Rounds

### Round 1 (2026-09-24)

- **Commands**:

  ```bash
  bash scripts/check-docs.sh   # 最後まで走り、残る赤は todo（Core-Test-17）だけ
  ```

- **AC Coverage**: `scripts/check-docs.sh` を pi-web-idd の最新に合わせた。1 つの検査が赤でも後ろの検査を最後まで走らせ、最後に失敗した段をまとめて返す（これまでは Core-Test-17 の赤で止まり、intent と qa の検査が走っていなかった）。最後まで走らせて見えた IDD-002 の記録の赤 7 件は、DEC の番号が 2 桁（`DEC-21`〜`DEC-34`）で、今の検査の書式（3 桁）に合わないためだったので、IDD-002 の decision / qa / reference の番号を `DEC-021`〜`DEC-034` に揃えた（参照はこの 3 ファイルの中だけで、ほかの番号とも重ならない） — covered
- **Intent Delta**: None: 検査の走らせ方と記録の番号の書式の修正で、設計の判断を含まない
- **R2**: PENDING（`scripts/check-docs.sh` は作業の流れに関わるパスで Risk High の下限に当たる。配布元の pi-web-idd の同じ変更と一緒に R2 をかける）
- **Verdict**: PARTIAL

### Round 2 (2026-09-24)

- **Commands**:

  ```bash
  bash scripts/check-docs.sh   # 残る赤は todo（Core-Test-17）だけ
  ```

- **AC Coverage**: Round 1 の R2 を、配布元の pi-web-idd の同じ変更（`scripts/check-docs.sh` は両 repo で同一）にかけた（v4.1-flash、$0.08、request-changes、should 2 件・nit 1 件）。この repo に当てはまるのは、変更が入れた性質「1 つの赤が別の赤を隠さない: 各段を失敗しても最後まで走らせ、失敗した段をまとめて返す」がどこにも書かれていない、の 1 件で、この round に記録する（検査の段を足すときも、途中で止めずに結果を集める形を保つ）。Risk の下限の指摘はこの文書では当たらない（risk: High で R2 を PENDING にしていた）。別 repo の作業を束ねて書いている、の nit は pi-web-idd 側の記録の話。あわせて、最後まで走らせた検査で、並行して回した IDD-023 と IDD-024 が同じ INV-020〜022 を採番していた赤が見えた（どちらも merge 済み。INV の番号は repo で一意）。IDD-024 の INV を空き番号の INV-024〜026 に付け替えた（参照は IDD-024 の decision / qa / reference の中だけ） — covered
- **Intent Delta**: None: Round 1 の変更の R2 の記録と、その変更が持つ性質の書き残しで、新しい判断を含まない
- **R2**: request-changes（Round 1 の R2、上記）
- **Verdict**: PASS
