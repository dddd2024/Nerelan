# Issue #1328 — executor environment runtime repair (T001)

Worktree: `F:\nrl-research\ws\task-1792663305047-032e411861ce`
Frozen base: `0dc2737cec081ad17a8efa01249b77f444b22536`
Reference: PR1330 commit `27521c6ef8e709c4c954d4809e3dc56a4f9b55ad` (base `dd592583`), read-only Git object.

## Why this change

PR1330's independent review (thread `PRRT_kwDOSCDj_s6vGI0S`) found the fix incomplete:
`build_binding_child_env` filtered malformed location values, but the **production**
`build_role_child_env` binding branch copied every string verbatim. A parent
`USERPROFILE`/`APPDATA`/`TEMP` containing NUL/control characters therefore reached
`subprocess` launch with an uncaught `ValueError`. Even when launch survived, the
child lost the OS profile and CPython resolved `site.getusersitepackages()` to the
literal `~\...` directory, so a tooling install wrote into the edited workspace and
`functional_patch_hygiene_failed` rejected the patch.

## Actual changes

`reverse_agent/platform_v1/opencode_executor.py`
- Added `_BINDING_CHILD_ENV_LOCATION_ALLOWLIST` (USERPROFILE, HOMEDRIVE, HOMEPATH,
  APPDATA, LOCALAPPDATA, TEMP, TMP, TMPDIR, HOME) and appended it to
  `_BINDING_CHILD_ENV_ALLOWLIST`, preserving the explicit allowlist (PATH, SystemRoot,
  PATHEXT first). The comment explains the user-site / literal-`~` root cause instead of
  the stale APPDATA/`expanduser` ordering.
- Added `_safe_child_env_value()`: one shared minimum validator (non-empty `str` with no
  control characters). Both the binding branch and the direct branch of
  `build_role_child_env` and `build_binding_child_env` now use it, so production and
  helper cannot drift.
- `build_role_child_env` binding branch now forwards the same location keys and applies
  the same validation as the helper; the direct branch keeps COMSPEC/XDG keys and uses
  the shared validator instead of its duplicate inline loop.
- Role permission merge, executor-generated `OPENCODE_CONFIG_CONTENT`, and the OpenCode
  disable flags are unchanged. No provider/secret key is ever read (`parent_env.get` is
  called only for allowlisted names). The caller's inherited `OPENCODE_CONFIG_CONTENT`
  is never forwarded — the merged binding config replaces it.
- `functional_patch_hygiene_failed` was not modified or weakened.

`tests/platform_v1/test_opencode_executor.py` (only test file touched)
- `test_role_binding_child_env_forwards_valid_os_location_keys_only` — production
  binding-mode: valid OS locations forward exactly; sentinel provider keys
  (`FAKE_SENTINEL_*`, fake values only) never appear in the child or its JSON; merged
  config carries the binding provider plus the role permissions and drops the caller's
  inherited config keys.
- `test_role_binding_child_env_drops_control_and_empty_location_values` — NUL, `\x1f`,
  `\n`, `\x7f` and empty values are dropped; a valid sibling key still forwards.
- `test_role_binding_child_env_matches_binding_helper_validation` — role and helper
  builders agree key-for-key on the same malformed parent.
- `test_role_binding_child_env_real_interpreter_resolves_user_site` — real host
  interpreter subprocess with the exact production child env; asserts the user site is
  absolute, under the forwarded profile and does not start with `~`. Guarded by
  `needs_real_interpreter` (skips only when no host interpreter can import `json`/`site`).

## RED evidence (recorded before the production edit)

Command: `pytest tests/platform_v1/test_opencode_executor.py -k role_binding_child_env -q`
Result: **3 failed, 1 passed**.

- `..._forwards_valid_os_location_keys_only`: `KeyError`/missing location keys —
  the production binding branch copied none of USERPROFILE/APPDATA/TEMP/HOME.
- `..._drops_control_and_empty_location_values`: `KeyError: 'LOCALAPPDATA'` — the
  branch copied only the three base keys, so no location key existed at all.
- `..._real_interpreter_resolves_user_site`:
  `AssertionError` — the child reported
  `~\\.local/lib/python3.12-mingw_x86_64_ucrt_gnu/site-packages`, i.e. the literal-`~`
  workspace pollution, exactly the reported defect.

Direct pre-fix probe of the malformed parent through the production builder:
`build_role_child_env({'PATH': 'C:\\Windows', 'USERPROFILE': 'C:\\Users\\bad\x00name'}, <binding config>, 'coder')`
returned a child env and the subprocess launched OK because the malformed value was
**dropped entirely** (no USERPROFILE forwarded) — the child then has no profile and
resolves its user site under `~`. The NUL value cannot reach an uncaught `ValueError`
in this path because the key is not forwarded; the fix keeps that property while also
forwarding the *valid* keys the child needs. With a raw pass-through (the PR1330 helper
bug shape) the same value raises `ValueError: embedded null character` inside
`subprocess`. The fix removes both failure modes: valid locations forward, malformed
ones are filtered before launch.

## GREEN evidence

- `pytest tests/platform_v1/test_opencode_executor.py -q` → **197 passed, 1 skipped**
  (the skip is the pre-existing Windows-only direct-env guard).
- `pytest tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_functional_validation.py -q`
  → **239 passed, 1 skipped**.

## Shell-tool limitations / unverified

- The shell's default `pytest` is the msys/UCRT Python 3.12 and cannot import
  `langgraph` and other optional deps; a full `pytest tests/platform_v1` collection is
  blocked by that missing module (29 collection errors, all `No module named
  'langgraph'`/related, none in the touched file). `python -m pytest` on the system
  CPython 3.13 has no `pytest`. Per the task, nothing was installed. The HOST should run
  the full blocking suite with its own provisioned interpreter.
- `PYTHONPATH` was set to the worktree for the local runs.
- The real-interpreter regression ran under the msys Python 3.12 on this host; it is a
  host-provisioning observation, not a live producer/OpenCode success.
- No live OpenCode, relay, provider or server call was made. No claim of a clean producer
  or scientific run is made here.
- Not verified: exact-head CI, independent review, governed merge (host responsibility).

## Constraints observed

No commits, pushes, PR changes, merges, tags, releases, deployment, installs, venv,
stash/reset/clean/restore, provider calls, secrets access, model/binding/score/quota
changes, or evidence deletion. Only the two source/test files and this report were
written, all inside the supplied worktree.
