<!-- crag:auto-start -->
# GEMINI.md

> Generated from governance.md by crag. Regenerate: `crag compile --target gemini`

## Project Context

- **Name:** flask
- **Stack:** python
- **Runtimes:** python

## Rules

### Quality Gates

Run these checks in order before committing any changes:

1. [lint] `uv run ruff check .`
2. [lint] `uv run ruff format --check .`
3. [lint] `uv run mypy .`
4. [test] `uv run tox run`
5. [build] `python -m build`
6. [ci (inferred from workflow)] `uv run --locked --no-default-groups --group pre-commit pre-commit run --show-diff-on-failure --color=always --all-files`
7. [ci (inferred from workflow)] `uv run --locked --no-default-groups --group dev tox run`
8. [ci (inferred from workflow)] `uv run --locked --no-default-groups --group dev tox run -e typing`

### Security

- No hardcoded secrets — grep for sk_live, AKIA, password= before commit

### Workflow

- Follow project commit conventions
- Run quality gates before committing
- Review security implications of all changes

<!-- crag:auto-end -->
