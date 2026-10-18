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
