# WP3.3 assignment archive

Hands-on assignments are paused as of 2026-10-21. Codex is authorized to maintain
numeric normalization and header tests. There is no owner implementation gate.
The exercises and test cases are preserved; the production normalizer is integrated.
See [the current completion review](phase-3-wp3.3-acceptance-review.md) and
[optional practice commands](../exercises/wp33/README.md).

The following is a historical record of the earlier scaffolding session.
Its stub status, failures and next-step recommendation are superseded, not current
instructions or current validation results.

## Assignment-scaffolding review — 2026-10-21

Scope: this session's assignment preparation and independent integrity tests,
not acceptance of the other active session's complete WP3.3 implementation.

- Created `docs/wp3.3-first-assignment.md`,
  `exercises/wp33/test_first_assignment.py`, and
  `tests/unit/test_table_source_audit.py`. Reused the existing learner stub and
  numeric contracts. The stub remains `raise NotImplementedError`.
- Kept the existing separation between exercise and production extraction.
  No dependency, lockfile, canonical schema, persistence, selection or arithmetic
  policy was changed by this session. A duplicate draft stub was removed in
  favor of the concurrently created exercise. No architecture deviation or new
  ADR is required for these tests and instructions.
- `python -m pytest tests/unit/test_table_source_audit.py -v` (using
  `.venv/Scripts/python.exe` and the documented cache override): **4 passed**.
  Checks cover nested/quarantined ownership, omitted tables, omitted cells,
  and lexical tampering.
- `bash scripts/check.sh` via Git Bash with
  `PYTEST_ADDOPTS='-o cache_dir=.runtime/pytest-wp33-first'`: **passed** locked
  dependency validation, Ruff lint/format and strict mypy; **272 passed,
  10 database tests deselected**. No database test URL was supplied. An earlier
  run encountered lint errors in files being edited by the other active session;
  that session's subsequent changes resolved them before the successful run.
- `python -m pytest exercises/wp33/test_first_assignment.py -v --tb=short`
  with the same cache override: **5 failed**, each at the reserved
  `NotImplementedError`, as intended for the unimplemented exercise.
  These are actual failures in an explicitly selected exercise, not pytest
  expected-failure markers or skipped checks.
- Explicit mypy, Ruff lint, and Ruff format checks of both newly added test
  files: **passed**. `git diff --check`: **passed** for tracked changes;
  the three new files were also inspected directly.
- `bash scripts/verify-wheel.sh`: initial attempt **failed** because network
  permissions blocked PyPI. Repeated with `UV_OFFLINE=true`: **passed**, using
  cached build/runtime artifacts and hash-verified dependencies. The installed
  wheel was validated outside the checkout, including the concurrently added
  table-extraction smoke assertions. TLS and artifact checks were not weakened.
- Unrun: database integration, extended learner exercise tests, complete-corpus
  table diagnostics and human source adjudication in this session. The wider
  WP3.3 package remains subject to the other session's review and the reserved
  normalization work; no complete financial normalization or publication is
  claimed. Concurrent edits mean repository-wide checks describe the checkout
  at execution time, not a frozen commit.
- Assignment acceptance: exact path, typed signature, beginner requirements,
  five executable examples, and runnable commands supplied. Implementation and
  production integration remain outstanding by design. No commits or pushes.
- Next recommended work: you implement the reserved function, then submit it
  for review and run the broader exercise cases. Coordinate the full WP3.3 gate
  with the other active session before starting any later work package.
