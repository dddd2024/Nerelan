# Headless control CLI-0: inventory and threat model

Canonical owners: #1198 (implementation), #806 (platform contract), #384 (local identity), #1206 (orphan Claim recovery), #1207 (Goal authorization).

## Status and scope

This is a provider-free, non-authoritative diagnostic. It is NOT a working headless autonomous scheduler or authenticated CLI for Goal mutations. Keep legacy acceptance cli.py separate. Source baseline: e1e333eb4493122ff7a9f55972ebca2721a11c43.

## Existing code and trust boundaries

- trusted_host.py: native owner host contains Task API, GoalService, coordinator, Model Control and session authority.
- local_client_session.py: a memory-only 256-bit session capability, rotated and revoked by host, handed to trusted native client in process. Never extract it from the browser, stdin, argv, environment, process metadata, filesystem or logs.
- trusted_client.py: browser/native bridge. The browser capability is NOT a generic OS-local service identity or Agent dispatch permission.
- task_service.py: public GET /api/health only; other private reads and every POST pass Origin and local-client authentication. Unauthenticated Task/Goal request returns 401. Do not disable this gate.
- goal_service.py and control_store.py: source of truth for Goal planning, approval, idempotency, CAS revision, Task/Claim/budget, and receipts.
- unattended_coordinator.py: Task pickup only through live bounded authorization and fenced Claim. Historical RUNNING Goal is not an active agent. Orphaned external side effects are not proved absent by a missing operation row.
- cli.py: existing legacy acceptance evidence CLI; not an owner dispatcher.
- headless_cli.py: CLI-0 only, no TaskStore read, no privileged API access, no mutations.

## CLI-0 contract

Run python -m reverse_agent.platform_v1.headless_cli doctor --json.

Doctor makes exactly one GET against a fixed local address http://127.0.0.1:8766/api/health. It suppresses ambient HTTP proxies, sends no bearer capability, allows at most 4096 bytes and uses one two-second monotonic deadline covering connect, headers and the entire bounded body read. Each socket receive uses only the remaining budget, so slow-drip responses cannot reset the deadline. It rejects every redirect. PUBLIC_HEALTH_OBSERVED/exit 0 means only that the public Task API is responding. It must NOT imply authority, available models, healthy coordinator, quota availability or running tasks.

Run python -m reverse_agent.platform_v1.headless_cli status --json.

Without host-authenticated local IPC, status returns WAITING with reason authenticated_control_transport_not_implemented and exit 50. Mutating goal, task, run, window commands return NOT_SUPPORTED/exit 50 without network or TaskStore access. Output is fixed sanitized JSON, never caller data or token.

## Threat model / security decision before CLI-1

Attackers include a same-user local executable, a prompt-injected Agent, an untrusted renderer, a stale scheduler process after reboot, a process reading argv/env, and any tool that can issue loopback HTTP requests. Localhost alone is not a principal. No bare SQL, filesystem path, or user-supplied JSON principal may grant authority. A signed Goal/window identifier from a caller is not sufficient evidence of user approval.

A future selected host-owned IPC transport could use Windows named pipes with explicit OS security descriptors, session identity and further per-request scoped proof. First evaluate mature platform mechanisms (#361) and the existing local client isolation (#384). This transport IS NOT implemented here. Avoid sharing browser bearer tokens. The host must own issue, rotation and revocation of a distinct CLI/scheduler identity. Interactive owner can request a grant but cannot mint it silently; scheduler identity is restricted to exact trusted Goal ID/revision, task, executor/binding, repository/workspace, operation, deadline, retries, concurrency and budget. All actions reuse GoalService/ControlStore/TaskStore transactions and receipts, with no second dispatcher.

Future versioned request contract should include exact authenticated principal from host (never accepted from payload), operation, expected Goal revision, Task ID, window ID, nonce/idempotency key, expiry and Claim epoch. Reject unknown operation and unsupported transport rather than inventing success. Crash, old CLAIM ACTIVE and unknown remote receipt must stay HOLD; quota or model routing must not silently substitute accounts.

## Required next phases (unfinished)

CLI-1: select host-owned IPC with security and spoofing tests, define typed request/response, scope enforcement and no-capability negative tests.
CLI-2: authenticated interactive command entrypoint; share real Goal/Task/Run IDs with desktop.
CLI-3: internal scheduler calls the SAME authenticated backend; never simulates GUI or bypasses local identity.
CLI-4: provider-free Windows host dogfood then an explicitly approved bounded one-task real model smoke after #1206/#1207/#1202 hold conditions clear.
CLI-5: full SDK and remote access remain under #806, not implemented by CLI-0.

## Tests and limits

Tests for headless_cli include fixed request target, proxy disabling, malformed response, strict bool readiness, no secret reflection, no mutations through unsupported commands, machine-readable nonzero codes and no privilege conflation. Real ephemeral localhost socket fixtures drip headers and bodies into child processes and assert completion below four seconds. Only internal socket injection changes the test port; there is no endpoint override in the CLI. Zero model/provider calls. Do not describe passing CLI-0 tests as autonomous Task/Run success.
