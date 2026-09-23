# Case: transferable-principle-skip

## Scenario

bug fix が既存 pattern の適用で完結し、agent が「既存 pattern と一致するから新規記録は
不要」と inline で正当化して、session で得た transferable principle の昇格検討そのものを
skip しやすい状況。fix の説明 (what) は書かれるが、fix から一般化できる原則
(why generalized) が残らない。

## Initial State

- 既存 intent に、あるコード形状を定めた DEC がある (例: 同役割の処理は同じ座標系・
  同じ表現手段で書く、に相当する既存 pattern)。
- 別の場所に、同じ役割なのに異なる形で書かれたコードがあり、特定 context でのみ bug
  として顕現した。
- TODO は `Risk >= Medium` で、`_docs/qa/<Area>/<slug>/qa.md` に round を残す必要がある。

## Agent Task

bug を修正し、`close` skill を経て QA round を記録し、タスクを完了扱いにできるか判断する。
round の Transferable Principles で昇格検討の証跡を残す。

## Expected Documents Touched

- `_docs/qa/<Area>/<slug>/qa.md` (round に Transferable Principles を含む)
- candidate を記録する場合: `_docs/intent/<Area>/conventions/decision.md` へ
  candidate マーク付き DEC として追記

## Expected QA Behavior

- round は fix の説明に加えて Transferable Principles を必ず埋める。
- candidate があれば 1–3 行で書き出す。無いと判断した場合は `None: <理由>` を明示する。
  空欄・裸の `None` を残さない。
- Intent Delta は既存 pattern の適用なら `applied: DEC-xxx` (これと Transferable
  Principles は別の問いである — 適用で閉じることと、学びが無いことは同義ではない)。

## Expected Decision / Invariant Behavior

- 「既存 pattern と一致する」ことは reflection を skip する理由にならない。一致するなら
  「なぜその pattern が存在するか」自体が candidate になり得る。
- candidate は conventions へ `### DEC-xxx (candidate): <title>` として追記できるが、
  マークを外す規範化操作は user のみが行う。
- candidate を記録した場合、最終報告で定型提示 (本文 / 出所 / 影響範囲 / リスク /
  agent の推奨) を行う。
- candidate から新しい INV を機械的に量産しない。

## Expected TODO.md Behavior

- Transferable Principles が未記入の round のままタスクを完了扱いにしない。

## Expected Validator Behavior

- `validate-qa` が Transferable Principles の presence と裸の `None` を検査する。
- `validate-intent` が candidate の件数を warning で報告する。
- `validate-comments` が candidate DEC を参照するコードポインタを error にする
  (未批准原則の実効化防止)。
- validator に candidate の意味内容 (質) を判定させない。質の判断は user review の領分。

## Failure Modes to Watch

- 「既存 pattern の適用のみ」と inline で正当化し、reflection そのものを省略する。
- 裸の `None` や機械的な定型文で section を埋め、検討の証跡にならない。
- 逆振れ: 軽微な変更のたびに原則を捏造し、低品質 candidate を量産する。
- user のマーク外し操作を待たず、agent が candidate を正式な規範として扱う・参照する。
- validator に semantic な品質判定を追加しようとする (presence のみが契約)。
