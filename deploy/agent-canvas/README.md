# Agent Canvas deployment reference (Platform V1)

This directory holds the pinned, trusted-host deployment reference for the
OpenHands Agent Canvas + Codex ACP vertical slice. It is **not** a custom
frontend — it is a thin deployment manifest that pins component versions,
image digests, and configuration for a trusted-host live run.

## Pinned components

See `docs/platform_v1/component-lock.json` for the machine-readable lock.
Summary:

| Component | Version | Source |
|-----------|---------|--------|
| `@openhands/agent-canvas` | `1.6.1` (v1.6.0 lineage) | npm |
| `@openhands/typescript-client` | `1.34.0` (bundled) | npm |
| OpenHands runtime image | `0.61-nikolaik` | `docker.openhands.dev/openhands/runtime` |
| OpenHands app image | `0.61` | `docker.openhands.dev/openhands/openhands` |

## Live-probe prerequisites

The live compatibility probes (Gate 1, items 4-7) are **opt-in** and require:

- A trusted host with Docker and `uv` installed.
- Node `>= 22.12.0` (Agent Canvas engine requirement).
- Python `3.12+` for the OpenHands CLI launcher.
- Explicit opt-in: set `PLATFORM_V1_LIVE_PROBE=1` in the host environment.
- A GitHub Token and Codex login file available **only** on the trusted host,
  mounted via read-only environment — never written to the repo, task
  workspace, logs, or commit artifacts.

## Credential isolation

The deployment reference never bakes credentials into images or config:

- `GITHUB_TOKEN` is read from the host environment at runtime only.
- Codex login files are bind-mounted read-only into the container and are
  not copied into the task workspace or any git-tracked path.
- The `.gitignore` entries prevent accidental commit of credential files.

## Restart recovery

Execution state is recoverable after restart because:

- The deterministic `execution_id` (derived from Issue number + base SHA)
  is stable across restarts.
- The `pr_marker` is deterministic, so a restarted run re-identifies the
  same Draft PR without creating a duplicate.
- The accepter re-derives truth from Git state and CI checks, not from
  in-memory agent state, so a restart never loses or fabricates evidence.
