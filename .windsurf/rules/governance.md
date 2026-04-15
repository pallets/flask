---
trigger: always_on
description: Governance rules for flask — compiled from governance.md by crag
---

# Windsurf Rules — flask

Generated from governance.md by crag. Regenerate: `crag compile --target windsurf`

## Project

(No description)

**Stack:** python

## Runtimes

python

## Cascade Behavior

When Windsurf's Cascade agent operates on this project:

- **Always read governance.md first.** It is the single source of truth for quality gates and policies.
- **Run all mandatory gates before proposing changes.** Stop on first failure.
- **Respect classifications.** OPTIONAL gates warn but don't block. ADVISORY gates are informational.
- **Respect path scopes.** Gates with a `path:` annotation must run from that directory.
- **No destructive commands.** Never run rm -rf, dd, DROP TABLE, force-push to main, curl|bash, docker system prune.
- - No hardcoded secrets — grep for sk_live, AKIA, password= before commit
- Follow the project commit conventions.

## Quality Gates (run in order)

1. `uv run ruff check .`
2. `uv run ruff format --check .`
3. `uv run mypy .`
4. `uv run tox run`
5. `python -m build`
6. `uv run --locked --no-default-groups --group pre-commit pre-commit run --show-diff-on-failure --color=always --all-files`
7. `uv run --locked --no-default-groups --group dev tox run`
8. `uv run --locked --no-default-groups --group dev tox run -e typing`

## Rules of Engagement

1. **Minimal changes.** Don't rewrite files that weren't asked to change.
2. **No new dependencies** without explicit approval.
3. **Prefer editing** existing files over creating new ones.
4. **Always explain** non-obvious changes in commit messages.
5. **Ask before** destructive operations (delete, rename, migrate schema).

---

**Tool:** crag — https://www.npmjs.com/package/@whitehatd/crag
