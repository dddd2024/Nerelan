# ADR-001: Platform V1 Component Compatibility

Status: PR97_CODE_REWORK_COMPLETE_AWAITING_TRUSTED_HOST_LIVE_PROBE
Date: 2026-08-02
Decision: Pin Agent Canvas v1.6.0 lineage; use v1.6.1 for npm installation; live compatibility not yet verified

## Context

Platform V1 (Issue #96) requires a pinned compatibility probe before broad
implementation. The Work Item pins Agent Canvas to v1.6.0 and requires
selecting compatible OpenHands Agent Server, Software Agent SDK, and Codex
ACP versions with recorded version, image digest, license, and compatibility
evidence.

The live probe (Agent Canvas startup, Agent Server health, WebSocket/event
channel, isolated workspace, Codex ACP authentication, restart recovery)
requires a trusted host with Docker and explicit opt-in. This ADR documents
the pinned versions and compatibility evidence gathered from public
registries; exact image digests and live probe results require trusted-host
verification before activation.

## Findings

### Agent Canvas v1.6.0 — npm tombstone

- npm package: `@openhands/agent-canvas`
- v1.6.0 was **tombstoned** (unpublished) from the npm registry.
- v1.6.1 (2026-07-24) was released to **recover the npm publish** after the
  tombstone. Release note: "fix(release): recover npm publish after
  tombstoned 1.6.0" (OpenHands/agent-canvas#1940).
- The v1.6.0 source tag exists in `github.com/OpenHands/agent-canvas`
  (referenced in the v1.6.1 full changelog:
  `OpenHands/agent-canvas@v1.6.0...v1.6.1`).
- v1.6.1 is the same release lineage as v1.6.0; it is not a feature bump.

**Decision:** Pin to the v1.6.0 lineage. For npm installation use v1.6.1
(the recovered publish). For source builds the v1.6.0 tag is available.
This is not a fork, not a custom frontend, and not a version incompatibility
— it is a recovered npm publish of the same release.

### Agent Canvas v1.6.1 — npm metadata

- Package: `@openhands/agent-canvas@1.6.1`
- License: MIT
- Repository: `github.com/OpenHands/agent-canvas`
- gitHead: `43f091baf135142ed6c146f888f44a957141193f`
- dist.shasum: `6406a8e09aa66a636524f199a04f5e912e2a3635`
- dist.integrity: `sha512-YNr8xzPGEK0OEU6ISTE5Mzk3MffUxqfzwmd5qu6CCGTwXW+PQpT17/vSlyQkeMh83UPYJTFCEqyelptKDFnIvg==`
- SLSA provenance attestation present
- Engines: node >= 22.12.0
- Key dependency: `@openhands/typescript-client@1.34.0`

### OpenHands sub-component versions

From the OpenHands GitHub release notes:

| Release | software-agent-sdk | automation | typescript-client |
|---------|--------------------|------------|-------------------|
| v1.6.x  | < 1.38.0           | < 1.4.1    | 1.34.0            |
| v1.7.0  | 1.38.0             | 1.4.1      | —                 |
| v1.8.0  | 1.39.1 (agent-server) | 1.5.0   | 1.36.1            |

- v1.7.0 (2026-07-29): "chore: bump software-agent-sdk to 1.38.0 and
  automation to 1.4.1"
- v1.8.0 (2026-07-30): "chore: bump agent-server 1.39.1, automation 1.5.0,
  typescript-client 1.36.1"

At v1.6.1 the bundled `@openhands/typescript-client` is 1.34.0 (confirmed
from npm metadata). The software-agent-sdk and automation versions at v1.6.x
are prior to 1.38.0 and 1.4.1 respectively; exact versions require
live-host verification of the installed package set.

### ACP (Agent Client Protocol)

- Repository: `github.com/agentclientprotocol/agent-client-protocol`
- ACP is the protocol that connects Agent Canvas to multiple agent
  backends (OpenHands, Codex CLI, Claude Code, Gemini CLI).
- Codex CLI supports ACP.
- The ACP spec is still evolving; exact spec version requires live-host
  verification against the installed Codex CLI version.

### OpenHands Docker images

- OpenHands documentation references:
  `docker.openhands.dev/openhands/runtime:0.61-nikolaik` and
  `docker.openhands.dev/openhands/openhands:0.61`.
- Exact image digests for the v1.6.x lineage require live-host
  `docker pull` and `docker inspect --format='{{.RepoDigests}}'`.

## Compatibility assessment

| Probe                                         | Status                     |
|-----------------------------------------------|----------------------------|
| Agent Canvas v1.6.0 available on npm          | No — tombstoned; use v1.6.1 |
| Agent Canvas v1.6.1 available on npm          | Yes — MIT, SLSA provenance |
| v1.6.0 source tag available on GitHub         | Yes                        |
| @openhands/typescript-client version pinned   | Yes — 1.34.0               |
| OpenHands sub-component versions documented   | Yes — ranges confirmed     |
| ACP protocol documented                       | Yes — repo confirmed       |
| Exact Docker image digests                    | Pending trusted-host probe |
| Live startup / WebSocket / workspace probe    | Pending trusted-host probe |
| Codex ACP authentication probe                | Pending trusted-host probe |
| Restart recovery probe                        | Pending trusted-host probe |

## Decision

1. Pin Agent Canvas to the **v1.6.0 lineage**. Use `@openhands/agent-canvas@1.6.1`
   for npm installation (v1.6.0 was tombstoned). The v1.6.0 tag is available
   for source builds.
2. Pin `@openhands/typescript-client@1.34.0` (bundled with agent-canvas v1.6.1).
3. Reference OpenHands sub-component version ranges from release notes;
   exact installed versions and Docker image digests require trusted-host
   verification before the first live run.
4. The live compatibility probes (items 4-7 of Gate 1) are **opt-in** and
   require a trusted host with Docker. They are not executable in the
   provider-free CI environment. The adapter implementation and provider-free
   tests do not depend on live probe results.
5. No custom frontend, no fork, no sandbox closure, and no credential
   exposure is required.

## Consequences

- The thin adapter layer can be implemented and tested without live probes.
- Provider-free tests validate contract, policy, idempotency, and acceptance
  logic without real provider credentials.
- Live activation on a trusted host requires a separate opt-in step to:
  verify exact image digests, run the startup/WebSocket/workspace probes,
  verify Codex ACP authentication, and verify restart recovery.
- If any live probe fails, the status becomes `BLOCKED_COMPONENT_COMPATIBILITY`.
