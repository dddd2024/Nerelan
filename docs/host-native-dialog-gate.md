# Native Owner dialog gate: bounded fallback for #1207

`native_owner_dialog.py` has **no production caller**, HTTP route, grant issuer,
window activation or dispatch integration. Its boolean is not authorization.
The existing #1216 HTTP 409 denial remains unchanged.

The host-side primitive displays a frozen display-only selection including Goal
ID/revision/artifact, repository, executor/binding, task, window, host lifecycle,
policy revision/digest and effective policy text, with one task, 30 minutes and
zero retries. It rejects control/non-ASCII characters to limit display spoofing.
It does not load persisted truth or verify the supplied policy digest; these are
caller assertions, not a verified Goal snapshot or effective execution policy.

The default Windows implementation requires a nonzero active console session,
visible WinSta0 and Default input/thread desktops. Services, remote sessions,
locked desktops and API errors deny. Only IDYES passes, with No as the default
button and a 60-second timeout; session visibility is checked again afterwards.
The callback injection is an in-process test seam, never an HTTP parameter.
No native dialog is opened at import/startup. Win32 behavior is tested with
mock APIs only; actual Windows desktop behavior has not been accepted manually.
An ordinary Windows dialog does not resist same-user automation or authenticate
the OS user as the repository Owner. This primitive is not that identity proof.

Blocker: TrustedHost currently forwards renderer-selected requests; Goal launch
has its own BEGIN IMMEDIATE transaction, while activation and claims have separate
admission paths. A future host-owned selection entry must load persisted truth,
resolve the exact effective policy and account binding, establish Owner identity,
and compare-and-consume a short-lived host-memory grant atomically with window
activation and launch, then fence claim admission, expiry, revocation and restart.
Connecting this boolean directly to the legacy activation API would be unsafe.

## Test-only grant preparer (P0 #1207 continuation)

`owner_grant_preparer.py` is an isolated protocol prototype with **no production
caller**, including no TrustedHost integration. Only isolated fixtures may
instantiate it. `FixturePolicy` is not a resolved production execution policy.
It loads a persisted PLANNED Goal, requires one single-mode Codex task, pinned
binding and exact repository, and verifies the configured repository workspace.
The dialog displays the entire serialized Goal, workspace, fixture policy, host
and preview window, including instructions. Oversized scopes deny without
truncation; non-ASCII data is JSON escaped.

OS YES produces a 256-bit random host-memory token valid for 30 seconds from
before the dialog. Only one outstanding selection is retained. Consumption burns
the token under a lock before checking Goal identity, expiry and the full stored
snapshot again. Revision, executor or binding changes, wrong Goal, replay and
other host instances deny. The preparer accepts no dialog callback; fixture code
alone injects the native platform callback.

`ConsentPreview` is **not production permission or a durable receipt**. There is
no atomic transaction covering consumption, Goal/window/Claim activation and
receipt persistence. Exact effective production policy and account readiness,
authenticated Owner identity, restart/revocation fencing and Claim admission
remain gaps. No HTTP bypass, production TaskStore modification, second dispatcher,
live Goal launch or model call is introduced. The three historical ACTIVE Claims
still have UNKNOWN remote effects; production rollout remains blocked. Mock
dialog tests are not Windows desktop or product acceptance.

## Transactional host admission seam (2026-10-18)

`PlatformControlStore.activate_window(..., _host_sql_admit=...)` is an **internal
SQLite transaction hook** for a future trusted-host Owner entrypoint. When a
new window is inserted, the hook runs under the **same BEGIN IMMEDIATE**
transaction, before COMMIT. The caller must supply the exact trusted-host
`_host_expected_goal_id`, and the store rejects scopes exceeding one task,
one concurrent worker, zero retries or 30 minutes. It refuses to commit until
exactly that persisted Goal is RUNNING with one QUEUED, Codex-bound Task under
the new window; an empty callback cannot leave a dispatchable window.
Host-window timestamps must be canonical UTC RFC3339 (`Z` or `+00:00`),
and the actual SQLite `julianday` parser must accept both values before any
window insert; Python-only ISO variants or extended offsets cannot strand an
ACTIVE window that SQLite will never consider dispatchable. If a
trusted SQL-only admission raises, the window and all its in-transaction SQL
writes roll back together. Identical policy
replay with a hook is rejected instead of silently returning an old window;
competing window activations remain serialized across SQLite connections.
Legacy no-hook activation and delegated-controller activation are not changed.

**Not a permission issuer:** the hook is never passed from renderer JSON,
not connected to `TrustedHost` or its HTTP handlers, and does not itself
confirm the Owner identity, verify the one-use token, select/pin a Goal,
materialize a Task, settle an orphan Claim, or dispatch a model. An authorized
future caller must verify the immutable persisted Goal and verified host-only
Owner selection *inside* this transaction, enforce the exact one-Task/30-minute/
zero-retry envelope, persist an admission receipt, and then commit. During the callback SQLite transaction control (COMMIT / ROLLBACK,
including executescript's implicit commit) is denied by an authorizer;
this prevents accidental premature commits in a trusted callback. Expiry is
checked again after acquiring the write lock and after callback return,
before final COMMIT. A malicious in-process callback could remove this
authorizer or perform external effects; this is NOT a sandbox or permission
boundary for arbitrary callback code. The trusted caller must not invoke
nondurable filesystem writes or spawn an executor.

Provider-free tests assert common-commit, rollback, replay rejection,
invalid trusted/delegated callback mixing, and two independent SQLite-host
races. Production work remains blocked until all above conditions are met.
