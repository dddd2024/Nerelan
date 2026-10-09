# Trusted local-client session and native browser transport

Issue #118 depends on #384: loopback and Origin do not authenticate the
caller. `LocalClientSession` provides a host-memory identity prerequisite:
256 random bits, a bounded monotonic lifetime of at most seven days,
constant-time comparison after a strict 64-character hexadecimal shape
check, and synchronized rotation and revocation. A missing, malformed,
expired or stale capability fails closed. Clock failure or rollback revokes
the session; entropy or private-bootstrap delivery failure leaves it unusable.

The combined trusted host mints after creating its services and before
starting their serving threads. Cleanup revokes before shutting down resources,
including partial startup failures. Each successful start creates a new
capability; stopping or restarting cannot preserve the previous capability.
The value has no environment variable, command-line argument, URL, HTTP
bootstrap endpoint, persistent file, TaskStore field or browser storage.
Its representation and public errors contain fixed messages only.

`TaskService` callers supply an explicitly trusted in-process
`trusted_client_receiver`. A service creating its own session requires that
receiver before opening a database or socket. Each start rotates the session
and calls the existing private `deliver` seam before starting its HTTP thread;
failed delivery revokes the capability and closes the socket. Thread-start
failure also closes and revokes. Explicit `port=0` requests an ephemeral port.
An injected `LocalClientSession` can remain caller-owned without a receiver,
but `start` still rotates it: the caller must privately deliver the new value
after every successful start. A value delivered before start is stale.

The provider-free acceptance CLI gives each of its three TaskService instances
its own receiver and sends that instance's capability header. The OpenCode
acceptance caller uses the same private delivery seam. Its HTTP client can be
tested against a disposable TaskService without running the OpenCode CLI or
calling a model. These in-process fixture checks do not prove production
browser, OpenCode execution or unattended coding acceptance.

The provider-free fixture CLI explicitly supplies synthetic execution and plan
identities to exercise the existing durable-run fences. They are fixture data,
not canonical Owner authority, and apply only to its deterministic fixture
tasks. TaskService defaults and durable identity checks remain unchanged;
an authenticated client without execution pins still receives 409 before a
durable run or workspace mutation. OpenCode and production callers require
their own applicable execution authority and are not given fixture identities.

`deliver` is an in-process seam for trusted native launcher code, not a
public API or proof that an arbitrary callback is trusted. The Windows launcher
starts the host's owned Node browser broker with private anonymous stdin IPC.
The capability stays in host and broker memory; the broker's native HTTP layer
adds it to requests only for the exact configured Task API origin and `/api/`
paths, originating from the configured frontend frame. It does not modify
renderer request headers or follow redirects. It blocks service workers,
strips credential cookies, bounds requests, responses and timeouts, and
reports fixed errors. All existing frontend HTTP clients use that one seam.

Task API GETs exposing user state and all POSTs now require exactly one current
capability header before JSON parsing, task lookup or dispatch. Missing,
duplicate, malformed, expired and stale values return a fixed 401. Origin
validation is independent: a disallowed Origin returns 403; omitting Origin
does not grant access. A factory without a private session defaults to denial.
After rejecting a POST, the handler may discard an explicitly sized bounded
body without parsing it, so Windows socket closure does not hide the response.
GET `/api/health` exposes only `{"ready":true}` for launcher readiness; OPTIONS
is preflight only and cannot read state or execute work.

The supported launcher checks the broker's exact process creation time,
executable and readiness, and retains verified ownership and fail-closed
cleanup. `-NoBrowser` starts services without delivering a browser identity;
opening an arbitrary browser tab does not authenticate it. Broker exit clears
UI readiness; host cleanup revokes the identity and stops its owned broker.
The exact existing `playwright-core` 1.62.1 dependency is a production dependency;
this change does not install packages or alter shared node_modules.

Neither this capability nor the browser `ACTIVATE` literal proves Owner policy
confirmation. All existing execution, authority, budget and publication checks
remain necessary. Model Control authentication is a separate unresolved surface.
Source tests use synthetic identities, native Node HTTP and owned loopback
fixtures, without launching a real browser or making model calls. Supported
Windows frontend flows, lifecycle cleanup and restart acceptance still require
separate actual runtime evidence. #384 and #118 remain open pending that evidence,
canonical Owner and upper authority, privileged-operation evaluation, durable
receipts and independent acceptance.

The launcher forwards the selected frontend port to Vite through npm's `--`
argument separator, together with loopback `--host` and `--strictPort`. An
occupied selected port must fail instead of silently starting on another port.
Vite's existing `runner` configuration loader avoids the bundle loader's
temporary configuration files under shared `node_modules/.vite-temp`.
Terminal broker failure or browser disconnect closes the private stdin handle
after browser cleanup, so the host's open pipe cannot retain the broker process.
Closing the supported main frontend page also terminates that private session.
Chromium can remain connected after its last window closes, so browser disconnect
alone cannot establish that the frontend is still open. The page-close event is
registered before navigation and shares the same browser and stdin cleanup.
The native child regression uses an SDK fixture that closes the page without
disconnecting the browser while the parent keeps stdin open; it is source
verification, not actual Windows browser acceptance. The recorded Windows
failure showed a closed window with the broker still alive and readiness true;
independent real-window exit and readiness evidence remains required.

The original actual Windows attempt on source `1b99c23d` failed because Vite
used port 4174 instead of the requested 18879. Its owned service groups were
cleaned up; no private browser opened. Native source regressions verify argument
forwarding and an actual broker's bounded failure exit with parent stdin open.
These checks do not establish actual browser lifecycle acceptance or prove that
shared dependency state was unchanged during that original attempt.

## Bounded delegated checker

The native browser identity admits HTTP requests; it does not confirm a policy.
Production window activation accepts exactly `policy_id`, `policy_revision` and
the complete canonical `policy` returned by `GET /api/windows/policy`.
The host obtains immutable Decision, candidate-head and command-plan pins from
the owner-controlled `REVERSE_AGENT_POLICY_AUTHORITY_PIN_JSON` environment,
never from Vite variables, browser storage or the HTTP body. Missing or changed
authority disables activation and autonomous dispatch. Confirmation provenance
identifies the delegated controller and explicitly records `personally_human=false`.

The supported delegated adapter is one standalone `validate_task` with command
ID `git_diff_check`, bound to the approved Goal idempotency key, plan task,
candidate head, instance, workspace and exact paths. It bypasses bindings and
model execution, reuses durable TaskStore leases/checkpoints, and records
`host_validation`, `model_execution_skipped=true` and `PATCH_HYGIENE`.
Patch hygiene does not prove functional acceptance or implementation by a model.
Filesystem writes, network, credentials and publication adapters are unavailable
under this policy; unsupported selected capabilities fail closed.

Windows, full canonical policies, delegation slots, claims and operation receipts
remain in the existing TaskStore SQLite database. Replays preserve spending and
terminal windows. Receipt totals use all stored rows; cursor pages retain a
stable history snapshot. The status response exposes a safe instance ID and
whether it is a workspace or an acceptance instance, without exposing its path.
An isolated acceptance database has independent history. It must not be presented
as proof that an existing workspace's tasks disappeared, nor silently merged with
that workspace. Configure `REVERSE_AGENT_TASK_DB_PATH` consistently for either
host entrypoint, or retain the combined host's existing DB-directory setting.

Fixture reopen checks verify durable records independently of real browser
acceptance. A saved SQLite file alone does not prove a successful server restart;
real restart acceptance requires a separately observed startup and readback.
