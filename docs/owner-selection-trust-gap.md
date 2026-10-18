# P0 #1207: human selection trust gap (bounded increment)

Audited base: `59c0ec8e8f23207ddd2648ed022d466d117560a2` (Draft #1210).
This increment disables HTTP Owner window activation. It does not restore
human-approved execution, introduce a receipt issuer, or retrofit historical
windows/claims. Delegated-controller activation retains its separate authority.

## Actual trust path

- `trusted_host.run_combined_trusted_host` delivers `LocalClientSession` identity
  to `TrustedClient.start` through private stdin. Session identity authenticates
  a native client lifecycle; it contains no human confirmation or Goal snapshot.
- `frontend/trusted-client.mjs:forwardTaskRequest` forwards renderer-selected
  API paths and request bodies with the native capability. It checks frame and
  API origins, but provides no independent human-selection ceremony. A client
  nonce, selected_goal_id, ACTIVATE string or JSON human_confirmed flag has the
  same untrusted provenance as the selected executor/revision.
- `task_service` previously routed unpinned `/api/windows/activate` to
  `AutonomyService.activate`, whose legacy policy validation accepts caller
  identity and confirmation. It now returns 409
  `owner_selection_confirmation_unavailable` for every unpinned activation,
  including broad windows that could evade a strict-shape-only guard. Pinned
  routing still calls `activate_policy`; payload flags cannot select that mode.
- Delegated `activate_policy` requires the loader's exact canonical policy and
  revision, records DELEGATED_CONTROLLER provenance, and persists authority via
  `PlatformControlStore.activate_policy_window`. This is controller authority,
  not evidence that the human selected a Goal.
- `GoalService.launch` uses BEGIN IMMEDIATE for materialization. Its strict
  one-Goal test binds the first launched Goal, not a human selection.
  `PlatformControlStore.claim_task` rechecks task/Goal/revision/executor/binding
  under BEGIN IMMEDIATE before claims and budget reservations. Consistency with
  a caller-selected Goal does not prove human authorization.

## Required host-native interaction before Owner activation can return

A trusted host-owned confirmation surface must independently show the exact
immutable Goal revision/artifact digest, repository, executor/account binding,
window identity and bounds, policy revision/digest, and host lifecycle. A human
must confirm there through an input path unavailable to renderer requests or
agents. An ordinary browser click or native token attached to arbitrary renderer
HTTP is insufficient. The UI/input trust boundary itself needs review.

Only after that event may host-private code issue an immutable selection record.
Its issuer cannot be an API that accepts client assertions of confirmation. Store
and consume the record atomically with activation/admission using a unique
single-use identifier and exact snapshot comparison. Fence revocation, expiry,
policy changes, process restart and cross-window replay; recheck authority at
launch and claim before allocating budget. No issuer or synthetic receipt is
implemented here because the required human input anchor is absent.

## Scope and verification meaning

The legacy in-process activation API remains for synthetic fixtures; it is not
an Owner approval API. Read models, stop operations and existing host result-only
recovery are unchanged. Historical strict windows still need separate remediation
before executing new work; this increment alone is not an end-to-end admission
proof. No production TaskStore or live host was inspected or modified.

HTTP negative tests authenticate with a real synthetic LocalClientSession and
assert no database writes or activation/model dispatch for arbitrary first Goal,
wrong revision/executor/binding, forged receipts/nonces, stale policy, replay,
and multiple windows. Without a trusted proof even a matching tuple is denied;
these are absence-of-authority tests, not a receipt verifier. Existing strict
Goal tests check mismatches and durable result-only recovery. Goal/run read-model
fixtures now explicitly set up windows in process; production HTTP denial remains
tested. All tests are provider-free and do not establish product acceptance.

## Local QA commands

```
python -m pytest tests/platform_v1/test_goal_service.py tests/platform_v1/test_autonomy.py tests/platform_v1/test_autonomy_window_lifecycle.py tests/platform_v1/test_task_client_auth.py tests/platform_v1/test_task_service.py --basetemp .tmp-owner-selection-final-pytest -q
python -m pytest tests/platform_v1/test_unattended_coordinator.py tests/platform_v1/test_execution_runtime_budget.py tests/platform_v1/test_trusted_host.py --basetemp .tmp-owner-selection-claims-pytest -q
git diff --check
```

The initial first command used `.tmp-owner-selection-pytest`: 266 passed and
one Windows connection-abort failure exposed a response-before-body-consumption
problem. The guard now consumes the existing bounded JSON body before denial;
the final command above reran the entire selected set: **267 passed in 90.34s**. Scratch basetemp trees
are untracked and must not be staged. No CI, frontend build, provider call,
production execution, independent review or GitHub mutation was performed.

Supplemental coordinator/budget/trusted-host result: **261 passed, 3 skipped
in 468.28s**. Final `git diff --check`: passed. Results describe the local
uncommitted diff over the audited base, not a new commit or CI verdict.
