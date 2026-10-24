# Issue #1328 Boundary Execution Report (Rev5)

**Base:** `7e165b588c14e50332b01782a13321624edec643` (merged main, incl. #1334 child-environment handling)
**Prior candidate diff reused from:** `654f1e82635b00589ef21cd0d8d9849a2c585009` (Rev4 artifact-acceptance tree, read-only)
**Revision:** 5 of the same goal (repair window, not a fresh retry budget).

This delivery is an EXECUTION_ONLY source candidate. The host separately runs frozen
exact-source probes, a fresh independent CLI review, CI and governed landing.

---

## Scope of this revision

The Rev4 candidate's full diagnostics/recovery support is retained. This revision makes
three narrow corrections that Rev4 failed against three new independent controlled cases,
plus one production-path classification correction. Source and tests are updated.

### `reverse_agent/executor_neutral/core.py`

- **Traversal onerror (failure 1).** `_scan_workspace_indirections` now passes an
  `onerror` callback to `os.walk`. A controlled `os.scandir` `PermissionError` on an
  ordinary subdirectory is recorded as an `access_error` violation instead of being
  silently skipped, so the pre-staging refusal fires before `git add` and the sentinel
  blob never enters the object database.
- **Native-header false positive (failure 2).** `_inspect_native_header` no longer treats
  "`e_lfanew` out of range" as `native_executable`. It rejects only when a genuine
  `PE\x00\x00` signature is found at the declared `e_lfanew` offset (including `0x2000`)
  within the bounded `0x2080`-byte read. A realistic-length source file
  (`b"MZ = 1\n" + b"# ordinary source comment\n" * 5`) whose bytes at `0x3C` are ASCII is
  therefore accepted, while a genuine PE at `e_lfanew=0x2000` is still rejected. ELF,
  Mach-O and package rejection and bounded reads are unchanged.
- **Runtime path rejection (failure 3).** New `_runtime_artifact_rule` classifies literal
  runtime artifacts — the `~/AppData/Local/Nerelan/` prefix and any `platform-v1` /
  `.platform_v1_runtime` path ending in `.sqlite3`, `.sqlite3-wal`, `.sqlite3-shm`, `.db`,
  `.db-wal` or `.db-shm` — as `runtime_artifact`. It is applied in the pre-staging scan, so
  the file is rejected before `git add` or any payload read; it never inspects contents and
  does not blanket-ban unrelated data fixtures (e.g. `project/data.sqlite3` stays accepted).
- `_snapshot_workspace` now raises a `SnapshotIndirectionError(ValueError)` carrying the
  full violation list, keeping the exact `snapshot_indirection_detected:<list>` message the
  independent probes rely on, while giving the FunctionalValidation path structured access
  to the offending entries.

### `reverse_agent/platform_v1/functional_validation.py`

- `validate_functional` catches `SnapshotIndirectionError` from the pre-read refusal and
  reclassifies it as `functional_patch_hygiene_failed` / `failure_kind == "patch_hygiene"`,
  preserving bounded offending-file/rule feedback via `hygiene_diagnostics` instead of
  leaking it as `functional_observation_failed:ValueError` / `host_observation`.
- Hygiene is now checked before `functional_implementation_missing`, so an early refusal
  that yields an empty tree cannot be misclassified as a missing implementation.
- `public_hygiene` and the `hygiene_diagnostics` feedback lines are retained from Rev4.

### Other platform sources (retained from Rev4)

- `opencode_executor.py`: `_artifact_file_is_safe` boundary gate, prompt constraint,
  `_count_untracked_lines` symlink guard.
- `contract_recovery.py`: `public_hygiene` persistence and `safe_recovery_tree` restore.
- `context_builder.py`: ContractFixup feedback loading.
- `repository_preparation.py`: `assert_pristine_workspace`.

---

## Independent host probes (10 cases, all pass)

Host scripts under `F:\reverse-agent\.platform_v1_runtime\issue1328-20261022` were run
against the final source in this worktree (not copied or edited):

| Probe | Cases | Result |
|-------|-------|--------|
| `verify_boundary_independently.py` | 6 (junction, metadata-error, legitimate MZ, extensionless ELF, large-offset PE, package tree) | all 6 pass |
| `verify_boundary_extra.py` | 4 (ignored-cache, long-MZ source, literal-tilde sqlite, traversal failure) + real functional classification/feedback | all pass |

Key evidence for the three corrected cases (fresh fixture run):

- `long_MZ_python_source`: `rejected=false`, changed `ordinary.py`, no diagnostics.
- `literal_tilde_runtime_sqlite`: `rejected=true`, rule `runtime_artifact`,
  `payload_blob_added=false`, `python_payload_read_attempts=0`, index/HEAD preserved.
- `traversal_failure`: `rejected=true`, `blob_added=false`, index/HEAD preserved.
- `ignored_cache_and_source`: still `rejected=false` with only `ordinary.py` (the
  ignored `__pycache__` regression did not return).

Functional classification probe (real `validate_functional`, not a helper-only assertion):

- `reason == "functional_patch_hygiene_failed"`, `failure_kind == "patch_hygiene"`,
  feedback contains `link` and `reparse`, `outside_blob_added=false`,
  `collector_payload_read_attempts=0`.

---

## Owned test suites (host CPython 3.13, pytest 8.4.2)

```
python -m pytest tests/executor_neutral/test_vertical_slice.py     — 68 passed
python -m pytest tests/platform_v1/test_functional_validation.py   — 47 passed
python -m pytest tests/platform_v1/test_opencode_executor.py       — 214 passed, 1 skipped
python -m pytest tests/platform_v1/test_contract_miss_fixup.py     — 34 passed
git diff --check                                                     — clean
```

The single skip in `test_opencode_executor.py` is the pre-existing symlink-not-supported
skip, unrelated to this change.

New production-path regressions were added to all four permitted test files:
traversal `onerror` fail-closed with Git-ODB absence, long-MZ source acceptance, runtime
sqlite pre-staging rejection, portable runtime path rules, ignored-cache/source split,
and a real `validate_functional` junction classification (not a helper-only `raises`).

---

## What was not verified (execution-only candidate)

- No commit, push, PR, merge, tag, release or deployment.
- Exact-head CI (`baseline`, `state-gate`, `landing-state-gate`) not run here.
- No independent CLI review; host runs a fresh independent review of the exact source.
- No native Linux/macOS execution; no frontend build; no provider/model/server call.
- This report does not claim #1328 completion or any scientific/short-test acceptance.
