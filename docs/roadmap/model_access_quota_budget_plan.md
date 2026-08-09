# Model Access Quota and Budget Roadmap

## 0. Document status

This document fixes the long-term quota/budget plan for the existing `model_access` subsystem.

It is a roadmap and architecture constraint, not current execution authority. It does not authorize implementation by itself. Current engineering authority remains the active project decision / work item and the repository's existing risk gates.

## 1. Goal

Extend model access so reverse-agent can distinguish and use four different resource signals:

1. provider-reported account balance / credits;
2. provider-reported quota and reset windows such as RPM, TPM, RPD or token allowances;
3. gateway-observed usage and cost;
4. reverse-agent-defined budgets and scheduling policy.

The purpose is not only to display a number in Settings. The normalized resource state should eventually become one input to model/provider selection together with capability, availability, latency, cost and user policy.

## 2. Existing placement

The existing model-access path remains authoritative:

```text
reverse-agent frontend
        |
        v
model-control service
        |
        v
LiteLLM Proxy logical model alias
        |
        +-- commercial provider
        +-- free / education provider
        +-- local OpenAI-compatible endpoint
```

Quota/budget support is an extension of this plane. Do not create a second unrelated API-key management subsystem.

## 3. Reuse-first decision

### 3.1 LiteLLM

Keep LiteLLM as the default gateway / logical-model routing candidate already adopted by the project. Reuse its mature capabilities for gateway-observed spend, budgets, virtual keys, routing and provider abstraction where they fit.

Do not reimplement generic token/cost accounting or generic gateway routing in reverse-agent unless a concrete missing requirement is proven.

### 3.2 New API

Treat New API as a reference implementation and optional reusable component for provider/channel balance refresh behavior. Its provider-specific balance-query patterns are especially relevant when an upstream exposes a real balance endpoint.

Do not automatically place New API and LiteLLM in series. A two-gateway chain adds operational state, failure modes and duplicated policy. Prefer one primary gateway plus thin provider quota adapters. Only introduce a second gateway if a measured requirement cannot be met cleanly otherwise.

Before copying or adapting implementation code, verify the exact upstream version, license and compatibility requirements.

### 3.3 Portkey / Helicone and similar projects

Use these as references for budget policy, observability, alerts and cost analytics. They are not planned as mandatory runtime dependencies.

## 4. Critical distinction: official remaining quota vs local accounting

The system must never present locally estimated remaining quota as provider-authoritative data.

A provider may expose any subset of:

```text
balance / credits endpoint
usage endpoint
quota endpoint
rate-limit response headers
reset timestamps
billing/cost reports
nothing machine-readable
```

If no authoritative machine-readable source exists, reverse-agent may estimate from a known starting allowance minus locally observed usage, but the result must be explicitly marked estimated. Usage outside reverse-agent can make that estimate wrong.

## 5. Normalized resource contract

Introduce a normalized non-secret resource record concept before implementing provider-specific UI.

Target shape:

```yaml
profile_id: coding-default
provider_id: provider-account-or-channel

availability:
  status: available
  checked_at: 2026-08-09T00:00:00Z

balance:
  value: 4.27
  unit: USD
  source: provider_api
  authoritative: true
  refreshed_at: 2026-08-09T00:00:00Z

quota:
  limit: 1000000
  remaining: 182000
  unit: tokens
  window: day
  reset_at: 2026-08-10T00:00:00Z
  source: provider_api
  authoritative: true

rate_limits:
  rpm_limit: 60
  rpm_remaining: 41
  tpm_limit: 100000
  tpm_remaining: 64000
  source: response_header

accounting:
  observed_input_tokens: 0
  observed_output_tokens: 0
  observed_cost: 0.0
  currency: USD
  source: gateway_accounting

budget:
  configured_limit: 5.0
  consumed: 0.0
  remaining: 5.0
  currency: USD
  source: reverse_agent_policy
```

The exact schema may change during implementation, but the provenance fields must survive.

## 6. Required provenance vocabulary

At minimum, resource values must identify one of these sources:

```text
provider_api
provider_usage_api
response_header
gateway_accounting
reverse_agent_policy
estimated
manual
unknown
```

Every externally refreshed value should carry `refreshed_at`. Windowed quota should carry `reset_at` where known. Values derived from local accounting must not set `authoritative=true` unless the provider contract makes that claim valid.

## 7. Adapter model

Add thin provider quota adapters behind the trusted-host model-control service rather than teaching the browser about provider secrets or provider-specific APIs.

Conceptual interface:

```text
QuotaAdapter
  supports(profile) -> bool
  fetch_balance(...) -> ResourceValue | unsupported
  fetch_quota(...) -> ResourceValue | unsupported
  parse_rate_limit_headers(...) -> ResourceValue | unsupported
```

Adapters may use:

- official provider billing/quota APIs;
- official usage APIs;
- rate-limit headers returned by normal inference requests;
- gateway accounting as a fallback;
- explicit estimation only as a last resort.

Provider secrets remain trusted-host only. The frontend receives sanitized resource state, never credentials.

## 8. Storage and refresh rules

Do not require persistent secret storage to implement quota state.

Resource observations may be persisted separately from secrets because they are operational metadata, but they must include freshness/provenance and must not be mistaken for current provider truth after expiration.

Refresh policy should support:

```text
manual refresh
refresh on connection test
refresh after inference response when headers contain quota data
bounded periodic refresh for providers with official quota APIs
```

Avoid aggressive polling. Provider terms, API limits and cost must govern refresh frequency.

## 9. Frontend plan

Extend Settings only after the backend contract is stable.

Per model/provider profile, show separately:

```text
connection status
official balance / credits (if available)
quota remaining + reset time (if available)
rate-limit headroom (if available)
locally observed usage/cost
configured reverse-agent budget
source / freshness / authoritative-or-estimated badge
```

Never collapse all of these into a single ambiguous `remaining` field.

## 10. Scheduler integration

Quota is not only a dashboard feature. After collection is reliable, expose normalized resource signals to the model scheduler.

The scheduler may eventually consider:

```text
model capability fit
provider availability
remaining authoritative quota
rate-limit headroom
reset time
observed latency
observed cost
configured budget
user preference: speed / economy / quality / custom
```

The first scheduling version must remain deterministic and explainable. It should emit a reason record for provider selection, for example:

```text
selected: provider-a/model-x
reasons:
  - satisfies required capability
  - authoritative daily quota remaining > minimum threshold
  - within configured budget
  - lower expected cost than fallback provider
fallbacks:
  - provider-b/model-y
```

Do not let quota data silently bypass permission, trust or execution gates.

## 11. Failure behavior

Quota/balance collection must fail soft for model availability but fail closed for claims about resource truth.

Examples:

- balance endpoint unavailable -> mark balance `stale`/`unknown`; do not invent zero;
- provider has no quota API -> mark unsupported; continue using gateway accounting if configured;
- estimated quota becomes stale -> do not present it as authoritative;
- malformed rate-limit headers -> ignore the value and retain an error observation;
- quota exhausted -> scheduler may avoid the provider, but execution authorization still follows existing gates.

## 12. Phased implementation plan

### Phase Q0 - provider capability audit

For each intended provider (including currently used free/limited providers), record:

```text
balance API available?
usage API available?
quota API available?
rate-limit headers?
reset semantics?
units?
official documentation?
auth scope required?
```

Output: provider capability matrix. No runtime changes.

### Phase Q1 - normalized contracts

Add resource/quota domain contracts and tests. No live provider calls required.

Acceptance:

- provenance and freshness are mandatory;
- authoritative and estimated states cannot be confused;
- secrets are absent from public response schemas.

### Phase Q2 - gateway accounting reuse

Integrate/reuse LiteLLM-observed usage/cost and reverse-agent budgets before writing many custom provider adapters.

Acceptance:

- locally observed usage is available per logical profile/provider mapping;
- local budgets are enforceable without pretending to be provider balance.

### Phase Q3 - authoritative provider adapters

Implement only the highest-value official quota/balance adapters proven by Q0. Prefer official APIs and headers. Reuse mature upstream patterns where appropriate.

Acceptance:

- each adapter has contract tests and sanitized error behavior;
- unsupported providers remain explicit;
- polling is bounded.

### Phase Q4 - Settings resource dashboard

Expose balance/quota/accounting/budget with provenance and freshness labels.

### Phase Q5 - scheduler signals

Use reliable resource state as one factor in deterministic provider/model selection. Add explanation records and fallback behavior.

### Phase Q6 - policy profiles

Support user-selectable scheduling objectives such as:

```text
economy
balanced
quality-first
latency-first
custom constraints
```

These policies are orchestration inputs, not replacements for capability or safety gates.

## 13. Non-goals and permanent boundaries

Do not:

- scrape provider web dashboards when an official machine interface is absent unless a later explicit decision authorizes and justifies it;
- claim exact remaining provider balance from local estimates;
- store provider API keys in browser storage, task objects, logs or public quota records;
- rebuild a general-purpose billing platform;
- add a second gateway merely because it has overlapping features;
- couple quota collection to Codex login material;
- make economic routing able to bypass Trust Layer / Decision / Command Plan authorization.

## 14. Acceptance criteria for the complete capability

The capability is complete only when the project can demonstrate all of the following:

1. provider-authoritative balance/quota is visibly distinct from local accounting and estimates;
2. every displayed value has source and freshness metadata;
3. unsupported provider quota is represented explicitly rather than guessed;
4. API keys remain trusted-host only;
5. LiteLLM or another selected gateway supplies generic accounting/routing functions instead of reverse-agent duplicating them;
6. provider-specific adapters are thin and independently testable;
7. stale or failed quota refresh cannot fabricate resource availability;
8. Settings can explain what remains, when it resets and where the number came from when those facts are available;
9. scheduler decisions can include quota/cost signals and emit human-readable reasons;
10. quota/cost optimization never weakens existing authorization and trust boundaries.

## 15. Architectural decision summary

Fixed direction:

```text
Keep model_access as the owning subsystem.
Keep LiteLLM as the default gateway/routing candidate.
Reuse mature accounting/budget features.
Use thin provider-specific quota adapters for official remaining balance/quota.
Use New API as a strong reference/optional reusable source for balance-refresh patterns, not as an automatic second gateway.
Normalize provenance, freshness and authoritative-vs-estimated status.
Feed reliable resource state into later model scheduling.
```

This is supporting platform infrastructure, not a claimed product differentiator. reverse-agent should spend custom engineering effort only on the gaps that mature gateway/observability projects do not already solve cleanly.
