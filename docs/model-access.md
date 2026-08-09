# Model access module

## Purpose

The model access module separates provider/model configuration from task execution. The frontend selects a sanitized model profile. A trusted-host process owns provider secrets and connection probes. OpenHands and Codex ACP remain executor choices; Codex login material is not stored in a model profile.

## Supported profiles

- `openai-compatible`: any endpoint exposing an OpenAI-compatible `/models` API.
- `litellm-proxy`: a LiteLLM Proxy endpoint using logical model aliases.

Each profile contains:

```json
{
  "id": "coding-default",
  "name": "Default coding model",
  "provider": "litellm-proxy",
  "base_url": "http://localhost:4000/v1",
  "model_id": "coding-default",
  "executor": "openhands",
  "enabled": true,
  "is_default": true,
  "api_key_env": "LITELLM_VIRTUAL_KEY"
}
```

`api_key` may be submitted to the service for the current process, but is never returned. `api_key_env` stores only an environment-variable name.

## Start the trusted-host service

Python 3.13 is required.

```powershell
$env:REVERSE_AGENT_MODEL_PROFILES_JSON = '[{"id":"coding-default","name":"Default coding model","provider":"litellm-proxy","base_url":"http://localhost:4000/v1","model_id":"coding-default","executor":"openhands","enabled":true,"is_default":true,"api_key_env":"LITELLM_VIRTUAL_KEY"}]'
$env:LITELLM_VIRTUAL_KEY = "replace-on-host"
python -m reverse_agent.model_access.service
```

Defaults:

- bind host: `127.0.0.1`
- port: `8765`
- allowed browser origin: `http://localhost:5173`
- live probes: disabled

Optional environment variables:

```text
REVERSE_AGENT_MODEL_CONTROL_HOST
REVERSE_AGENT_MODEL_CONTROL_PORT
REVERSE_AGENT_MODEL_CONTROL_ORIGIN
REVERSE_AGENT_MODEL_CONTROL_LIVE
REVERSE_AGENT_MODEL_PROFILES_JSON
```

`REVERSE_AGENT_MODEL_CONTROL_HOST` accepts only `localhost` or a loopback IP such as `127.0.0.1`/`::1`. The service intentionally refuses wildcard, LAN and public bindings because this first version has no remote authentication layer.

Set `REVERSE_AGENT_MODEL_CONTROL_LIVE=1` only on a trusted host when real `/models` probes are intended.

## Start the frontend

Normal HTTP mode:

```powershell
$env:VITE_MODEL_CONTROL_API_BASE = "http://127.0.0.1:8765/api"
npm --prefix frontend run dev
```

Standalone mock mode:

```powershell
$env:VITE_MODEL_CONTROL_MODE = "mock"
npm --prefix frontend run dev:mock
```

Mock mode contains no provider secret and does not invoke a real model.

## LiteLLM placement

Recommended deployment:

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
        +-- free/education provider
        +-- local OpenAI-compatible endpoint
```

The profile `model_id` should be a LiteLLM logical alias such as `coding-default`; upstream provider changes then do not require frontend changes.

## Planned quota and budget extension

Quota, provider balance, usage/cost accounting and budget-aware model scheduling belong to this same `model_access` plane rather than a separate API-key management subsystem.

The fixed long-term plan is documented in:

```text
docs/roadmap/model_access_quota_budget_plan.md
```

Key boundaries:

- provider-authoritative balance/quota must remain distinct from gateway accounting and estimates;
- LiteLLM remains the default gateway/routing candidate and should provide generic accounting/budget capabilities where possible;
- provider-specific quota support should use thin trusted-host adapters and official APIs/headers where available;
- New API is a reference/optional reuse candidate for provider balance-refresh patterns, not an automatic second gateway;
- every quota/balance value exposed to the frontend must carry provenance and freshness;
- resource/cost signals may later influence deterministic model scheduling but may not bypass execution, permission or trust gates.

This roadmap does not mean quota/billing is implemented in the current version.

## Security boundaries

- The model-control service is loopback-only.
- The browser does not call provider endpoints directly.
- API keys are not written to localStorage, sessionStorage, fixtures, task objects, logs or API responses.
- In-process secrets disappear when the model-control service restarts.
- Environment-backed secrets are resolved only by variable name.
- Live network probes fail closed unless explicitly enabled.
- The module configures model access only; it does not prove that an OpenHands or Codex ACP execution completed.

## Verification

```powershell
powershell -ExecutionPolicy Bypass -File frontend/OWNER_LOCAL_VERIFICATION.ps1
```

Focused commands:

```powershell
python -m pytest tests/test_model_access.py -q
npm --prefix frontend test
npm --prefix frontend run typecheck
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix frontend run build:mock
```
