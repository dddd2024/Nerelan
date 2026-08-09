# Freshness and Drift Governance Architecture

> Status: fixed modernization architecture under #148. This document defines the selected mature-component-first approach for keeping Skills, governance/policy, adapters and external integration assumptions current. It does not grant code-mutation authority.

## 1. Problem

reverse-agent depends on fast-moving external systems: OpenCode, Codex, OpenHands, LangGraph, Agent Canvas, GitHub, provider APIs and future Pack/Skill ecosystems. A file can still exist and pass syntax checks while its assumptions are already stale.

The project must therefore distinguish:

```text
version drift
!=
semantic drift
```

Version drift means an upstream package, CLI, Action, tag or pinned commit changed.
Semantic drift means a Skill, policy, adapter, prompt or operating contract no longer matches the behavior or contract it was verified against.

The target is NOT to auto-edit every Skill or policy to the newest wording. The target is:

> detect relevant upstream/contract change -> mark impacted assets for revalidation -> run compatibility tests -> only then refresh the verified state.

## 2. Mature-component-first decision

Use mature components for generic update detection and repository enforcement. Keep only reverse-agent-specific dependency/impact metadata and compatibility tests in-repository.

Selected stack:

```text
Renovate
  -> primary dependency/upstream drift watcher
  -> Dependency Dashboard
  -> update PRs
  -> custom managers for non-standard pins

GitHub Actions
  -> semantic compatibility / freshness checks
  -> scheduled revalidation
  -> PR-triggered impacted tests

CODEOWNERS + GitHub Rulesets
  -> mandatory ownership/review and required Freshness status

OPA Bundles (later, after Rego adoption)
  -> policy distribution/version activation
  -> NOT semantic freshness detection
```

### Dependabot role

Dependabot is a supported fallback when Renovate is not installed/available. Do NOT run Dependabot and Renovate against the same dependency ecosystems because duplicate update PRs create noise and split authority.

If Renovate is selected for the repository, it is the primary watcher for Python/package manifests, JavaScript/package manifests, GitHub Actions and custom pinned upstreams.

## 3. Why Renovate is the primary watcher

Renovate is selected because reverse-agent has both standard dependencies and non-standard external pins.

Required direct-use capabilities:

- native PEP 621 / `pyproject.toml` dependency updates;
- standard JavaScript package dependency updates;
- native GitHub Actions reference updates;
- custom regex managers for dependencies embedded in repository-owned metadata/docs/config;
- `github-tags`, `git-refs` and related datasources for upstream tag/commit tracking;
- Dependency Dashboard for one visible queue of pending/deferred/ignored updates;
- package rules to require explicit approval for high-risk upgrades.

Examples of non-standard pins Renovate should eventually track:

```text
Agent Canvas upstream version/commit
OpenCode supported CLI version
Codex supported CLI version
policy engine/runtime version
selected external adapter protocol versions
Pack/Skill upstream version markers where a stable upstream exists
```

Renovate detects drift and proposes controlled updates. It does not decide that a Skill or policy is semantically valid after the update.

## 4. Freshness Registry

Introduce one small reverse-agent-specific registry after the schema is approved:

```text
governance/freshness-registry.yaml
```

This registry is domain metadata, not a replacement dependency manager.

Conceptual entry:

```yaml
- id: opencode-executor-skill
  kind: skill
  path: skills/opencode/SKILL.md
  depends_on:
    - opencode-cli
    - task-execution-contract
    - connection-binding-contract
  verified_against:
    opencode-cli: "<verified version>"
    task-execution-contract: "<contract version>"
  last_verified_at: "<timestamp>"
  max_age_days: 14
  verification_suite:
    - tests/compatibility/opencode_skill/**
  owner: executor-runtime
```

The registry must never contain raw credentials or tokens.

The registry's schema should later be validated by the same typed/schema tooling selected for governance (prefer CUE once that migration is active) rather than growing a second ad-hoc schema engine.

## 5. Freshness states

Every registered asset resolves to one of:

```text
FRESH
REVIEW_REQUIRED
STALE
BLOCKED
```

Semantics:

- `FRESH`: all declared dependencies/contracts still match the last verified set and the freshness interval is valid.
- `REVIEW_REQUIRED`: a dependency/contract changed or the review interval elapsed; compatibility verification is required.
- `STALE`: compatibility verification failed or a required upstream is known to have drifted beyond the verified contract.
- `BLOCKED`: the required upstream/contract cannot be resolved safely, so the asset must not authorize privileged execution.

`last_verified_at` alone can never turn a changed dependency back to FRESH.

## 6. Impact graph

Use explicit dependency relationships instead of broad repository-wide invalidation.

Example:

```text
OpenCode CLI
  -> OpenCodeExecutor adapter
  -> OpenCode connection adapter
  -> OpenCode Skill
  -> real OpenCode acceptance fixture

Decision contract
  -> governance policy
  -> activation/preflight Skill
  -> CI policy check

LangGraph
  -> team graph adapter
  -> multi-Agent orchestration Skill
  -> team/verifier integration tests
```

When a source node changes, only reachable registered assets become `REVIEW_REQUIRED`.

Do not mark every Skill stale because an unrelated dependency changed.

## 7. Trigger model

### Trigger A — Renovate update PR

When Renovate proposes an upstream/dependency change:

```text
update PR
-> identify impacted registry assets
-> run their compatibility suites
-> Freshness check reports FRESH or STALE
-> update verified metadata only if tests pass
```

Critical Agent/runtime/policy dependencies must not auto-merge merely because the package update itself installs successfully.

### Trigger B — Contract/path changes in normal PRs

If a PR changes a registered contract/provider path, the Freshness job calculates impacted Skills/policies/adapters and runs the corresponding suites.

Examples:

```text
architecture/contracts.py changed
-> dependent governance + workflow Skills REVIEW_REQUIRED

task_execution.py changed
-> executor/worker integration Skills REVIEW_REQUIRED

connection binding contract changed
-> executor connection adapters REVIEW_REQUIRED
```

### Trigger C — Scheduled review

A scheduled GitHub Actions workflow checks:

- review interval expiry;
- unresolved `REVIEW_REQUIRED` / `STALE` assets;
- local contract/version consistency;
- compatibility suites that are safe to run periodically.

External/network probes remain explicit and fail-closed; scheduled jobs must not silently acquire privileged credentials.

## 8. GitHub enforcement

Use `.github/CODEOWNERS` for at least:

```text
skills/**
policy/** or governance policy paths
governance/freshness-registry.yaml
renovate configuration
.github/workflows/freshness*.yml
critical executor/connection adapters
```

Use GitHub Rulesets to require the relevant code-owner approval and a `Freshness` status check before protected-branch merge when these paths are touched.

Rulesets, not reverse-agent runtime code, own GitHub merge enforcement.

## 9. Renovate safety policy

Initial Renovate posture for reverse-agent:

```text
Dependency Dashboard: enabled
Critical runtime/Agent/policy updates: dashboard approval required
Automerge: disabled for critical integrations
Compatibility tests: mandatory before acceptance
Custom pins: update only through declared managers/datasources
```

The exact package rules are implementation detail for the future bounded task, but the above safety semantics are fixed.

## 10. Policy distribution later

If/when governance policy is migrated to OPA/Rego:

```text
policy source
-> reviewed bundle build
-> OPA Bundle distribution
-> runtime activation
```

OPA Bundles solve distribution/version activation. They do NOT prove that a policy is semantically current with changed Task/Workspace/Decision contracts, so the Freshness Registry and compatibility tests remain authoritative for that question.

## 11. What we do NOT build

Do not build a custom clone of Renovate/Dependabot.

Do not build:

- a custom package registry crawler;
- a custom GitHub release watcher for standard dependencies;
- a custom dependency update PR bot;
- a custom scheduler when GitHub Actions schedule is sufficient;
- a second repository merge-policy engine;
- an LLM-only 'looks current' freshness decision.

Reverse-agent-specific code should be limited to:

```text
impact metadata
compatibility fixtures/tests
freshness state calculation
sanitized report generation
```

## 12. Fixed implementation sequence

Do not interrupt #151.

After Product Setup & Connections reaches a stable contract, implement freshness automation before broad Pack/Skill proliferation:

```text
#151 multi-worker team
-> Product Setup & Connections
-> Freshness Automation Foundation
   1. Renovate config + Dependency Dashboard
   2. freshness registry schema
   3. impacted compatibility check
   4. scheduled freshness workflow
   5. CODEOWNERS/Ruleset integration
-> real OpenCode multi-Agent dogfood / Pack growth
```

If Product Setup creates high-value Skills/adapters before the Freshness task lands, register them in the initial registry migration instead of inventing temporary per-component freshness mechanisms.

## 13. Acceptance criteria

Freshness Automation Foundation is complete when all of the following are proven:

1. Renovate detects a normal package update.
2. Renovate detects at least one non-standard upstream pin via a custom manager.
3. The Dependency Dashboard exposes pending/deferred updates.
4. A synthetic upstream/contract change marks only declared dependent assets `REVIEW_REQUIRED`.
5. Passing compatibility tests can refresh verification metadata.
6. Failing compatibility tests produce `STALE` and block the required Freshness check where configured.
7. Review-age expiry produces `REVIEW_REQUIRED` without pretending the asset is broken.
8. CODEOWNERS/Rulesets protect freshness/governance configuration from silent changes.
9. No raw credentials are written to registry/reports/logs.
10. Dependabot is either disabled for overlapping ecosystems or is the explicit fallback instead of a second concurrent updater.

## 14. Architectural invariant

The invariant for future Skills, policy and adapters is:

> No critical operational artifact is considered current merely because its file exists. Its declared dependencies, compatibility evidence and verification age must still be valid.
