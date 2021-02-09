<!--
Before opening a PR, open a ticket describing the issue or feature the
PR will address. Follow the steps in CONTRIBUTING.rst.

Replace this comment with a description of the change. Describe how it
addresses the linked ticket.
-->

<!--
Link to relevant issues or previous PRs, one per line. Use "fixes" to
automatically close an issue.
-->

- fixes #<issue number>

<!--
Ensure each step in CONTRIBUTING.rst is complete by adding an "x" to
each box below.

If only docs were changed, these aren't relevant and can be removed.
-->

Checklist:

- [ ] Add tests that demonstrate the correct behavior of the change. Tests should fail without the change.
- [ ] Add or update relevant docs, in the docs folder and in code.
- [ ] Add an entry in `CHANGES.rst` summarizing the change and linking to the issue.
- [ ] Add `.. versionchanged::` entries in any relevant code docs.
- [ ] Run `pre-commit` hooks and fix any issues.
- [ ] Run `pytest` and `tox`, no tests failed.
