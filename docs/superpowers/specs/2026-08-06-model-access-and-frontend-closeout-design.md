# Model Access and Frontend Closeout Design

## Scope

This change starts from the verified Frontend V1 exact head `68445abdcd6e66c3ad5c4534a9dd5c1c2414e47d`. It closes the remaining Settings and New Task placeholders and adds a bounded model-access control plane. It does not implement the task executor, sandbox, OpenHands runtime, Codex ACP transport, billing, user accounts or persistent secret storage.

## Audit baseline

- PR #119 is draft and its frontend exact-head record reports 78/78 tests, typecheck, lint, production build and mock build passing.
- Repository CI has two mainline-intent failures outside the frontend product code.
- `frontend/src/routes/settings.tsx` is a placeholder.
- `frontend/src/components/new-task-composer.tsx` has no model selector and does not submit a task.
- `frontend/src/hooks/use-tasks.ts` is fixture-only.

## Architecture

### Model profile domain

The frontend owns only non-secret profile metadata: id, name, provider kind, base URL, model id, executor kind, default flag, enabled flag and secret status. Provider kinds are `openai-compatible` and `litellm-proxy`. Executor kinds are `openhands` and `codex-acp`. Codex ACP remains an executor selection and never stores Codex login material in a model profile.

### Model control API

The browser calls `/api/model-profiles`. The client supports list, upsert, delete, set-default and connection-test operations. API keys may be sent only on write/test requests and are never returned in responses or stored in browser persistence.

A deterministic in-memory mock implementation is enabled only with `VITE_MODEL_CONTROL_MODE=mock`. Normal mode uses HTTP and exposes connection errors.

### Settings UI

The Settings page becomes a model configuration workspace with profile list, create/edit form, provider and executor selectors, base URL, model id, one-time API key input, save, connection test, default selection and delete actions. Security copy states that browser storage is not used for API keys.

### New Task integration

The composer loads enabled profiles, preselects the default profile and requires a model profile before submission. It emits `CreateTaskInput` with title, model profile id and permission policy. The current fixture shell inserts the created task into the React Query cache without claiming that an executor ran.

### Trusted-host service

A dependency-free Python HTTP service implements the API for local trusted-host use. It stores secrets in memory only, can resolve secrets from environment variables, masks secret state in responses and probes OpenAI-compatible `/models` endpoints only when `REVERSE_AGENT_MODEL_CONTROL_LIVE=1`. CORS is restricted by `REVERSE_AGENT_MODEL_CONTROL_ORIGIN`.

## Error handling

Invalid fields return validation errors. HTTP failures are normalized for the UI. Connection testing distinguishes disabled live probes, authentication failures, timeout and upstream HTTP failures. Failed tests do not erase saved metadata and never retain submitted API keys in the browser.

## Testing

Frontend tests cover schemas, mock CRUD/default behavior, Settings interactions and New Task model selection. Python tests cover profile validation, secret masking, default uniqueness, environment-secret loading, disabled live probes and injectable probe behavior.

## Acceptance criteria

1. Settings is no longer a placeholder.
2. OpenAI-compatible and LiteLLM profiles can be created, edited, tested, set default and deleted.
3. API keys are never returned, logged or persisted by the browser.
4. New Task requires and submits a model profile id.
5. Codex ACP remains separate from provider credentials.
6. Frontend test, typecheck, lint and build commands pass.
7. Python model-control tests pass.
8. The change is published as a separate draft PR based on the Frontend V1 branch.
