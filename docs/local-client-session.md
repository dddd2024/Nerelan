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
