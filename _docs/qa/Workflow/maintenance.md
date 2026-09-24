---
title: "QA rounds: Workflow maintenance"
status: active
qa_status: partial
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
