# Long-term Implementation Plan v2

## Status and authority

`ACCEPTED_BASELINE`

This roadmap is the sequencing authority after the P0 Architecture Constitution. It does not authorize execution. Every phase requires its own Work Item and the risk-appropriate authorization described in `docs/architecture/governance-cost-model.md`.

## Fixed sequence

```text
P0  Architecture Constitution
P1  PR #9 Exact-head Integration and Freeze
P2  Repository Hygiene and Legacy Containment
P3  Analysis Trust Domain Kernel
P4  Safe Static Evidence Pipeline
P5  Binary Evidence Firewall
P6  Claim / Counterevidence Ledger
P7  Provider Contract and Action Provenance
P8  Sandbox Executor
P9  Falsification-driven Validation
P10 Analysis Capsule
P11 Durable Binary Analysis LangGraph Runtime
P12 BMAD and GitHub Adapters
P13 Trust Workbench
P14 Trusted Reverse-solving Application
P15 Crash / Patch / Malware / Firmware Adapters
P16 Production Hardening
```

Completion is evidence-based; calendar estimates never replace acceptance criteria.

## P0 — Architecture Constitution

- **Entry criteria:** replacement Decision approved; PR #9 exact head unchanged; generated fast Command Plan and preflight pass.
- **Risk tier:** R1.
- **Allowed scope:** architecture documents, ADRs, roadmap consistency, current-round gate/report evidence.
- **Forbidden scope:** source/tests/dependencies/workflows, runtime stores, providers, binary execution, PR #9 mutation.
- **Deliverables:** seven architecture authorities, ADR-001..010, this roadmap.
- **Tests:** document consistency, allowlist diff, control-plane tests, report/execution-log/final-check.
- **Acceptance:** `ARCHITECTURE_CONSTITUTION_ACCEPTED`; all Required Audit answers concrete.
- **Rollback:** revert P0 documentation commits; retain replacement Decision and failed-round history.
- **Unlock:** P1 only.

## P1 — PR #9 Exact-head Integration and Freeze

- **Entry criteria:** P0 accepted; PR #9 remains Draft/open/unmerged at `43418818af61d9be3208d2444fd6ce5120f73fab`; exact-head checks re-observed.
- **Risk tier:** R2 because merge mutates mainline history.
- **Allowed scope:** compare current main, preserve accepted ancestry, authorized integration, mainline verification, frozen-baseline record.
- **Forbidden scope:** rebase, squash, force-push, feature expansion, P2 hygiene.
- **Deliverables:** integration Decision, merge receipt, `FROZEN_BASELINE` identity.
- **Tests:** exact-head CI, ancestry verification, mainline regression and state-gate checks.
- **Acceptance:** accepted commits are ancestors of integrated main and checks bind the integrated SHA.
- **Rollback:** use repository-approved revert; never rewrite accepted ancestry.
- **Unlock:** P2 only.

## P2 — Repository Hygiene and Legacy Containment

- **Entry criteria:** P1 frozen baseline exists; storage ownership and legacy lifecycle are accepted.
- **Risk tier:** R2 for movement/retention changes.
- **Allowed scope:** stop new runtime artifacts in Git, introduce refs/digests, inventory mirrors, disable new legacy writers, prepare read-only compatibility.
- **Forbidden scope:** destructive deletion, Trust Domain implementation, workflow feature expansion.
- **Deliverables:** hygiene policy, migration inventory, retention/rollback plan, legacy containment evidence.
- **Tests:** fixture preservation, reference resolution, no new runtime-artifact diffs, rollback rehearsal.
- **Acceptance:** new work no longer writes ordinary runtime evidence to source commits; no facts have dual writers.
- **Rollback:** restore writer routing within the documented window without deleting new artifacts.
- **Unlock:** P3.

## P3 — Analysis Trust Domain Kernel

- **Entry criteria:** P2 containment accepted; JSON Schema/version policy frozen.
- **Risk tier:** R1.
- **Allowed scope:** pure domain values, schemas, ports, repository contracts, deterministic fixtures.
- **Forbidden scope:** provider execution, dynamic analysis, UI, durable workflow.
- **Deliverables:** versioned schemas and pure semantics for AnalysisRun, identities, Evidence, Claim revisions, validation/action/capsule references.
- **Tests:** schema round trips, invariant/property tests, forbidden-dependency architecture tests.
- **Acceptance:** domain has no framework/tool/DB-driver dependencies and enforces immutability/version rules.
- **Rollback:** revert additive schema/kernel changes before persistent production data exists.
- **Unlock:** P4.

## P4 — Safe Static Evidence Pipeline

- **Entry criteria:** P3 schemas/ports accepted; S0/S1 policy available.
- **Risk tier:** R1, elevated to R2 for new tool/dependency installation.
- **Allowed scope:** hashing, headers, strings, pure parsing, static tools that never execute the target.
- **Forbidden scope:** debugger/emulator/target execution, networked provider, Claim verification by tool exit.
- **Deliverables:** deterministic S0/S1 ingestion and ArtifactRefs/EvidenceUnits.
- **Tests:** hostile/malformed fixtures, determinism, sample binding, no-execution assertions.
- **Acceptance:** outputs are immutable, tainted, provenance-complete, and target execution is impossible.
- **Rollback:** disable adapters and retain imported evidence as historical/unaccepted.
- **Unlock:** P5.

## P5 — Binary Evidence Firewall

- **Entry criteria:** P4 evidence ingestion stable; trust/taint policies versioned.
- **Risk tier:** R1.
- **Allowed scope:** normalization, taint propagation, provenance validation, evidence/influence separation, telemetry promotion adapters.
- **Forbidden scope:** automatic Claim verification, dynamic execution, action authorization.
- **Deliverables:** firewall policy and rejection/quarantine paths.
- **Tests:** prompt/log/path injection fixtures, provenance gaps, stale evidence, telemetry non-promotion.
- **Acceptance:** untrusted inputs cannot select authority or silently enter accepted evidence.
- **Rollback:** quarantine new normalized records; preserve raw immutable artifacts.
- **Unlock:** P6.

## P6 — Claim / Counterevidence Ledger

- **Entry criteria:** P5 firewall accepted.
- **Risk tier:** R1.
- **Allowed scope:** Claim identity/revisions, evidence relations, counterevidence, confidence and validation states.
- **Forbidden scope:** provider execution, automatic verified status, UI write authority.
- **Deliverables:** append-only ledger and current-revision projection.
- **Tests:** revision immutability, contradictory evidence, stale support, concurrent update semantics.
- **Acceptance:** history is never overwritten and verified cannot be reached without validation evidence.
- **Rollback:** revert projection/adapters while preserving ledger records.
- **Unlock:** P7.

## P7 — Provider Contract and Action Provenance

- **Entry criteria:** P6 ledger accepted; engineering/analysis bridge contracts frozen.
- **Risk tier:** R2.
- **Allowed scope:** provider ports, capability descriptions, proposals, authorizations, receipts, idempotency keys; fixture-only adapters.
- **Forbidden scope:** unknown binary execution, production credentials, host-repository writes.
- **Deliverables:** provider contract and non-executing conformance suite.
- **Tests:** expiry/scope denial, replay/idempotency, receipt completeness, tainted-command injection.
- **Acceptance:** no provider runs without exact current authorization and every attempt yields an immutable receipt.
- **Rollback:** disable provider registry; preserve receipts.
- **Unlock:** P8.

## P8 — Sandbox Executor

- **Entry criteria:** P7 contracts accepted; isolated infrastructure and human approval available.
- **Risk tier:** R3.
- **Allowed scope:** S2/S3 disposable workers, limits, network policy, isolated outputs, cleanup/receipt integration.
- **Forbidden scope:** host credentials/home/repository write access, shared persistent sample workers, default network.
- **Deliverables:** sandbox executor with independently verified isolation.
- **Tests:** escape/credential/mount/network/resource/cleanup adversarial suite.
- **Acceptance:** isolation controls and destruction are observed, not inferred; failures block reuse.
- **Rollback:** disable dynamic tiers and return to S0/S1 only.
- **Unlock:** P9.

## P9 — Falsification-driven Validation

- **Entry criteria:** P8 executor accepted; Claim ledger available.
- **Risk tier:** R2 or R3 by experiment.
- **Allowed scope:** explicit hypotheses, discriminating experiments, counterexample search, immutable results.
- **Forbidden scope:** confirmation-only validation, policy bypass, overwriting failed results.
- **Deliverables:** ValidationExperiment/Result orchestration and freshness rules.
- **Tests:** falsifying fixtures, nondiscriminating experiments, stale/environment mismatch, retry idempotency.
- **Acceptance:** accepted validation distinguishes hypotheses and preserves negative results.
- **Rollback:** demote affected Claims to unvalidated; preserve results.
- **Unlock:** P10.

## P10 — Analysis Capsule

- **Entry criteria:** P9 validation accepted; artifact retention/export policy stable.
- **Risk tier:** R1, R2 when externally publishing sensitive artifacts.
- **Allowed scope:** deterministic manifests, digest verification, policy snapshots, portable projections.
- **Forbidden scope:** mutable sealed manifests, embedding secrets/raw payloads by default, release without authorization.
- **Deliverables:** CapsuleManifest creation, verification, and redacted export.
- **Tests:** tamper detection, missing artifacts, schema compatibility, deterministic manifest, redaction.
- **Acceptance:** a capsule independently resolves and verifies its accepted evidence/Claim/validation graph.
- **Rollback:** revoke distribution and issue a new version; never overwrite sealed manifests.
- **Unlock:** P11.

## P11 — Durable Binary Analysis LangGraph Runtime

- **Entry criteria:** P3-P10 contracts and execution boundaries accepted.
- **Risk tier:** R2.
- **Allowed scope:** persistent checkpoints, separate namespace, interrupt/resume, idempotent nodes, bounded retry, human approval, ports.
- **Forbidden scope:** shared Development graph/state, second AgentRunner, Claim authority in checkpoints.
- **Deliverables:** durable Binary Analysis graph and recovery procedures.
- **Tests:** crash/replay/resume, duplicate action prevention, checkpoint migration, terminal-state correctness.
- **Acceptance:** workflow recovery preserves domain truth and cannot duplicate high-risk actions.
- **Rollback:** stop dispatch and resume from a verified prior checkpoint/schema version.
- **Unlock:** P12.

## P12 — BMAD and GitHub Adapters

- **Entry criteria:** Development Workflow baseline frozen; runtime/authority ownership stable.
- **Risk tier:** R2 due network and repository mutation.
- **Allowed scope:** read planning artifacts, GitHub Work Item/PR observations, bounded authorized mutations through ports.
- **Forbidden scope:** planning artifacts as command authority, copied mutable GitHub truth, autonomous merge/release.
- **Deliverables:** adapters with freshness, provenance, and permission controls.
- **Tests:** stale/forged observations, permission denial, rate/network failures, no duplicate truth.
- **Acceptance:** GitHub remains authoritative and all writes are explicit, bounded, and readable back.
- **Rollback:** disable write adapters and retain read-only planning/work-item flow.
- **Unlock:** P13.

## P13 — Trust Workbench

- **Entry criteria:** P6/P9/P10 projections stable; interface threat model accepted.
- **Risk tier:** R1.
- **Allowed scope:** read projections, Claim/counterevidence comparison, validation/capsule inspection, human approval surfaces.
- **Forbidden scope:** UI as authority, direct database/provider writes, hidden counterevidence.
- **Deliverables:** Web/API workbench through application ports.
- **Tests:** accessibility, authorization, hostile rendering, stale projections, approval clarity.
- **Acceptance:** users can audit why a Claim is accepted/rejected without granting the UI independent authority.
- **Rollback:** disable UI while APIs/projections remain available.
- **Unlock:** P14.

## P14 — Trusted Reverse-solving Application

- **Entry criteria:** Workbench, workflows, providers, validation, and Capsules accepted.
- **Risk tier:** R2/R3 by selected actions.
- **Allowed scope:** compose existing trusted capabilities for reverse-solving Work Items.
- **Forbidden scope:** bypass firewall/sandbox/validation, sample-specific constants in generic framework.
- **Deliverables:** end-to-end trusted reverse-solving application and representative acceptance cases.
- **Tests:** known fixtures, adversarial samples, negative results, cross-run isolation, full Capsule replay.
- **Acceptance:** results are traceable to immutable evidence and current validation, with honest uncertainty.
- **Rollback:** disable application orchestration while retaining lower-level trusted services.
- **Unlock:** P15.

## P15 — Crash / Patch / Malware / Firmware Adapters

- **Entry criteria:** P14 representative reverse-solving flows accepted; adapter extension contract stable.
- **Risk tier:** R2/R3 by domain and execution.
- **Allowed scope:** domain-specific intake, evidence adapters, policies, validation templates.
- **Forbidden scope:** weakening shared trust rules, unisolated execution, cross-domain data leakage.
- **Deliverables:** independently testable adapters for selected domains.
- **Tests:** domain fixtures, taint/provenance, sandbox tiering, policy separation, Capsule replay.
- **Acceptance:** each adapter reuses shared contracts without becoming a second trust system.
- **Rollback:** unregister individual adapters and preserve their immutable artifacts.
- **Unlock:** P16.

## P16 — Production Hardening

- **Entry criteria:** measured usage identifies concrete reliability, scale, or compliance needs.
- **Risk tier:** R2/R3 by change.
- **Allowed scope:** performance, availability, backup/restore, key management, audit retention, deployment hardening based on evidence.
- **Forbidden scope:** speculative microservices/Kubernetes, authority duplication, weakening isolation for throughput.
- **Deliverables:** SLOs, threat-model updates, backup/restore evidence, operational runbooks, measured capacity plan.
- **Tests:** load/failure injection, disaster recovery, credential rotation, isolation regression, upgrade/rollback.
- **Acceptance:** measured objectives pass without changing constitutional trust and ownership rules.
- **Rollback:** versioned deployment rollback with data/schema compatibility and preserved evidence.
- **Unlock:** future work only through a new architecture or product Decision.

## Cross-phase invariants

1. No phase starts before its predecessor acceptance and a new authorization.
2. P1 never mixes with P2; P2 never mixes with P3.
3. GitHub, LangGraph, Analysis Repository, Artifact Store, Telemetry, and Capsule each retain their unique authority.
4. Engineering acceptance never equals Claim validation.
5. Unknown-binary execution never occurs before P8 and never outside R3 authorization.
6. Rollback preserves immutable evidence and history; it does not rewrite accepted facts.
