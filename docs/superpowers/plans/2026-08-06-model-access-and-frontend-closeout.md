# Model Access and Frontend Closeout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Frontend V1 model placeholders with a secure, testable model-profile control plane and integrate model selection into task creation.

**Architecture:** Add a shared model-profile contract, an HTTP/mock frontend client, an OpenHands-style Settings workspace, a model-aware New Task composer and a dependency-free trusted-host Python service. Keep provider credentials out of browser persistence and keep Codex ACP represented as an executor rather than an API provider.

**Tech Stack:** React 19, TypeScript 5.7, TanStack Query 5, Zod 3, Vitest, Python 3.13 standard library, pytest.

## Global Constraints

- Start from Frontend V1 exact head `68445abdcd6e66c3ad5c4534a9dd5c1c2414e47d`.
- Do not persist API keys in localStorage, sessionStorage, fixtures, repository files or API responses.
- Live upstream probes require `REVERSE_AGENT_MODEL_CONTROL_LIVE=1`.
- Codex ACP credentials remain outside model profiles.
- No task executor or sandbox implementation is added in this change.

---

### Task 1: Frontend model contract and client

**Files:**
- Create: `frontend/src/schemas/model-profile.ts`
- Create: `frontend/src/lib/model-control-client.ts`
- Create: `frontend/src/hooks/use-model-profiles.ts`
- Test: `frontend/tests/model-control.test.ts`

**Interfaces:**
- Produces `ModelProfile`, `ModelProfileInput`, `ModelConnectionResult`, `modelControlClient`, `useModelProfiles`, `useUpsertModelProfile`, `useDeleteModelProfile`, `useSetDefaultModelProfile`, `useTestModelProfile`.

- [ ] Write tests for validation, secret stripping, mock CRUD and single-default behavior.
- [ ] Confirm tests fail because the modules do not exist.
- [ ] Implement schemas, normalized errors, HTTP mode and deterministic mock mode.
- [ ] Confirm focused tests pass.

### Task 2: Settings model workspace

**Files:**
- Create: `frontend/src/components/model-profile-editor.tsx`
- Modify: `frontend/src/routes/settings.tsx`
- Test: `frontend/tests/model-settings.test.tsx`

**Interfaces:**
- Consumes hooks from Task 1.
- Produces create/edit/test/default/delete user flows.

- [ ] Write interaction tests for creating a profile, testing it, setting default and deleting it.
- [ ] Confirm tests fail against the placeholder page.
- [ ] Implement the profile list, editor and status messages.
- [ ] Confirm focused tests pass.

### Task 3: Model-aware task creation

**Files:**
- Modify: `frontend/src/components/new-task-composer.tsx`
- Modify: `frontend/src/components/app-shell.tsx`
- Modify: `frontend/src/hooks/use-tasks.ts`
- Modify: `frontend/src/types/index.ts`
- Test: `frontend/tests/model-task-composer.test.tsx`

**Interfaces:**
- Produces `CreateTaskInput` and `useCreateTask`.
- New tasks include `modelProfileId` and enter `WAITING_FOR_OWNER` without claiming execution.

- [ ] Write tests for default selection, required model selection and cache insertion.
- [ ] Confirm tests fail because no model selector exists.
- [ ] Implement typed submission and cache mutation.
- [ ] Confirm focused tests pass.

### Task 4: Trusted-host model control service

**Files:**
- Create: `reverse_agent/model_access/__init__.py`
- Create: `reverse_agent/model_access/contracts.py`
- Create: `reverse_agent/model_access/store.py`
- Create: `reverse_agent/model_access/service.py`
- Create: `tests/test_model_access.py`

**Interfaces:**
- Produces `ModelProfile`, `ModelProfileStore`, `ProbeResult`, `probe_openai_compatible`, and `run_model_control_service`.

- [ ] Write tests for validation, masking, default uniqueness, environment secrets and probe gating.
- [ ] Confirm tests fail because the package does not exist.
- [ ] Implement the store, injectable probe and HTTP endpoints.
- [ ] Confirm focused Python tests pass.

### Task 5: Documentation and verification

**Files:**
- Create: `docs/model-access.md`
- Modify: `frontend/OWNER_LOCAL_VERIFICATION.ps1`

- [ ] Document local service startup, frontend environment variables, LiteLLM usage and security boundaries.
- [ ] Add model-access commands to the owner verification script.
- [ ] Run frontend tests, typecheck, lint, build, mock build and Python focused tests.
- [ ] Run repository CI through a draft PR and record exact results.
