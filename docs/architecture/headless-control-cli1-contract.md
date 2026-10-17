# CLI-1 versioned control request contract (2026-10-17)

**Canonical architecture:** #806. **Bounded entrypoint implementation:** #1198. This is an R1 parser/test slice on `main` without dependency on unmerged CLI-0 PR #1211. It does not add an IPC server, user identity or scheduler.

## Components and status

`reverse_agent/platform_v1/control_contract.py` owns a **pure** `nerelan-control/v1` request envelope. It accepts only a bounded UTF-8 JSON object with exactly `protocol`, `operation`, `request_id`, and `args`. All request keys are unique; NaN/Infinity, extra fields, wrong types, unknown operations and oversized bytes fail with static error codes. Output objects do not echo untrusted caller bytes. `ControlRequest` is immutable and explicitly untrusted; constructing one never creates an authorization principal.

The parser reserves `doctor`, `status`, `goal.create/inspect/plan/approve/launch`, `task.list/inspect`, `run.status/watch/stop`, `window.status` as versioned operation names. Parsing is **not** endpoint support. No transport or operation handler is installed. Every valid parsed request sent to `unavailable_response` yields `WAITING`, `authenticated:false`, `dispatch_permitted:false`, `execution_started:false`.

Example **schema-only** request (not runnable or approved):

```json
{
  "protocol": "nerelan-control/v1",
  "operation": "goal.launch",
  "request_id": "req-demo-20261017",
  "args": {
    "goal_id": "goal-1790000000000-abcdef012345",
    "expected_revision": 3,
    "window_id": "window-1790000000000-abcdef012345",
    "repository": "dddd2024/Nerelan",
    "executor_kind": "codex",
    "binding_ref": "binding-demo",
    "policy_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "idempotency_key": "launch-demo-1234"
  }
}
```

**Do not feed this example to a real executor:** the values do not attest a real owner-approved Goal/window. The server must derive authenticated principal, trusted Goal revision and approved execution policy independently. A policy digest or request_id sent by a client proves neither identity nor scope.

## Invariants before any hosted CLI-2 or internal CLI-3 dispatch

1. **Transport:** only host-owned local IPC (design under #361/#384). Loopback, absence of Origin, filesystem read access or a copied browser session bearer is not authority. Fail closed if native host is absent.
2. **Principals:** at least interactive Owner and restricted internal scheduler; credentials are issued, scoped, rotated and revoked by host. Do not accept `principal`, `capability`, bearer, OS user or identity fields in JSON. An interactive requester cannot mint approval by sending `goal.approve`.
3. **Mutations:** secure human-reviewed Goal ID/revision, task, repository, workspace, executor/binding, allowed operation, time window, concurrency and cost budget must be checked by shared `GoalService`/`ControlStore` inside durable CAS/Claim admission. Request schema validation cannot authorize anything.
4. **Idempotency:** `goal.create/plan/approve/launch` and `run.stop` require bounded idempotency keys; the host must persist and compare key + canonical request digest, never treat repeated key for a different Goal/revision as equivalent. The present parser does not track prior requests.
5. **Resume:** #1206 old ACTIVE Claims and unknown external terminal receipts are not replay rights. A previous `RUNNING` Goal is not a live Agent. Unknown spending is UNKNOWN, not zero.
6. **Visibility:** read-only `task.list`, `run.watch`, private `status` still require authenticated identity; only CLI-0 public GET /api/health is unauthenticated. Never claim doctor means provider/model available.

## Verification and next exact deliverable

Tests run entirely in memory, monkeypatch IO and never open TaskStore or invoke a provider. The next task is a host-owned principal/IPC threat-model decision plus a real negative test proving an unrelated same-machine process cannot invoke a privileged operation. Only then bind this parser to a shared application service, and finally demonstrate one **explicitly Owner-approved** provider-free Goal through GUI and CLI, with matching Task/Run/receipt IDs. CLI-1 alone is not an agent, not production dispatch and not a claim of #1198 completion.
