# Connection / Executor / Binding Architecture

> Status: **CANONICAL MODERNIZATION DESIGN + TASK 3A FOUNDATION + TASK 3B SECRET-FREE OPENCODE ADAPTER** under #148 / #165 / #170.
> Scope: model/provider authentication, Agent/Executor integration, repository connection, and product startup UX.
> This document is design authority, not code-mutation authority.

Task 3A establishes the process-local contracts and trusted-loopback API for
`Connection`, `ExecutorDescriptor`, and `Binding`. Task 3B adds an explicit,
durable `Task.binding_ref` and a secret-free OpenCode adapter for `none` and
available executor-owned session authentication. The legacy `ModelProfile`
surface and non-Binding OpenCode path remain available during migration.

## 1. Problem being corrected

The current `ModelProfile` design combines concerns that should be separate:

```text
provider/base URL/model/API credential
+
executor choice (OpenHands / Codex ACP)
```

At the same time, concrete executors such as OpenCode own or consume their own provider/login configuration. Therefore a user can configure an API in reverse-agent Model Control and still have to configure the same provider again in OpenCode.

Current reverse-agent must **not** claim that a Model Control API key is automatically inherited by OpenCode. It is not.

Modernization must remove this duplicate-configuration model.

## 2. Canonical domain split

The product model is three layers:

```text
Connection
    -> authentication + provider/model access

Executor
    -> the coding/agent runtime that performs work

Binding
    -> selects one Executor + one Connection + one Model for a workload/profile
```

### 2.1 Connection

A Connection answers:

```text
Where does model/service capability come from?
How is it authenticated?
What models/capabilities are available?
Is it currently connected?
```

Examples:

```text
SenseNova API
OpenAI API
OpenAI account login
Gemini API
local Ollama / local OpenAI-compatible endpoint
GitHub account/repository connection (repository domain; see section 6)
```

A model/provider Connection should carry only sanitized metadata and secret references, for example:

```text
connection_id
provider
base_url (when applicable)
auth_method
credential_ref / external_session_ref
available_models / capability metadata
connection_status
```

It must not expose raw credentials to browser task state.

### 2.2 Authentication method

Authentication is a property of a Connection, not a different Agent.

Expected methods include:

```text
api_key
account_login / oauth
external_cli_session
none
```

Examples:

```text
OpenAI API       -> api_key
OpenAI account   -> account_login
OpenCode session -> external_cli_session
Local Ollama     -> none
```

Do not model "API" and "login" as separate Executors.

### 2.3 Executor

An Executor answers:

```text
Which Agent/runtime performs the actual software-engineering task?
```

Examples:

```text
OpenCode
Codex
OpenHands
future concrete executor runtimes
```

The Task 3A registry exposes only `opencode` as an operational executor. Codex
and OpenHands remain architectural examples until a later bounded task adds and
proves concrete runtime descriptors; their legacy `ModelProfile.executor`
values are compatibility inputs, not operational registry claims.

Multi-Agent orchestration is **not** an executor kind. LangGraph/team orchestration selects and coordinates worker execution; each worker still reaches a concrete executor through the normal execution adapter/router.

### 2.4 Binding

A Binding is the reusable selection that ties execution to model access:

```text
binding_id
executor_id
connection_id
model_id
optional bounded executor settings
```

Examples:

```text
coding-fast
  executor   = OpenCode
  connection = SenseNova API
  model      = sense-xxx

coding-strong
  executor   = Codex
  connection = OpenAI account
  model      = gpt-xxx
```

Task creation should reference a Binding/profile, rather than duplicating provider credentials and executor configuration into every task.

## 3. Single-configuration principle

The product UX requirement is:

> **The user configures/authenticates a provider once. Executor adapters consume that Connection without asking the user to configure the same credential again.**

This does **not** mean copying secrets into every executor's config store.

The adapter should choose the least-privilege integration supported by the executor:

```text
Connection Registry
        |
        v
Executor Adapter
        |
        +-- inject bounded child-process environment when supported
        +-- generate bounded transient provider config when supported
        +-- reference an executor-owned authenticated session when account login is native
        +-- fail with an actionable unsupported-binding error when no safe adapter exists
```

Raw credentials must not be persisted into TaskStore, frontend state, evidence, logs, or source-controlled config.

## 4. OpenCode-specific rule

Task 3B behavior:

```text
Task.binding_ref
  -> trusted-loopback Binding / Connection / ExecutorDescriptor lookup
  -> provider/model normalization
  -> bounded secret-free OPENCODE_CONFIG_CONTENT
  -> explicitly allowlisted child environment
  -> OpenCode launch
```

The adapter supports `none`, `external_cli_session`, and `account_login`.
Session-backed methods require the sanitized public session status to be
`available`. Model-Control-owned `api_key` connections fail closed before
subprocess launch because Task 3B does not transport a reverse-agent credential
to OpenCode.

Target behavior:

```text
selected Binding
  -> selected Connection
  -> OpenCode adapter
  -> use supported OpenCode provider/env/session mechanism
  -> launch OpenCode
```

The adapter does not scrape or migrate OpenCode credentials. Existing OpenCode
account/login state is reused only through OpenCode's normal runtime locations;
reverse-agent does not inspect or export the auth store.

For Binding launches, reverse-agent copies only an explicit allowlist of
non-secret runtime/location variables into the child environment and adds a
transient `OPENCODE_CONFIG_CONTENT` containing only provider and `baseURL`
metadata. That config, the complete child environment, and upstream Model
Control response bodies are not persisted into TaskStore, events, or evidence.

If OpenCode requires a provider-specific configuration that cannot be safely supplied transiently, the product must expose that as an explicit connection requirement instead of pretending inheritance succeeded.

## 5. Model Control migration

The current Model Control implementation is useful and should be evolved, not discarded.

KEEP:

- loopback-only trusted host service;
- secret-not-returned behavior;
- environment-variable secret references;
- connection test/probe concept;
- frontend settings surface.

REWRITE / SPLIT:

- current `ModelProfile` coupling of provider/model configuration with executor choice;
- executor field inside provider profile;
- assumption that saving a model profile is sufficient to configure every executor.

Target logical stores/interfaces:

```text
ConnectionRegistry
ExecutorRegistry
BindingRegistry
```

These names are conceptual; implementation may reuse existing files/types if that yields a thinner migration.

Do not create three databases merely because there are three logical registries. Prefer one trusted configuration service/store unless implementation evidence proves otherwise.

Task 3A follows that rule by extending the existing process-local
`ModelProfileStore`. Public Connection responses expose only sanitized status;
raw API keys stay process-local, environment-variable names are retained only
inside the trusted store, and account/external-CLI Connections record status
without accepting raw session credentials. Bindings contain identifiers only
and are rejected when their Connection or Executor reference is unknown.

## 6. GitHub/repository connection is a separate domain

GitHub is not a model provider Connection.

Repository integration should have its own connection concept:

```text
RepositoryConnection
  -> GitHub App / OAuth / gh authenticated session / existing git credential
  -> accessible repositories
  -> selected repository
  -> publication capability/status
```

Mature-component-first applies:

- prefer GitHub App/OAuth or trusted `gh`/git credential integration;
- do not implement a custom credential protocol;
- reverse-agent should expose sanitized connection status and repository selection;
- publication/merge authority remains separate from executor/model credentials.

## 7. Product startup / setup UX

Current `dev-up.ps1` is **one-command**, not a true one-click launcher.

Target first-run/status UX:

```text
Reverse Agent

Connections
  SenseNova       [Connected]
  OpenAI account  [Connected / Login]
  GitHub          [Connected / Connect]

Executors
  OpenCode        [Installed / Login status]
  Codex           [Installed / Login status]

Bindings
  coding-fast     OpenCode + SenseNova + model-x
  coding-strong   Codex + OpenAI account + model-y

Runtime
  Frontend        Running
  Task API        Running
  Model Control   Running

[Open Workspace]
```

The launcher should remain thin and reuse `dev-up.ps1` / `dev-down.ps1` lifecycle, PID ownership, health checks and fail-closed behavior.

Do not build a large desktop runtime before the thin launcher is proven.

## 8. Live connection probe correction

Current Model Control live `/models` probe is fail-closed unless `REVERSE_AGENT_MODEL_CONTROL_LIVE=1`, while the standard `dev-up.ps1` path does not enable it.

Therefore current UI may expose "Test connection" while normal startup returns `live_probe_disabled`.

Modernization must make this UX explicit and coherent. Acceptable solutions include a trusted opt-in control/startup configuration, but live network access must remain explicit rather than silently enabled.

## 9. Migration order

The agreed sequence is:

```text
#151 LangGraph real parallel team foundation (done)
        |
        v
Product Setup & Connections
  - Task 3A: Connection / Executor / Binding foundation (done in #165)
  - Task 3B: secret-free OpenCode Binding consumption (implemented in #170)
  - provider/API/account status adapters
  - GitHub repository connection
  - true double-click/thin launcher
  - coherent live connection probe
        |
        v
real OpenCode Multi-Agent dogfood
        |
        v
continue broader Modernization using the dogfood path
```

This Product Setup & Connections phase should be small and adapter-driven. It must not become a new OAuth/provider framework.

## 10. Mature-component-first rules

For every connection/auth/executor feature, ask first:

```text
Does the provider/executor already support this?
```

If yes:

```text
REUSE -> ADAPT -> expose sanitized status
```

If no and the capability is reverse-agent-specific:

```text
implement the smallest domain layer needed
```

Avoid:

```text
custom OAuth implementation
custom provider SDK when OpenAI-compatible/LiteLLM already fits
credential copying between tools
multiple independent secret stores
executor-specific duplicated provider configuration UIs
```

## 11. Acceptance criteria for the Product Setup implementation phase

The design is considered implemented only when all of the following are proven:

- one provider/API Connection can be configured once and consumed by a supported executor adapter without a second manual credential entry;
- account-login/external-session connections are represented separately from API-key connections;
- OpenCode configuration inheritance behavior is explicit and tested rather than assumed;
- no raw provider credential enters TaskStore/frontend/evidence/logs;
- GitHub connection/repository selection is distinct from model/provider connections;
- executor selection is distinct from provider/auth selection;
- a Binding identifies Executor + Connection + Model;
- standard startup accurately reports prerequisites/connection status;
- a user-facing double-click/thin launcher reuses the existing service lifecycle;
- live connection testing has an explicit trusted opt-in path;
- old `ModelProfile.executor` coupling has a documented retirement/migration path.

Task 3A satisfies the structural subset: distinct sanitized Connection,
Executor, and Binding contracts; fail-closed references; trusted-loopback CRUD;
and legacy ModelProfile compatibility. Task 3B proves secret-free Binding
consumption for `none` and available executor-owned sessions while preserving
the legacy path. It deliberately does not satisfy the provider-API
single-configuration criterion: Model-Control-owned `api_key` bridging remains
a separate design task.

## 12. Non-goals

This design does not authorize:

- rewriting OpenCode/Codex/OpenHands authentication;
- implementing provider OAuth from scratch;
- storing browser-readable credentials;
- introducing `executor_kind="multi_agent"`;
- replacing LangGraph orchestration;
- granting automatic merge/release authority;
- modifying frozen PR #146 merely to implement connection settings.
