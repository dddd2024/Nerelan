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
  -> configured model provider
```

Temporal owns durable scheduling and replay. PostgreSQL is its durable store.
The reverse-agent worker owns policy resolution and does not control Docker.
The separate thin trusted `SandboxController` is the sole Docker authority and
launches the pinned OpenHands Agent Server image once per Attempt. OpenHands
continues to own its coding loop and local Terminal/File Editor execution, but
that execution occurs inside the disposable bounded Attempt container.
LiteLLM is its only reachable model endpoint.

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

The Compose baseline creates the Temporal `default` namespace automatically and
idempotently. The same command is valid for a fresh project and after a
`docker compose down` that retains its named volumes; no manual schema or
namespace command is part of the startup contract.

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
network path into the Attempt.

Runtime workspaces live below the ignored `.var/unattended/` tree. Named
volumes `temporal-postgresql-data` and `temporal-server-data` retain local
Temporal state between ordinary container restarts. This is a development
baseline and is not a production deployment topology.
