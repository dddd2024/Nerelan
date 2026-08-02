# Reverse Agent

Reverse Agent is a governance and control-plane tooling repository for a **minimal AI-assisted development integration baseline**. The repository does not build a generic AI software-development platform; it provides thin risk classification, bounded path/operation policy, a high-risk approval boundary, and deterministic acceptance checks around mature development tools.

## Active development stack

```text
approved specification
-> approved immutable GitHub Work Item snapshot
-> Codex implementation
-> deterministic GitHub Actions
-> independent review
-> human merge
```

## Two authority paths

The project defines two distinct authority paths. No source is globally higher when it is not applicable to the selected path.

### Path A — ordinary R0/R1 authority

For ordinary R0/R1 work (after the one-time transition round that established this baseline), authority is:

```text
approved Work Item Issue body (R1 template)
  + Issue allowed_paths / forbidden_operations / acceptance_criteria
  + deterministic checks (pytest, git diff --check, GitHub Actions)
```

The Work Item Issue body is the primary authority for R0/R1. Issue comments and PR comments are **never** authority. `project_state/decision_packet.md` and `project_state/gates/command_plan.json` are **not** used for ordinary R0/R1.

### Path B — transition / R2-R3 authority

For transition rounds (when `transition_kernel_required=true`) and R2/R3 operations, authority is:

```text
bounded Decision in project_state/decision_packet.md
  + generated command_plan.json
  + transition-preflight PRE_EXECUTION_AUTHORIZED
```

R2/R3 operations fail closed. No Issue, Issue comment, PR comment, or roadmap document can authorize R2/R3 work.

## Current scope and non-goals

The current product scope is a **minimal integration layer** around mature development tools while product extensions remain undecided. The following are **not active implementation scope**:

```text
generic LangGraph orchestration platform
generic Agent Registry
generic multi-agent organization
generic Web agent control console
GitHub Issue/PR state replication
generic checkpoint/retry/reconciliation platform
Open SWE fork or OpenHands control-plane product
specific hostile-binary, reverse-solving, crash, patch, malware, or firmware product work
```

Security and binary direction remain **extension candidates**, not current implementation scope.

## Platform V1 — bounded OpenHands Agent Canvas + Codex ACP direction

The current selected bounded Platform V1 integration direction is **OpenHands Agent Canvas + Codex ACP**. This is a thin adapter layer (`reverse_agent/platform_v1/`) that binds the repository's governance layer (risk classification, path/operation policy, trusted evidence, deterministic acceptance) to the pinned OpenHands Agent Canvas + Codex ACP platform surface.

```text
do not fork OpenHands
do not copy its frontend or Agent Loop
do not build a second control platform
do not auto-merge
```

The adapter does not implement an executor, agent loop, sandbox, database, or frontend. Live compatibility probes (Agent Canvas startup, Agent Server health, Codex ACP authentication, restart recovery) require a trusted host with explicit opt-in and are not executable in the provider-free CI environment. The current status is `PR97_CODE_REWORK_COMPLETE_AWAITING_TRUSTED_HOST_LIVE_PROBE` — the full vertical slice is not yet accepted.

## Reference documents

- [AGENTS.md](AGENTS.md) — repository operating guide for agents and contributors
- [docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md](docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md) — single active top-level roadmap
- [docs/architecture/SOURCE_OF_TRUTH_MATRIX.md](docs/architecture/SOURCE_OF_TRUTH_MATRIX.md) — authoritative source for each class of fact
- [.github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml](.github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml) — R1 Work Item Issue template

## Legacy documentation (not the current workflow)

The active development stack and authority paths above define the current workflow. The following legacy artifact is retained as historical reference only and is **not** the default current workflow:

- [docs/run_closeout.md](docs/run_closeout.md) — legacy engineering-round closeout documentation. The `run-closeout` command and `project_state/decision_packet.md`-as-sole-authority model described there are superseded for ordinary R0/R1 work by the Work Item Issue body authority (Path A) defined above.
