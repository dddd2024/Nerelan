# Issue #1328 — environment final: custom PATHEXT regression correction (T001)

Worktree: `F:\nrl-research\ws\task-1792664324127-ba07690e0e81`
Base: `0dc2737cec081ad17a8efa01249b77f444b22536`
Reused frozen artifact: commit `7ff18523d3e34f8aaf9c0ffa5f2a32fc32a9c0ae`
("Accepted task artifact"; Task `task-1792663305047-032e411861ce`,
Execution `exec-task-1792663305047-032e411861ce`, Result
`62c250460d919a3f2faee9e4e7b18d81928f28f2e6262d74492a5f57e2ca886b`),
read as a read-only Git object.

## Author provenance (actual, stated by the task and the artifact record)

- The original environment/runtime patch (both helper AND production binding-path
  repair, location keys, shared validator, real-interpreter user-site test) was written by
  **DeepSeek V4.1 Flash**, task `task1792663305047-032e411861ce`. The commit object's own
  author field is the neutral acceptance identity
  `Nerelan artifact acceptance <artifact@nerelan.invalid>`; it is a landing identity, not
  the writing model.
- The current writer (this task, `task-1792664324127-ba07690e0e81`) is the configured
  model for this window, `workbuddy-ai/deepseek-v4.1-flash` per the task selection record;
  its actual identity is not independently attested beyond that selection record. The
  *requested* model name is not proof of authorship.
- An independent reviewer must therefore consider **all** authors of the reused patch, not
  only the last writer: the DeepSeek V4.1 Flash env/runtime patch is co-authored here,
  since the complete diff is reused and only the PATHEXT regression is corrected.

## Reuse of the frozen correction

The complete environment correction diff from `7ff18523` was applied to the two files
it touches (`git diff HEAD 7ff18523 -- <paths>` piped into `git apply`), cleanly:

- `_BINDING_CHILD_ENV_LOCATION_ALLOWLIST` (USERPROFILE, HOMEDRIVE, HOMEPATH, APPDATA,
  LOCALAPPDATA, TEMP, TMP, TMPDIR, HOME) appended to `_BINDING_CHILD_ENV_ALLOWLIST`
  (PATH, SystemRoot, PATHEXT first), with the user-site / literal-`~` rationale.
- `_safe_child_env_value()`: single shared validator (non-empty `str`, no control chars)
  used by `build_binding_child_env` and by **both** branches of `build_role_child_env`.
- Production binding-path repair retained: `build_role_child_env` binding branch forwards
  the same location keys and validation as the helper.
- The helper (`build_binding_child_env`) repair retained.
- The real-interpreter user-site regression test and its `needs_real_interpreter` guard
  retained.

`issue1328-environment-runtime-report.md` was **not** re-added; the task asked for a new
report file below, and the frozen report remains readable in the Git object under its own
commit, so no prior evidence is altered.

## The regression this task fixes

In the reused diff the direct (no binding config) branch of `build_role_child_env`
deleted `"PATHEXT"` from its inline `direct_env_allowlist` while introducing the shared
validator. `_ensure_windows_pathext` then only saw an absent key and injected
`.COM;.EXE;.BAT;.CMD`. On a real Windows parent with e.g. `PATHEXT=.EXE;.PY` the child
silently lost the previously forwarded, valid value.

Fix (minimal, no unrelated refactor):

- Added module-level `_DIRECT_CHILD_ENV_ALLOWLIST` = PATH, SystemRoot, **PATHEXT**,
  COMSPEC, `*_BINDING_CHILD_ENV_LOCATION_ALLOWLIST`, XDG_DATA_HOME, XDG_CONFIG_HOME.
- The direct branch iterates that constant and keeps the shared
  `_safe_child_env_value` validation, so control characters and empty values are still
  dropped and a malformed PATHEXT still falls back to `_DEFAULT_WINDOWS_PATHEXT` via
  `_ensure_windows_pathext`.
- Docstring updated to state that both branches forward a valid parent PATHEXT.

Preserved unchanged: role permission config, executor-rebuilt `OPENCODE_CONFIG_CONTENT`
(the caller's inherited config is still never forwarded), the OpenCode disable flags, the
explicit allowlist / secret exclusion, location keys, and the binding/helper paths.

## Tests (exactly `tests/platform_v1/test_opencode_executor.py`)

Added:

- `test_role_direct_child_env_forwards_valid_custom_pathext` — parent
  `PATHEXT=.EXE;.PY` forwards verbatim through the direct branch; COMSPEC/location/XDG
  keys forward; a fake secret sentinel never appears; `OPENCODE_CONFIG_CONTENT` is
  rebuilt (caller key dropped) with reviewer role permissions.
- `test_role_direct_child_env_malformed_pathext_falls_back_to_default`
  (parametrized: `None`, `""`, trailing newline, `../bad`, an absolute non-extension
  string) — valid profile still forwards; on Windows the child PATHEXT is the conservative
  default, on other platforms PATHEXT is absent (no-op branch).
- `test_role_direct_child_env_pathext_matches_binding_branch` — direct and binding
  branches agree on the forwarded custom PATHEXT.

RED evidence (unfixed frozen source, isolated copy, same tests):
`pytest ...\test_opencode_executor.py -k role_direct_child_env -q` →
**2 failed, 5 passed**; both failures
`assert '.COM;.EXE;.BAT;.CMD' == '.EXE;.PY'`, i.e. the real reported regression.

GREEN evidence (worktree source):
`pytest tests/platform_v1/test_opencode_executor.py -q` → **204 passed, 1 skipped**
(skip is the pre-existing Windows-only direct-env guard).

Runner: `C:\msys64\ucrt64\bin\pytest.exe` (msys/UCRT Python 3.12) with `PYTHONPATH` set to
the worktree. The system CPython 3.13 has no `pytest`; nothing was installed.
`git diff --check` is clean.

## Not verified / limitations

- Not run: the full `tests/platform_v1` blocking suite (the msys interpreter cannot import
  `langgraph` and other optional deps; installing is prohibited here). The HOST owns full
  testing with its installed pytest.
- The real-interpreter test is a host-provisioning observation, not a live producer run.
- No live OpenCode, relay, provider or server call; no scientific or live acceptance
  claim is made.
- Exact-head CI, independent review, PR publication and merge are HOST responsibilities.

## Constraints observed

No commits, pushes, PR changes, merges, tags, releases, deployment, installs, venvs,
stash/reset/clean/restore, provider calls, secrets access, dependency or governance edits,
or changes to original evidence. Only `reverse_agent/platform_v1/opencode_executor.py`,
`tests/platform_v1/test_opencode_executor.py` and this report were written, all inside the
supplied worktree.
