# WP3.3 preserved exercises

Hands-on assignments are paused. Codex owns implementation, tests, integration,
and documentation; no owner-written code is required to proceed.

The completed exercises remain useful regression material:

- `normalize.py` is a compatibility import for the single production function
  `processing.table_numbers.normalize_table_number`, not a second implementation.
- `test_first_assignment.py` retains five starter cases.
- `test_normalize.py` retains the wider numeric examples.
- `test_headers.py` reuses the completed production multi-period regression in
  `tests/unit/test_table_headers.py`.

These optional practice entry points run explicitly. Production numeric edge
cases and header tests also run in the default suite, without expected failures.

```bash
bash scripts/uv.sh run --frozen pytest exercises/wp33 -p no:cacheprovider
```

See [the extraction policy](../../docs/table-extraction.md) and
[the completion review](../../docs/phase-3-wp3.3-acceptance-review.md). Passing these tests
checks a bounded synthetic contract; it does not measure financial accuracy.
