# Unattended base platform v0

This baseline is a bounded integration layer, not a replacement workflow
engine, sandbox, coding loop, or model gateway.

```text
MinimalWorkItem
  -> deterministic Temporal Workflow
  -> host-side Activities
  -> OpenHands Agent Server
  -> bounded Docker sandbox
  -> LiteLLM proxy
  -> configured model provider
```

Temporal owns durable scheduling and replay. PostgreSQL is its durable store.
The reverse-agent worker owns policy resolution and calls the Agent Server over
HTTP; it does not control Docker. OpenHands owns its supported coding loop and
host-side sandbox controller. LiteLLM is the only model endpoint exposed to
OpenHands.

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
explicit local-development opt-in, not a production topology. Internal service
traffic remains on the private Compose `control` network.

Runtime workspaces live below the ignored `.var/unattended/` tree. Named
volumes `temporal-postgresql-data` and `temporal-server-data` retain local
Temporal state between ordinary container restarts. This is a development
baseline and is not a production deployment topology.
