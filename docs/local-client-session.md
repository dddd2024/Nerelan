# Trusted local-client identity foundation

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
public API or proof that an arbitrary callback is trusted. A later launcher
must use private IPC to its owned browser broker and keep the value out of
renderer state, worker environments, logs and evidence. Neither a capability
nor the existing browser `ACTIVATE` literal proves Owner policy confirmation.

This phase does **not** install request authentication. Current Task API
routes and browser behavior are unchanged, and #384 remains open. Deployment
acceptance requires the subsequent default-deny HTTP guard, separate strict
Origin checks, complete route classification and rejection before dispatch,
supported trusted browser bootstrap, positive frontend flows, and actual
Windows lifecycle evidence. The primitive must not be presented as a fix for
the currently unauthenticated Task API. Canonical Owner/upper authority,
privileged operation evaluation, durable receipts and independent acceptance
remain separate requirements for #118.
