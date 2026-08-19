# Reverse Agent

Reverse Agent is a local-first, governed multi-Agent development platform. Give it a final goal; it persists a specification and plan, decomposes work into dependent tasks, coordinates reusable Agent runtimes, survives restarts, validates results, and can prepare an allowlisted Draft PR for review.

The product deliberately reuses mature components:

- GitHub Spec Kit-compatible `Goal → Specification → Plan → Tasks` artifacts;
- LangGraph topology and checkpoints for sequential or parallel teams;
- OpenCode as the repository executor and model-session adapter;
- OpenHands Agent Canvas patterns for the dark web workspace;
- GitHub as repository, checks, review, and publication truth.

Repository-owned code is the thin trust layer: authority snapshots, autonomy policies, durable claims, idempotency, evidence, secret confinement, exact-path publication, and deterministic acceptance.

## Start the platform

Requirements: Python 3.13+, Node.js, an existing `frontend/node_modules`, Git, GitHub CLI, and OpenCode. The launcher does not install packages or invoke a model during startup.

```powershell
.\dev-up.ps1
```

Or double-click `launch_reverse_agent.bat`. The launcher starts loopback-only services and opens `http://127.0.0.1:4173`:

```text
Frontend       127.0.0.1:4173
Model Control  127.0.0.1:8765
Task API       127.0.0.1:8766
Coordinator    enabled, inert until an owner activates a bounded window
```

Stop only the processes recorded by this launch:

```powershell
.\dev-down.ps1
```

## Product workflow

```text
natural-language goal
-> persistent specification and editable plan
-> owner approval and bounded autonomous window
-> dependency-aware multi-Agent execution
-> durable checkpoint / reconciliation / resume
-> deterministic validation and sanitized evidence
-> allowlisted task branch and Draft PR
-> governed exact-head review and acceptance
```

The browser never receives shell authority, direct filesystem access, raw provider credentials, or merge authority. The coordinator is off unless the trusted host enables it, and it remains inert without an active owner-confirmed window. Draft publication never force-pushes, rebases, marks ready, merges, tags, releases, or deploys.

## Platform APIs

The loopback Task API exposes:

- `/api/goals` for persistent goal planning, approval, amendment, and launch;
- `/api/windows` for owner-activated time, repository, capability, WIP, task, and retry budgets;
- `/api/platform/status` and `/api/capabilities` for product readiness;
- `/api/tasks` for execution truth, events, changed files, validation, and evidence;
- `/api/tasks/{id}/publish` for idempotent allowlisted Draft-PR publication.

Provider-free tests cover the entire control path. Real model/API probes are separate R3 operations and are never part of ordinary startup or CI.

## Authority model

Two authority paths remain fail-closed:

- Path A: approved immutable GitHub Work Item snapshots for ordinary R0/R1 work.
- Path B: approved Decision, generated Command Plan, and `PRE_EXECUTION_AUTHORIZED` for R2/R3 work.

An autonomous window is execution policy, not repository-development authority. It cannot expand its own repositories, capabilities, duration, budgets, or publication boundary.

## Verification

```powershell
python -m pytest -q
npm --prefix frontend run typecheck
npm --prefix frontend test
npm --prefix frontend run build
python -m reverse_agent.freshness --registry governance/freshness-registry.json --repository-root .
git diff --check
```

Renovate proposes dependency updates without automerge. The freshness registry records the owner, upstream source, pinned/compatible version, evidence path, and review age for mature platform components.

## Reference documents

- [AGENTS.md](AGENTS.md) — repository authority, risk, publication, and stop rules
- [active roadmap](docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md)
- [source-of-truth matrix](docs/architecture/SOURCE_OF_TRUTH_MATRIX.md)
- [R1 Work Item template](.github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml)
- [legacy `run-closeout` reference](docs/run_closeout.md) — historical compatibility only
