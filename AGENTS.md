<!-- crag:auto-start -->
# AGENTS.md

> Generated from governance.md by crag. Regenerate: `crag compile --target agents-md`

## Project: flask


## Quality Gates

All changes must pass these checks before commit:

### Lint
1. `uv run ruff check .`
2. `uv run ruff format --check .`
3. `uv run mypy .`

### Test
1. `uv run tox run`

### Build
1. `python -m build`

### Ci (inferred from workflow)
1. `uv run --locked --no-default-groups --group pre-commit pre-commit run --show-diff-on-failure --color=always --all-files`
2. `uv run --locked --no-default-groups --group dev tox run`
3. `uv run --locked --no-default-groups --group dev tox run -e typing`

## Coding Standards

- Stack: python
- Follow project commit conventions

## Architecture

- Type: monolith

## Key Directories

- `.github/` — CI/CD
- `docs/` — documentation
- `src/` — source
- `tests/` — tests

## Testing

- Framework: pytest
- Layout: flat
- Naming: test_*.py

## Code Style

- Indent: 4 spaces
- Line length: 88

## Anti-Patterns

Do not:
- Do not catch bare `Exception` — catch specific exceptions
- Do not use mutable default arguments (e.g., `def f(x=[])`)
- Do not use `import *` — use explicit imports

## Security

- No hardcoded secrets — grep for sk_live, AKIA, password= before commit

## Workflow

1. Read `governance.md` at the start of every session — it is the single source of truth.
2. Run all mandatory quality gates before committing.
3. If a gate fails, fix the issue and re-run only the failed gate.
4. Use the project commit conventions for all changes.

<!-- crag:auto-end -->
