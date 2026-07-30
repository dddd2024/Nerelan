# Unattended base platform v0

This baseline is a bounded integration layer, not a replacement workflow
engine, sandbox, coding loop, or model gateway.

```text
MinimalWorkItem
  -> deterministic Temporal Workflow
  -> host-side Activities
  -> thin trusted SandboxController
  -> one bounded OpenHands Agent Server Attempt container
  -> LiteLLM proxy
  -> configured model provider (or the test-only provider-free fixture)
```

Temporal owns durable scheduling and replay. PostgreSQL is its durable store.
The reverse-agent worker owns policy resolution and does not control Docker.
The separate thin trusted `SandboxController` is the sole Docker authority and
launches the pinned OpenHands Agent Server image once per Attempt. OpenHands
continues to own its coding loop and local Terminal/File Editor execution, but
that execution occurs inside the disposable bounded Attempt container.
LiteLLM is its only reachable model endpoint.

LiteLLM v1.94.0 uses its native database-backed Virtual Key mechanism. The
existing PostgreSQL component hosts a separate `litellm` database owned by a
non-superuser `litellm` role; that role is denied the Temporal databases. A
one-shot idempotent bootstrap installs the synthetic-audit key with only model
`unattended-v0`, a USD 1 daily budget, 10 RPM, 50,000 TPM, one parallel
request, and only chat-completion plus model-discovery routes. The key type is
`llm_api`, not management.

The development stack derives its Temporal layout from the maintained
`temporalio/samples-server` PostgreSQL Compose example. Start the pinned stack
from WSL2/Linux after creating a local `.env` for non-provider service
credentials and a temporary `0600` provider file outside the repository:

```bash
cd deploy/unattended
export UNATTENDED_OPENAI_API_KEY_FILE=/tmp/reverse-agent-openai-api-key
python -m reverse_agent.unattended.cli secret-preflight
docker compose -f compose.yaml up -d --wait
```

`UNATTENDED_OPENAI_API_KEY_FILE` is a non-secret path. Compose mounts that file
only into LiteLLM; it does not put the provider value in any service
environment or expose it to OpenHands, the worker, sandbox, Temporal, or
PostgreSQL.

`UNATTENDED_LITELLM_EXECUTOR_KEY_FILE` is likewise a non-secret path to a
temporary external `0600` file containing generated non-provider material.
Compose mounts it into the one-shot key bootstrap and the trusted
sandbox-controller worker only. The controller places the bounded Virtual Key
in the OpenHands LLM request over stdin to the fixed Attempt transport; it is
not a container environment variable, Docker argument, URI, process title, or
metadata field. The Agent Server never receives `LITELLM_MASTER_KEY`.

The Compose baseline creates the Temporal `default` namespace automatically and
idempotently. The same command is valid for a fresh project and after a
`docker compose down` that retains its named volumes; no manual schema or
namespace command is part of the startup contract.

The `runtime-proof` profile also creates a fixed `attempt-workspaces` named
volume. A one-shot, network-isolated bootstrap with no Docker socket or secrets
sets its root to owner/group `10001:10001` and mode `0750`, then exits. The
long-lived controller runs as `10001:10001`, validates the root identity and an
atomic write/rename/delete probe, and provisions mode-`0700` deterministic
Attempt directories before launch. The Agent receives only its exact volume
subpath; it cannot mount or mutate the root or sibling Attempts.

Published development ports default to
`${UNATTENDED_BIND_ADDRESS:-127.0.0.1}`. Setting a broader address is an
explicit local-development opt-in, not a production topology. Internal
control-plane traffic remains on the private Compose `control` network.
LiteLLM is additionally attached to the internal `model-executor` network.
Attempt containers join only `model-executor`; Temporal, PostgreSQL, Canvas,
and the other control services do not.

Agent Server port 8000 is not published by the long-lived Compose stack or the
Attempt launch profile. Audit control stays at the trusted Docker boundary;
the ordinary worker receives neither a Docker socket nor an additional
network path into the Attempt. The controller uses a fixed Docker-exec JSON
transport to `127.0.0.1:8000`; callers cannot select a container, URL, method
outside the allowlist, header, endpoint, command, or callback.

The `runtime-proof` Compose profile adds the dedicated controller worker and a
test-only fixed provider-free fixture. The Temporal Workflow then executes the
real OpenHands conversation create/run lifecycle, the fixture selects the
Terminal tool, the Attempt creates and reads
`provider-free-runtime-proof.txt`, the adapter collects a sanitized
`TaskSubmission`, and cleanup removes the Attempt. This proves the integration
path without claiming a real provider call.

Agent Canvas is intentionally behind the non-default `deferred-canvas` profile.
The current Gate 2 topology is API/probe oriented and does not expose an
Attempt Agent Server port to a browser. A unified Web Console and a bounded
Controller-mediated browser route require a later Work Item.

Runtime workspace identity still derives from
`.var/unattended/{workspace-id}/{attempt}`, but its bytes live in the fixed
`attempt-workspaces` named volume. Named volumes `temporal-postgresql-data` and
`temporal-server-data` retain local Temporal state between ordinary container
restarts. This is a development baseline and is not a production deployment
topology.
