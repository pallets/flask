<!-- crag:auto-start -->
# Amazon Q Rules — flask

> Generated from governance.md by crag. Regenerate: `crag compile --target amazonq`

## About

(No description)

**Stack:** python

**Runtimes detected:** python

## How Amazon Q Should Behave on This Project

### Code Generation

1. **Run governance gates before suggesting commits.** The gates below define the quality bar.
2. **Respect classifications:** MANDATORY (default) blocks on failure; OPTIONAL warns; ADVISORY is informational only.
3. **Respect scopes:** Path-scoped gates run from that directory. Conditional gates skip when their file does not exist.
4. **No secrets.** - No hardcoded secrets — grep for sk_live, AKIA, password= before commit
5. **Minimal diffs.** Prefer editing existing code over creating new files. Do not refactor unrelated areas.

### Quality Gates

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `uv run tox run`
- `python -m build`
- `uv run --locked --no-default-groups --group pre-commit pre-commit run --show-diff-on-failure --color=always --all-files`
- `uv run --locked --no-default-groups --group dev tox run`
- `uv run --locked --no-default-groups --group dev tox run -e typing`

### Commit Style

Follow project commit conventions.

### Boundaries

- All file operations must stay within this repository.
- No destructive shell commands (rm -rf above repo root, DROP TABLE without confirmation, force-push to main).
- No new dependencies without an explicit reason.

## Authoritative Source

When these instructions seem to conflict with something in the repo, **`.claude/governance.md` is the source of truth**. This file is a compiled view.

---

**Tool:** crag — https://www.npmjs.com/package/@whitehatd/crag

<!-- crag:auto-end -->
