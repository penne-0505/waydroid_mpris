---
title: Core conventions
status: active
intent_schema: 3
draft_status: n/a
created_at: 2026-09-02
updated_at: 2026-09-02
references:
  - "_docs/intent/Core/mpris-position-lead/decision.md"
related_issues: []
related_prs: []
---

# Core conventions

<!-- Area 横断の transferable principle を集める。candidate は user の批准まで規則として扱わない。 -->

## Context

個別の変更から取り出された、Area 内で再利用できる判断原則を集約する。

## Decisions

### DEC-008 (candidate): 体感的なずれの報告は、自層の誤差を実測してから対策層を決める

- **What**: 「遅い」「ずれている」といった体感ベースの不具合報告に対しては、まず自分たちの層が
  出している値の誤差を実測し、報告された体感量に対する寄与を定量化する。対策をどの層に置くかは
  その後に決める。
- **Why**: 体感量は複数層の合算であり、報告された症状の所在と実際の発生源は一致しないことがある。
  実測を挟まずに自層を調整すると、正しく動いている層に補正を入れてしまい、真の発生源が
  隠れたまま残る。加えて、実測値がないと導入する調整点の Why が「体感で合ったから」以上に
  書けず、後から再検討する条件を持てない。
- **Change freedom**: 実測の手段 (probe 内の観測時刻との突き合わせ、外部基準との比較など) と精度。
  対策層の選択も自由であり、実測の結果として自層に調整点を置く結論になってもよい。
- **Why not**: 「まず調整点を用意して利用者に合わせてもらう」案。調整点自体は有用でも、
  発生源を特定しないまま置くと、層をまたいだ補正が重なったときに互いを打ち消す方向へ
  積み上がり、どの層を戻せばよいか判断できなくなる。

## Consequences / Impact

- 体感ベースの報告に対して、実測の一手間が固定的に加わる。
- 実測結果は該当変更の DEC の `Why` と `Revisit when` に接続できる。

## Quality Implications

- 実測なしに調整点を導入していないこと。
- 調整点を導入した場合、その既定値が「無効」であること (自層の既定挙動を歪めない)。

## Intent-derived Invariants

None

## Rollback / Follow-ups

- candidate のため、規範として扱う前に user の批准が必要。批准されない場合は本 entry を削除してよい。
