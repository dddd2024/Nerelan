# Issue #1328 — environment final: test portability correction and report scope (T001)

Worktree: `F:\nrl-research\ws\task-1792669304328-6410dfdeca6d`
Base: `0dc2737cec081ad17a8efa01249b77f444b22536`
Frozen artifact under correction: commit `09733661ccc4600163f1070c897080c9592f3ba1`
(Task `task-1792664324127-ba07690e0e81`, Execution
`exec-task-1792664324127-ba07690e0e81`, Result
`21fb599778cc32a26dc2306dbab9596c3605b2feca13edcf121d2cf83dd833db`).
Prior frozen artifact it reused: `7ff18523d3e34f8aaf9c0ffa5f2a32fc32a9c0ae`
(Task `task-1792663305047-032e411861ce`, Result
`62c250460d919a3f2faee9e4e7b18d81928f28f2e6262d74492a5f57e2ca886b`).

Both commits are read as read-only Git objects. The earlier report files
(`issue1328-environment-runtime-report.md` in `7ff18523`,
`issue1328-env-final-report.md` in `09733661`) are **not** modified or rewritten;
their original facts remain available by referencing those commits. This
report does not supersede them.

## What this task changed

Scope is deliberately narrow: **test portability only, plus report clarity**.

- Corrected the cross-platform contract in
  `tests/platform_v1/test_opencode_executor.py`.
- Added pure Windows / POSIX branch regressions using `platform.system` mocking.
- `reverse_agent/platform_v1/opencode_executor.py` is **byte-identical** to the
  frozen artifact. Verified by object hash, not by inspection:

  ```text
  worktree: 55c08c77c72556bced70022bfeff65a1de8440c9
  frozen:   55c08c77c72556bced70022bfeff65a1de8440c9   (BYTE-IDENTICAL)
  ```

`tests/platform_v1/test_child_environment_isolation.py` was **not modified**; its
existing isolation tests are untouched and still pass in full.

## The defect the independent review found

The frozen test
`test_role_direct_child_env_malformed_pathext_falls_back_to_default`
unconditionally asserted the Windows default first:

```python
assert child.get("PATHEXT", ".COM;.EXE;.BAT;.CMD") == ".COM;.EXE;.BAT;.CMD"
```

and then asserted absence on non-Windows. That encodes a Windows-shaped contract
onto every platform, but the runtime contract is narrower:

- `_safe_child_env_value` drops empty strings, non-strings and any value
  containing a control character — on **every** platform.
- `_ensure_windows_pathext` is a **no-op** off Windows, so it neither rewrites
  nor invents a `PATHEXT` there.
- Consequently, on POSIX the direct branch **preserves** any non-empty,
  control-free `PATHEXT` verbatim. A simulated `platform.system == "Linux"`
  returns `../bad` and `C:\Windows\bad.exe` unchanged.

That preservation is pre-existing compatibility behavior, not a regression. The
test was wrong; the source was right for these cases. No source change was made.

## RED evidence (frozen test, POSIX platform simulated)

The frozen test file was materialised from the Git object into a scratch path
(outside any tracked file, removed afterwards) and run with
`platform.system` patched to `"Linux"`:

```text
FAILED ...::test_role_direct_child_env_malformed_pathext_falls_back_to_default[../bad]
FAILED ...::test_role_direct_child_env_malformed_pathext_falls_back_to_default[C:\\Windows\\bad.exe]
2 failed, 3 passed
```

Both failures were
`AssertionError: assert 'C:\\Windows\\bad.exe' == '.COM;.EXE;.BAT;.CMD'`.
This reproduces the reviewer's finding exactly, and confirms the failing
assertion was the test's contract, not the runtime.

## The corrected tests (exactly one file)

All in `tests/platform_v1/test_opencode_executor.py`. The Windows and POSIX
branches are separated so each asserts its own real contract, and the platform
seam is mocked with `monkeypatch.setattr(module.platform, "system", ...)` —
the same approach the existing
`tests/platform_v1/test_child_environment_isolation.py` uses. No global
`os.name` / path-class mutation.

- `test_role_direct_child_env_invalid_pathext_on_windows_uses_default`
  (parametrized `None`, `""`, `".EXE;.PY\n"`, `"../bad"`,
  `"C:\\Windows\\bad.exe"`) — simulated Windows: every non-conforming value is
  replaced by `.COM;.EXE;.BAT;.CMD`, `SystemDrive` is derived, a valid profile
  still forwards.
- `test_role_direct_child_env_dropped_pathext_stays_absent_on_posix`
  (parametrized `None`, `""`, `".EXE;.PY\n"`) — simulated Linux: shared
  validation drops these, the key is absent, and **no** Windows default is
  invented.
- `test_role_direct_child_env_preserves_nonempty_control_free_pathext_on_posix`
  (parametrized `"../bad"`, `"C:\\Windows\\bad.exe"`) — simulated Linux: the
  intentional compatibility behavior is asserted as such, so nobody can later
  "fix" the runtime into a Windows-shaped rejection without failing a test.
- Retained unchanged from the frozen artifact:
  `test_role_direct_child_env_forwards_valid_custom_pathext`,
  `test_role_direct_child_env_pathext_matches_binding_branch`,
  `test_role_binding_child_env_*` (location keys, control/empty dropping,
  helper-agreement) and the real-interpreter user-site test with its
  `needs_real_interpreter` guard.

The POSIX cases are not skipped and the source was not weakened.

## GREEN evidence

Two interpreters were used, and they are **not** interchangeable:

| Runner | Python | pytest | Result |
| --- | --- | --- | --- |
| Installed HOST CPython | 3.13.12 (MSC v.1944 64-bit) | 8.4.2 (user site `...\Roaming\Python\Python313`) | `243 passed, 1 skipped` |
| msys2 UCRT | 3.12.11 (GCC UCRT 15.2.0) | 9.1.1 | used for platform simulation |

HOST command, both required files, no installs:

```text
C:\Users\wjc27\AppData\Roaming\Python\Python313\Scripts\pytest.exe
  tests/platform_v1/test_opencode_executor.py
  tests/platform_v1/test_child_environment_isolation.py -q
-> 243 passed, 1 skipped in 5.36s
```

Split: `test_opencode_executor.py` 209 passed / 1 skipped;
`test_child_environment_isolation.py` 34 passed.

The single skip is pre-existing and unrelated:
`test_opencode_executor.py:1873` — `symlinks not supported on this platform`.
The real-interpreter test **ran** (not skipped) and passed:
`test_role_binding_child_env_real_interpreter_resolves_user_site PASSED`.

Branch-simulation runs (both directions, same file):

```text
platform.system -> "Linux":   12 passed, 198 deselected   (test_role_direct_child_env)
platform.system -> "Windows": 12 passed, 198 deselected   (test_role_direct_child_env)
```

`git diff --check` is clean. Nothing was installed; no venv was created.

## Test-visibility caveats (what each result actually means)

- The restricted worker's earlier visibility of `pytest` is **not** the same
  thing as the installed HOST CPython. The HOST CPython 3.13 at
  `C:\Program Files\Python313\python.exe` has **no** `pytest` on its own
  `sys.path` (`python -m pytest` → `No module named pytest`); the runs above
  used the separately installed user-site pytest 8.4.2 entry point. A
  restricted-worker pytest result must not be reported as a HOST result, and
  vice versa.
- No native Linux pass is claimed. All POSIX evidence here is branch
  simulation by mocking `platform.system`, which exercises the real branch
  logic but not a real Linux kernel, path module or argv. **CI is still
  required** for a genuine non-Windows observation.
- The native Windows HOST suite `opencode_executor` +
  `child_environment_isolation` remains `243 passed / 1 skipped` on this head;
  the extra branch simulation is what exposed the portability bug, and a native
  Linux run would not have caught it from this host.

## Model attribution scope

Two distinct facts, kept separate:

- **Selected / leased model.** The task record for this window names
  `workbuddy-ai/deepseek-v4.1-flash` as the cheapest qualifying selection
  (`magpie-...: cheapest_qualifying`). That is a *selection record* for the
  window.
- **Independently attested underlying model.** There is none beyond that record.
  No external attestation, provider log or signed claim is available in this
  environment, and no provider call was made to obtain one.

Therefore the *requested* or *selected* model name is **not proof of
authorship** of this diff. Both frozen commits additionally carry the neutral
landing identity `Nerelan artifact acceptance <artifact@nerelan.invalid>` in
their author field, which is an acceptance identity, not the writing model.
The reviewer must treat authorship as unverified beyond the selection record,
and must consider all authors of the reused environment patch — the
`7ff18523` and `09733661` work is carried forward here, not re-authored.

Prior report provenance claims are preserved by reference to those commits; this
report does not restate or revise them.

## Report file naming

This delivery adds `issue1328-env-portability-report.md` (this file). The
earlier `issue1328-env-final-report.md` from `09733661` is **not** rewritten;
its numbers (`204 passed, 1 skipped` on the then-current interpreter, and the
msys runner note) describe that revision and were correct for it. It is
deliberately left in the Git object rather than duplicated here, so prior
evidence stays intact and auditable.

## Not verified / limitations

- No native Linux or macOS execution. CI still required.
- The `tests/platform_v1` blocking suite as a whole was not run; only the two
  explicitly permitted files were executed.
- The real-interpreter test is a host-provisioning observation, not a live
  producer run.
- No live OpenCode, relay, provider, server or model call; no product,
  scientific or #1328-completion acceptance is claimed.
- Exact-head CI, independent review, PR publication and merge are HOST
  responsibilities. This Goal delivers execution only.

## Constraints observed

No commits, pushes, PR creation or modification, merges, tags, releases,
deployments, installs, venvs, stash/reset/clean/restore, provider/model/server
calls, secret or credential access, dependency changes, or governance edits.
No tracked file outside the two permitted test scopes was modified, and no
runtime source change was made.
