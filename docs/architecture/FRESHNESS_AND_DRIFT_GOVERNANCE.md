# Freshness and Drift Governance Architecture

> Status: fixed modernization architecture under #148 and #152. This document defines the selected mature-component-first approach for keeping Skills, governance/policy, adapters and external integration assumptions current. It does not grant code-mutation authority.

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

After Product Setup & Connections reaches a stable contract, implement #152 before broad Pack/Skill proliferation and before declaring real OpenCode multi-Agent dogfood a stable operating mode:

```text
#151 multi-worker team
-> Product Setup & Connections
-> #152 Freshness Automation Foundation
   1. Renovate config + Dependency Dashboard
   2. freshness registry schema
   3. impacted compatibility check
   4. scheduled freshness workflow
   5. CODEOWNERS/Ruleset integration
-> real OpenCode multi-Agent dogfood / Pack growth
```

If Product Setup creates high-value Skills/adapters before #152 lands, register them in the initial registry migration instead of inventing temporary per-component freshness mechanisms.

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


## 15. Pinned/local contract review — 2026-09-19

This review refreshes the four existing registry entries for their actual
fixed-version or local adaptation contracts. It does not establish latest-upstream
compatibility, real provider execution, Spec Kit CLI interoperability, visual
snapshot acceptance, or completion of the #152 architecture criteria above.
The 30-day review limits and live UTC-date freshness workflow remain unchanged.

The tested candidate starts at main `ef8bb6959ac37301c880e0971a97a9d56e9c99a9`
with activation `0e7e62e74e1c3d93ce84e8d9b9ed943bfce11e59`.
Production and frontend source are identical to that base. The team test fixture
is the exact independently reviewed PR #954 file at head
`751418682ed70ddb5dd51e63b58c307cd98944c8` (Git blob `fd82474b4a81ed186de125ffb29b0ddeec5e32d9`).
That repair is included in this candidate, not claimed to have already landed on
main. It preserves original tests/assertions while matching the current team
execution contract. No installed external tool or model was executed.

| Entry | Reviewed source and supported contract | Actual evidence |
|---|---|---|
| LangGraph 1.0.10 | Official `langchain-ai/langgraph` tag `1.0.10`, commit `cdda595e6e9d7d0f47f3ca92012fb8f1c45c1cad`; installed distribution exactly 1.0.10 | Full development graph, repaired team and unattended coordinator suites; real graph runtime with fake executors |
| langgraph-checkpoint-sqlite 3.1.0 | Official `checkpointsqlite==3.1.0` tag, commit `3614e88c58af63f597764218646e85c49952b2da`; installed distribution exactly 3.1.0 | Full durable execution and durable execution v5 suites; real SQLite saver, restart and serialization contracts |
| Agent Canvas 1.6.1 | Official `OpenHands/agent-canvas` tag `v1.6.1`, commit `43f091baf135142ed6c146f888f44a957141193f`; clean upstream checkout and documented five-file presentation fork | Four component test files: 27 passed; typecheck, production build and lint each exit 0 |
| github-spec-kit compatible | Existing `GoalService` deterministic specification/plan/tasks convention; official Spec Kit release source reviewed, no upstream CLI used | Full goal service and plan revision suites, plus actual `GoalService.plan` probe proving separate nonempty persisted spec/plan, acceptance criteria and task IDs/dependencies under subprocess/socket guards |

Python compatibility command (254 passed, one warning):

```text
python -B -m pytest tests/test_development_graph.py tests/test_team_graph.py tests/platform_v1/test_unattended_coordinator.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_durable_execution_v5.py tests/platform_v1/test_goal_service.py tests/platform_v1/test_goal_plan_revision.py tests/test_freshness.py -q -p no:cacheprovider
```

The warning is `PytestUnhandledThreadExceptionWarning` from the existing deliberate
`_CrashSimulated: simulated_crash_after:POST_PLANNER` crash seam. It is recorded,
not suppressed. The initial compatibility run preceded the registry metadata and
deterministic freshness-test update; the affected freshness tests are rerun after
those edits. No runtime source changed between those checks.

Frontend commands, run on this candidate's unchanged tracked frontend tree:

```text
npm --prefix frontend test -- tests/workspace.test.tsx tests/task-first-sidebar.test.tsx tests/responsive.test.tsx tests/accessibility.test.tsx
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend run lint
```

The root checkout lacked a usable Vitest executable. The successful candidate runs
reuse the existing dependencies from `F:/Nerelan-issue844-visible-goal-evidence/frontend/node_modules`
through an ignored local junction, after byte-identical package-lock comparison;
there was no dependency install or download. Actual Vitest was 2.1.9. The build
retains its existing greater-than-500-kB chunk warning; no size threshold was raised.

Canvas provenance correction: the prior registry URL for `All-Hands-AI/agent-sdk`
redirects to `OpenHands/software-agent-sdk`, which is a different component.
The registry now points to the actual Canvas repository. The five adapted files
retain presentation structure and neutral slots, not upstream backend/runtime
hooks. Historical reuse-map density wording is not exact for the present fork:
current expanded rail is 232px (collapsed 60px), versus upstream 300px; current
sidebar rows/text are 30px/13px, versus upstream 36px/14px. These existing local
visual adaptations are explicitly within this review's local presentation scope.
No claim of byte identity or pixel-perfect upstream appearance follows.

Raw local evidence is retained under
`F:/Nerelan-final-audit-evidence-20260911/issue152-*` (compatibility log,
installed versions, guarded goal probe, component/typecheck/build/lint logs),
along with the independent source/scope audit. Exact-head Actions and independent
acceptance remain separate publication requirements; local success alone is not
mainline acceptance.
