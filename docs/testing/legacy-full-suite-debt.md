# Legacy Full-Suite Debt

This document records the exact failing node set in the repository-wide diagnostic test suite (`python -m pytest -q`) that is intentionally **not** required as a merge gate for the reusable base-platform PR #93.

## Status

The repository-wide diagnostic step in CI is marked `continue-on-error: true` and labelled as legacy debt. It must not be described as a successful full-suite gate. The failures documented here are pre-existing, dedicated reverse-tool tests that are outside the scope of the thin Supervisor and reusable unattended-platform base.

## Failing nodes

### tests/test_local_reverse_forced_ida_extract.py — 4 failures

These tests reference local Windows binaries and reverse-specific behavior that is not available on the generic Ubuntu CI runner:

1. `tests/test_local_reverse_forced_ida_extract.py::TestRunForcedExtraction::test_thunk_detection`
   - `KeyError: 'sub_401005_is_thunk'`

2. `tests/test_local_reverse_forced_ida_extract.py::TestRunForcedExtraction::test_sha256_transform_inferred`
   - `AssertionError: assert 'SHA-256' in ''`

3. `tests/test_local_reverse_forced_ida_extract.py::TestRunForcedExtraction::test_blocker_resolved_when_transform_recovered`
   - `assert False is True`

4. `tests/test_local_reverse_forced_ida_extract.py::TestRunForcedExtraction::test_ida_failure_blocked`
   - `AssertionError: assert ('timeout' in 'binary not found for 18019fca52b389fe (tried e:\\reverse/逆向课程2024春01/sha_256.exe)' or 'failed' in '...')`

## Root cause

The dedicated reverse-tool tests depend on:
- local Windows binary paths (e.g. `E:\reverse\逆向课程2024春01\sha_256.exe`);
- reverse-specific IDA Pro extraction behavior;
- fixtures and artifacts that are not part of the reusable base-platform scope.

## Scope boundary

These tests must not block the generic Supervisor/platform PR. Dedicated reverse-tool production code and its tests remain unchanged and are not added to the base-platform scope. Any new failure outside this documented legacy set is blocking.
