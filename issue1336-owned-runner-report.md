# Owned CLI lifecycle correction (#1336)

This patch reuses the system-authored implementation and tests from unaccepted
custody commit `f236ede80fbcb68c29164c0d6b6bdcdeb1e1eb62`. The supervisor
corrected its blocked-reader cleanup order and exception handling after system
correction attempts failed. It is not an entirely system-produced delivery.
The accepted artifact boundary checks remain in place.

The CLI starts inside a Windows Job or POSIX process group. Every exit path
attempts to stop that owned tree before output cleanup. Windows Job closure
precedes bounded reader joins; a still-live reader's buffered pipe is not
synchronously closed. A repeated POSIX stop request never promotes an
unconfirmed result to confirmed. Exceptional cleanup uncertainty returns the
explicit `cleanup_unconfirmed` result with UNKNOWN usage and no artifact reads.
Timeouts retain parseable numeric usage as PARTIAL. PR #1337 supplies the
separate retry guard; accounting uncertainty alone is not that guard.

Local verification before publication:

- `python -m pytest -q -p no:cacheprovider tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_opencode_process_ownership.py`:
  226 passed, 1 skipped. The added regressions cover a real reader lock with
  bounded fixture release, POSIX exception cleanup, and actual executor-core
  refusal to collect artifacts on uncertain timeout, normal, and error paths.
- Independent controlled Windows Job/pipe fault injection: a parent sleeping
  for 60 seconds, inner timeout 0.2 seconds, and deliberately false cleanup
  confirmation returned in 0.225 seconds with confirmation still false. The
  outer Job confirmed every fixture process stopped; its 25-second limit did
  not fire.
- Independent real executor-core timeout fixture: returned in 1.138 seconds;
  the owned child did not complete its later write. Usage input/output 11/3
  was persisted as PARTIAL in the fixture database.
- Both OS probes checked executor source SHA-256
  `a2791fbb1f1bffb41898e5ff80d144e45c546a583bda1fc0cabfa41da6e899fe`.
- `git diff --check` passed.

These are provider-free local checks, not claims about old timed-out tasks,
upstream served-model identity, scientific results, or released capacity.
Existing UNKNOWN holds and frozen workspaces were not reconciled or reused.
Linux CI and a fresh independent exact-head review are required after
publication. Those later results belong in the PR's dated verification record.
Provider error diagnostics, availability, capability attribution, pricing,
state convergence, the remaining short test, and #1191 are still unfinished.

## Dated CI correction, 2026-10-23 10:40 UTC

The first Linux baseline on merge-main head `091a036b` found seven failures:
six lease tests mocked the replaced subprocess.run seam, and POSIX normal
parent exit exposed asynchronous descendant reaping during confirmation.
The lease fixture now mocks the owned-process seam while retaining all
bind/release/deadline assertions. The shared POSIX confirmation primitive
polls group existence for at most ten seconds; a surviving group or zombie
still returns false. Controlled-clock regressions cover both eventual
disappearance and deadline expiry.

The six focused suites (executor, ownership, runtime budget, quota inflight
wiring, agent escalation, and GoalService) passed 479 tests with one skip in
47.05 seconds after this correction. This records a local author-time check;
the subsequent exact-head Linux CI and review state are tracked on the PR.
