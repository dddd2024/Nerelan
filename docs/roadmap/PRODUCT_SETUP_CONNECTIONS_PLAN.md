# Product Setup & Connections Plan

> Status: fixed near-term roadmap under #148. This document does not grant code mutation authority.

## Position in sequence

```text
#149 LangGraph seam               DONE
#151 parallel team + verifier     DONE
Task 3A contract foundation       CURRENT (#165)
Task 3B binding consumption       NEXT
#152 Freshness Automation         AFTER SETUP
real OpenCode multi-Agent dogfood AFTER FRESHNESS FOUNDATION
```

## Objective

Make reverse-agent usable as one coherent product rather than a collection of separately configured developer tools.

The product must distinguish:

```text
Connection = provider/service + authentication
Executor   = coding Agent/runtime
Binding    = Executor + Connection + Model
```

and implement the user rule:

> Configure/authenticate once; supported executor adapters reuse that Connection without asking for the same credential a second time.

Task 3A provides the process-local contracts, sanitized registry API and
fail-closed references. It exposes only `opencode` as an operational executor
descriptor and preserves the legacy `ModelProfile` API for migration. Task 3B
must prove that a supported executor adapter consumes a selected Binding; Task
3A alone does not claim credential inheritance or runtime execution.

## Workstream A — Connection model

Replace the current conceptual coupling between provider/model profiles and executor choice.

Required authentication types:

- API key / environment-backed secret;
- account login/OAuth when the mature provider/executor supports it;
- external CLI session;
- no authentication for local endpoints.

Do not expose raw secrets to browser task state, TaskStore, evidence or logs.

## Workstream B — Executor adapters (Task 3B)

For OpenCode, Codex and later executors, detect/use only supported integration mechanisms:

- bounded child-process environment;
- bounded transient provider config;
- officially supported executor-owned login/session state.

Do not scrape or migrate credentials between tools.

Current OpenCode behavior must remain documented accurately until replaced: Model Control API configuration is not automatically inherited by OpenCode.

## Workstream C — Binding profiles

A reusable Binding identifies:

```text
binding_id
executor_id
connection_id
model_id
```

Tasks select a Binding rather than mixing provider credentials and executor identity.

## Workstream D — GitHub repository connection

Treat GitHub as a repository-domain connection, separate from model/provider connections.

Prefer GitHub App/OAuth/`gh`/existing git credential integration. Expose sanitized account/repository connection status and repository selection. Keep publication/merge authority separately controlled.

## Workstream E — Product launcher

Reuse `dev-up.ps1` / `dev-down.ps1` for lifecycle and add a thin Windows double-click launcher.

The launcher should:

- verify prerequisites;
- start Model Control, Task API and Frontend;
- wait for health checks;
- report connection/executor readiness;
- open the workspace;
- stop only owned processes on shutdown/failure.

Do not replace the lifecycle with a large custom desktop runtime in the first implementation.

## Workstream F — Connection testing UX

Resolve the current mismatch where Settings exposes connection testing but live probing is disabled unless `REVERSE_AGENT_MODEL_CONTROL_LIVE=1` is explicitly enabled.

Network probing stays explicit/fail-closed; the product must expose a clear trusted opt-in path instead of silently enabling it.

## Acceptance

This phase is complete only when:

1. one provider API connection is configured once and successfully consumed by one supported executor adapter without duplicate manual key entry;
2. one account/external-session connection is detected/reused without reverse-agent storing its raw credential;
3. Executor selection is independent of Provider/Auth selection;
4. a Binding selects Executor + Connection + Model;
5. GitHub repository connection is a distinct product concept;
6. a thin double-click launcher works while reusing existing service lifecycle logic;
7. all connection status exposed to the frontend is sanitized;
8. the current `ModelProfile.executor` coupling has a migration/retirement path;
9. the Connection/Executor/Binding contracts are stable enough to register in #152 Freshness Automation Foundation.

After this phase, run #152 before treating real OpenCode multi-Agent dogfood / Pack growth as a stable operating mode.

Canonical architecture details live in `docs/architecture/CONNECTION_EXECUTOR_BINDING_ARCHITECTURE.md`.
Freshness architecture lives in `docs/architecture/FRESHNESS_AND_DRIFT_GOVERNANCE.md` and Issue #152.

## Fixed delivery order

```text
#149 DONE
-> #151 DONE
-> Task 3A Connection / Executor / Binding foundation (#165)
-> Task 3B supported executor Binding consumption
-> remaining Product Setup: repository connection, probe UX, thin launcher
-> #152 Freshness Automation Foundation
-> real OpenCode Multi-Agent dogfood
-> Pack / Capability growth
-> later data-based routing
```
