# User Journey Validation Gate

Status: project-level testing and acceptance requirement

## Purpose

Frontend correctness is not proven by unit, integration, API, component, or deterministic browser tests alone. A change can pass those checks while a real user still cannot discover, understand, or complete the intended workflow.

The project therefore treats user-visible frontend behavior as a separate validation surface and adopts a **User Journey Validation Gate** for critical user journeys.

The core invariant is:

> Lower-level test PASS does not substitute for proof that a user can complete the intended frontend journey through the visible UI.

## Testing stack

Frontend-impacting work should be validated through layered evidence:

1. Unit tests.
2. Integration tests.
3. API / contract tests.
4. Deterministic Playwright E2E tests for known critical paths and regressions.
5. Human-like Agent QA operating the rendered frontend as a black-box user.
6. Exploratory UI / UX evaluation.
7. User Journey verification.
8. Evidence-backed PASS / WARN / FAIL report.

Deterministic Playwright and human-like Agent QA are complementary, not interchangeable. Playwright protects known paths with reproducible assertions. The exploratory agent tests whether the interface can actually be used without being given the implementation's hidden knowledge.

## Black-box Agent contract

The exploratory test agent must behave like a user of the product.

Unless a test explicitly targets a developer-only flow, the agent must not:

- read source code to discover the intended interaction path;
- call internal application APIs as a shortcut around the UI;
- inspect or modify the database directly;
- bypass controls with DOM/script injection merely to make the journey pass;
- use hidden implementation knowledge that a normal user would not possess.

The agent should use browser-visible interaction: inspect the rendered page, click/tap controls, type, select, upload, scroll, wait for state transitions, observe notifications and errors, and judge whether the next action is understandable.

A first-time-user scenario should receive the **goal**, not a selector-by-selector script. Example: "Configure a provider, verify the connection, create a task with an image, run it, follow its execution, and inspect the completed result."

## Critical journeys

At minimum, the gate must cover the product's primary frontend lifecycle:

`Provider configuration -> Verify connection -> Create task -> File/image input -> Agent orchestration/configuration -> Start task -> Observe live execution -> Reach terminal completion/failure state -> Inspect result/evidence -> Recover or retry after failure`

As new user-facing capabilities become release-critical, their primary journey must be added to this set rather than relying only on feature-local tests.

## What the exploratory agent must look for

The agent should actively report, rather than work around, problems such as:

- controls that are visible but do nothing;
- loading states that never reach a bounded terminal state;
- swallowed or invisible errors;
- success messages that contradict backend/visible state;
- stale or inconsistent task status;
- actions whose effect is not visible to the user;
- unclear labels, ambiguous controls, missing affordances, or no understandable next step;
- workflows that require guessing undocumented order or hidden prerequisites;
- file/image input that appears accepted but is not actually bound to the task;
- execution views that are effectively a black box while work is running;
- terminal states that fail to communicate completion, failure, retry, or recovery;
- layout/responsive defects that make controls inaccessible or materially impair use;
- regressions in keyboard/focus/accessibility behavior where relevant to the tested path.

## Personas

The exploratory layer should eventually run more than one behavioral profile:

- **Novice / first-time user**: no repository or implementation knowledge; primary usability gate.
- **Technical AI-agent user**: understands providers, agents, tasks, and model configuration.
- **Advanced operator**: familiar with systems such as Codex/OpenHands and expects observability and control.
- **Error-seeking user**: intentionally supplies invalid, missing, duplicate, or conflicting input to test recovery and explanation.

The novice persona is the most important signal for discoverability. If lower-level tests and scripted E2E pass but the novice agent cannot complete a critical journey through visible UI, the result is not a full frontend PASS.

## Evidence contract

Every agentic journey run should produce a structured evidence record. At minimum record:

- journey ID and persona;
- build/commit under test;
- step number and user goal;
- visible action taken;
- expected observable result;
- actual observable result;
- PASS / WARN / FAIL;
- severity for a finding;
- screenshot on failure and at important state transitions;
- Playwright trace/video where available;
- elapsed/wait state when timeout or stuck-loading is involved;
- classification: product defect, test/agent flake, or environment/infrastructure issue;
- concise reason explaining why the result affects or does not affect user completion.

Evidence must make a failure reproducible enough for an owner or implementation agent to understand the user-visible break without relying on an ungrounded model judgment.

## Gate semantics

A frontend-impacting change can satisfy the User Journey Validation Gate only when:

1. required deterministic E2E journeys pass;
2. required black-box agent journeys either pass or have explicitly accepted limitations;
3. no unresolved high-severity finding prevents completion of a critical journey;
4. evidence artifacts exist for the run;
5. failures have been classified so product bugs are not silently dismissed as agent flakiness;
6. user-visible status reaches bounded and understandable terminal states;
7. success assertions match what the user can actually observe.

A UX/user-journey FAIL may block release independently of unit, integration, API, or deterministic E2E PASS.

## Execution policy

Use the following rollout model:

### Phase A - deterministic critical journeys

- retain/expand Playwright coverage for critical frontend workflows;
- standardize traces, screenshots, terminal-state assertions, and failure artifacts;
- ensure tests validate actual user-visible state, not only request success.

### Phase B - novice exploratory agent

- add one black-box first-time-user agent journey;
- provide only goals and allowed interaction constraints;
- produce structured evidence and finding classification;
- run initially as an advisory signal while flake sources are measured.

### Phase C - multi-persona and negative-path coverage

- add technical/operator/error-seeking personas;
- run exploratory journeys on frontend-impacting PRs when practical and on scheduled/release validation;
- deduplicate recurring findings and preserve regression scenarios as deterministic Playwright tests where possible.

### Phase D - blocking gate

Promote the User Journey Validation Gate from advisory to blocking after the project establishes acceptable stability, bounded cost/runtime, reproducible failure classification, and a documented policy for reruns/flakes.

## Regression rule

When an exploratory agent discovers a reproducible product defect:

1. preserve the agent evidence;
2. fix the product defect;
3. where feasible, convert the discovered failure into a deterministic Playwright regression test;
4. keep exploratory coverage capable of finding failures outside the already-scripted path.

This prevents the project from repeatedly rediscovering the same bug while retaining the exploratory layer's ability to find new classes of failure.

## Relationship to existing frontend verification

Existing owner verification and Playwright coverage remain valid deterministic evidence. This policy adds the missing black-box usability/exploration layer; it does not replace existing tests.

## Definition of Done for the capability

This capability is considered fully implemented when the repository contains:

- deterministic Playwright coverage for every current critical journey;
- a reusable black-box browser-agent runner or adapter;
- goal-based novice journey definitions;
- evidence artifact schemas and persisted run output;
- failure classification and bounded retry/timeout policy;
- multi-persona/negative-path support;
- CI/release routing rules for frontend-impacting changes;
- a machine-evaluable User Journey Validation Gate result;
- documentation that makes the gate's PASS/WARN/FAIL semantics auditable.

Until those implementation items exist, this document and the corresponding roadmap item establish the requirement and target architecture; they do not falsely claim that the complete gate is already automated.