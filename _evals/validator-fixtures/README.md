# Validator fixtures

These fixtures exercise the repository validators themselves.

They are not active project tasks or QA records. `scripts/test-validators.mjs`
runs the validators against these files and expects:

- files under `valid/` to pass;
- files under `invalid/` to fail.
- frontmatter files under `warning/` to pass with the expected warning.

The intent and QA fixtures run through their validators with `--fixture` and
use `fixture_path` front matter so the validators can apply the normal
canonical-path rules while the fixture files remain under `_evals/`.

The QA invalid fixture without `qa_schema` also verifies legacy compatibility:
legacy plans still require an `INV-*`, while schema v2 accepts `None`.

Frontmatter fixtures are copied into a temporary canonical `_docs/<type>/`
path. They verify that `intent_schema` and `qa_schema` are accepted only for
their matching document types, unknown fields remain warnings, and duplicate
keys are rejected before a later value can overwrite an earlier one.
