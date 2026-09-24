#!/usr/bin/env bash
set -euo pipefail

# 未初期化 template では TODO.md が starter/ 側にある。展開後は root へ戻るため、
# どちらの状態でも同じコマンドで検証できるよう実在するほうを選ぶ。
if [ -f "TODO.md" ]; then
  todo_file="TODO.md"
elif [ -f "starter/TODO.md" ]; then
  todo_file="starter/TODO.md"
else
  echo "check-docs: TODO.md not found at root or starter/" >&2
  exit 1
fi
export DD_TODO_FILE="$todo_file"

# 途中導入したプロジェクトは、導入時点の upstream の commit（idd init が lock に記録）以降だけを検査する
if [ -z "${DD_SCOPE_BASE:-}" ] && [ -f docs-template.lock.json ]; then
  adopted="$(sed -n 's/.*"adopted_base": *"\([0-9a-f]\{7,40\}\)".*/\1/p' docs-template.lock.json | head -1)"
  if [ -n "$adopted" ]; then export DD_SCOPE_BASE="$adopted"; fi
fi

# 各段は失敗しても最後まで走らせ、最後に失敗した段をまとめて返す。1 つの赤で後ろの検査が走らないと、別の赤が隠れる
failed=()
step() {
  local name="$1"; shift
  if ! "$@"; then failed+=("$name"); fi
}

# only the template's own scripts: a project that adopted the overlay may keep its own TypeScript in scripts/
template_ts=()
for f in scripts/*.ts; do
  case "$(basename "$f")" in
    agent-workflow-hook.ts | generate-doc-probe.ts | scope.ts | test-agent-workflow-hook.ts | test-agent-workflow-smoke.ts | test-validators.ts | validate-*.ts) template_ts+=("$f") ;;
  esac
done
step fmt deno fmt --check "${template_ts[@]}"
step typecheck deno check "${template_ts[@]}"
step comments-test deno test scripts/validate-comments.test.ts
step frontmatter deno run --allow-read --allow-env --allow-run=git scripts/validate-frontmatter.ts
step todo deno run --allow-read scripts/validate-todo.ts "$todo_file"
step doc-links deno run --allow-read --allow-env --allow-run=git scripts/validate-doc-links.ts
step intent deno run --allow-read --allow-env --allow-run=git scripts/validate-intent.ts
step qa deno run --allow-read --allow-env --allow-run=git scripts/validate-qa.ts
step comments deno run --allow-read --allow-env --allow-run=git scripts/validate-comments.ts

# intent-delta presence は展開後の利用者 project の規範。未初期化 template
# (starter/ が存在) は meta-work 例外により対象外。
if [ ! -d "starter" ]; then
  step intent-delta deno run --allow-read --allow-env --allow-run=git scripts/validate-intent-delta.ts
fi
step workflow-hook deno run --allow-read --allow-write --allow-env --allow-run scripts/test-agent-workflow-hook.ts
# validator と出荷物の自己テストはテンプレートを開発する側の検査。見本（fixtures）を持つ repo でだけ回す
if [ -d "_meta/validator-fixtures" ]; then
  step validators-selftest deno run --allow-read --allow-write --allow-env --allow-run scripts/test-validators.ts
  step workflow-smoke deno run --allow-read scripts/test-agent-workflow-smoke.ts
fi

if [ ${#failed[@]} -gt 0 ]; then
  echo "check-docs: FAILED: ${failed[*]}" >&2
  exit 1
fi

# 射程の明示。exit 0 を「完了の根拠」へ流用させないための最後の 1 行。
echo "check-docs: documentation contracts and validator health only."
echo "check-docs: the project's own build / typecheck / lint / test gates are separate — run them too."
