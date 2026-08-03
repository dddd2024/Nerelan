# Cross-Agent Context Contract

```text
STATUS: ACTIVE
AUTHORITY: PLANNING_REFERENCE_ONLY
```

This contract defines how context is shared — and explicitly not shared — across different Agent products that operate on this repository. It is a planning reference; it does not itself authorize commands, file changes, closeout, or merge.

Transient execution facts (the Path-A authority snapshot — repository, Issue number, approval state, approver, approval event/time, body digest, immutable observation ref, work-item identity, target branch, base SHA) belong only in the Draft PR body for the specific Work Item. They must not be embedded in this permanent contract, because they would otherwise become stale dynamic metadata that contradicts the contract's own freshness rules. The active Work Item snapshot for this contract is recorded in PR #104.

## Why this contract is needed

Different Agent products do not automatically share private memory.

ChatGPT Project memory, Codex memory, OpenHands persistence, Claude/Cursor/Trae memories, and similar product-level context belong to their respective product scopes. Each product may retain its own role assumptions, prior summaries, cached constraints, conversation state, and session caches. Those private memories are not automatically synchronized across products and may be stale or contradictory.

Only content written into the same Git commit or verifiable GitHub state may be read by different Agents as shared project fact. Even shared state must be checked for freshness before it is trusted.

## Memory layers

### 1. Repository-backed shared state

- tracked files at an exact commit;
- `AGENTS.md`, active source-of-truth documents, active Decision/Command Plan, generated gates, and current tracked context artifacts;
- available to any Agent that reads the same repository revision;
- authority class: `REPOSITORY_POLICY` when grounded in tracked files at the observed commit.

Shared repository state is only authoritative at the exact commit an Agent actually reads. A cached summary of a previously read commit is not equivalent to re-reading the current commit.

### 2. GitHub-backed shared state

- Issues, labels, PRs, comments, commits, branches, checks, and merge state;
- shared only when the Agent has connector/network access to GitHub;
- Issue/PR comments remain non-authoritative unless the active authority model explicitly says otherwise;
- authority class: `GITHUB_OBSERVATION` for verifiable GitHub state.

GitHub comment is not Path-B authority. Issue body is not Path-B authority. Path-B authority requires a bounded APPROVED Decision plus generated Command Plan plus `PRE_EXECUTION_AUTHORIZED` per `AGENTS.md`.

### 3. Product/platform project memory

- ChatGPT Project memory, Codex project instructions, OpenHands persistence, Claude/Cursor/Trae memories, and similar product-level context;
- scoped to the product/account/project configuration;
- not automatically visible to another Agent product;
- authority class: advisory only — never `REPOSITORY_POLICY`.

Product/platform memory is not repository policy. It must not be presented as a repository fact without a tracked citation.

### 4. Agent-local persistent memory

- role assumptions, prior summaries, cached constraints, and app-specific saved context;
- advisory only unless independently grounded in the current repository or GitHub authority;
- authority class: `AGENT_LOCAL_ROLE_CONSTRAINT` when describing a constraint local to one Agent product.

Agent-local persistent memory is not repository policy. A constraint that one Agent product enforces locally does not prove that every Agent or the repository universally enforces the same constraint.

### 5. Run/session scratch state

- current conversation, scratchpad, temporary workspace, and runtime state;
- not assumed to survive or transfer to another Agent;
- authority class: `SESSION_ASSUMPTION` for in-session assumptions not yet grounded in repository or GitHub state.

Run/session state is the least durable layer. It must not be treated as shared project fact.

## Freshness checks for shared state

Shared state must be checked for freshness before it is trusted. A generated context artifact or cached summary is only usable when its freshness can be verified against the current repository or GitHub state. Freshness is checked by comparing:

```text
commit SHA
Decision ID
round ID
generated_at
source digest
```

If any freshness field cannot be verified against the current observed state, the shared artifact must be treated as stale and re-read from the current repository or GitHub state before use.

## Conflict-resolution rule

When facts from different layers conflict, resolve in this order:

```text
exact Git/GitHub fact for the relevant fact class
→ applicable active Path-A or Path-B authority
→ active repository source-of-truth documentation
→ current generated context/index artifacts, verified for freshness
→ approved Work Item planning text
→ Agent-product/private memory
→ model recollection or inference
```

This ordering must not weaken Path-B fail-closed behavior. A GitHub comment cannot authorize Path-B work. An Issue body cannot authorize Path-B work. Private Agent memory cannot authorize Path-B work. Authority remains class-specific under `SOURCE_OF_TRUTH_MATRIX.md` and `AGENTS.md`.

## Required Agent behavior

An Agent must:

- name the source of each claimed prohibition or permission, using the source classes below;
- distinguish `REPOSITORY_POLICY` from `AGENT_LOCAL_ROLE_CONSTRAINT`;
- never present private memory as a repository fact without a tracked citation;
- detect stale generated context by Decision/round/commit identity;
- report a conflict as `AGENT_CONTEXT_CONFLICT` instead of silently choosing one memory;
- obey its own higher-level system/safety constraints, while clearly stating that such a block is local to that Agent product rather than a global project rule;
- re-read the active repository and GitHub state at task start rather than relying solely on remembered summaries;
- avoid copying dynamic project facts into long-term skill/prompt files.

### Source classes

When an Agent claims a rule or constraint, it must tag the source:

```text
REPOSITORY_POLICY
ACTIVE_DECISION
GENERATED_COMMAND_PLAN
GITHUB_OBSERVATION
AGENT_LOCAL_ROLE_CONSTRAINT
SESSION_ASSUMPTION
USER_PROVIDED_CONTEXT
```

### AGENT_CONTEXT_CONFLICT

When sources conflict and the conflict cannot be resolved by the conflict-resolution rule alone, the Agent must stop and return:

```text
AGENT_CONTEXT_CONFLICT
```

The conflict report must include at least:

```text
claim
source
source revision
conflicting source
applicable authority class
selected action
```

### AGENT_LOCAL_ROLE_CONSTRAINT

When an Agent's own product system or safety limit prevents an operation, the Agent must still obey that limit, but must express it as local rather than universal:

```text
This Agent product cannot perform the operation because of
AGENT_LOCAL_ROLE_CONSTRAINT.
This does not establish a repository-wide prohibition.
```

Such a role-specific refusal does not prove that every Agent or the repository universally forbids the operation.

## Issue #102 clarification

Issue #102 proposed a trusted-host compatibility observation experiment. The documentation here must explain:

- the active repository evidence currently supports blocking the live probe until a new Issue #102 Path-B Decision exists;
- a private Agent role may additionally refuse to author that Decision;
- such a role-specific refusal does not prove that every Agent or the repository universally forbids Owner-authored Decision creation;
- the safe handoff is for an Owner/planner to author and approve exact authority content, then for an executor to materialize and validate it only if its own product permissions allow.

This contract does not authorize Issue #102, Docker, OpenHands, or Codex ACP execution. This task (Issue #103) is documentation and deterministic tests only.

## Relationship to existing authority documents

This contract is a planning reference. It does not change the authority model in `AGENTS.md` or `SOURCE_OF_TRUTH_MATRIX.md`. Where this document and `AGENTS.md` appear to conflict, `AGENTS.md` and the active source-of-truth documentation govern. This contract's purpose is to make the boundary between shared repository fact and private Agent memory explicit so that Agents do not silently treat private memory as project policy.
