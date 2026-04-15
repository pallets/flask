# Governance — flask
# Inferred by crag analyze — review and adjust as needed

## Identity
- Project: flask
- Stack: python

## Gates (run in order, stop on failure)
### Lint
- uv run ruff check .
- uv run ruff format --check .
- uv run mypy .

### Test
- uv run tox run

### Build
- python -m build

### CI (inferred from workflow)
- uv run --locked --no-default-groups --group pre-commit pre-commit run --show-diff-on-failure --color=always --all-files
- uv run --locked --no-default-groups --group dev tox run
- uv run --locked --no-default-groups --group dev tox run -e typing

## Advisories (informational, not enforced)
- actionlint  # [ADVISORY]

## Branch Strategy
- Trunk-based development
- Free-form commits
- Commit trailer: Co-Authored-By: Claude <noreply@anthropic.com>

## Security
- No hardcoded secrets — grep for sk_live, AKIA, password= before commit

## Autonomy
- Auto-commit after gates pass

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

## Dependencies
- Package manager: uv (uv.lock)

## Anti-Patterns

Do not:
- Do not catch bare `Exception` — catch specific exceptions
- Do not use mutable default arguments (e.g., `def f(x=[])`)
- Do not use `import *` — use explicit imports
