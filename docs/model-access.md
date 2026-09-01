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

## Durable API-key persistence (OS credential store)

On platforms with a supported OS credential store, an `api_key` Connection can persist its secret durably instead of keeping it only for the current process:

- Windows: the Windows Credential Manager, reached from trusted-host Python code through the standard library only;
- other platforms: no OS-backed adapter is instantiated; Connections keep the exact legacy process-local behavior.

How it works:

- Saving an API key writes the OS credential store item first; only then is sanitized state persisted. The sanitized state contains only a non-secret `credential_ref`; secret bytes never enter the state file, TaskStore, evidence, logs, public JSON or frontend storage.
- The `credential_ref` is derived from and bound to the Connection authority (connection id, provider, base URL, auth method). Changing an authority-bearing field changes the reference, so a stale stored item can never be silently reused, and one Connection can never resolve another Connection's item.
- After a trusted-host restart, a fresh store over the same sanitized state resolves the secret from the OS credential store without re-entry. Public reads report status only; the secret is never read back to the frontend after save or restart.
- Execution resolves the secret at point of use through the credential store. A locked or unavailable store fails closed for execution and for saving; there is never a plaintext fallback.
- Removing a saved key or deleting the Connection removes only the Nerelan-owned OS credential store item.

Public `secret_status` vocabulary for the `api_key` path:

```text
missing               no credential configured
session               in-process secret for the current service run
environment           resolved by environment-variable name
stored                durably saved and currently available in the OS store
store_locked          OS credential store locked or unavailable
replacement_required  stored item no longer exists (removed externally); re-enter the key
```

Uninstall / portable mode:

- Vault items live in the OS credential store of the machine and user account that saved them. They are not part of the repository, the frontend bundle or any product directory.
- Vault items are not exported with normal configuration or state backup: the persisted sanitized state carries only the non-secret `credential_ref`, and copying or exporting that state file does not carry the secret.
- Uninstalling the application or deleting its data directory does not remove OS credential store items; remove a saved key explicitly in the Connection editor (clear secret) or delete it in the OS credential store itself.
- Moving an exported sanitized state file to another machine or user account leaves `credential_ref` entries unresolvable there; they surface as `replacement_required` and the key must be re-entered.

## OpenAI / ChatGPT account login and GPT models

An enabled Connection with `provider=openai` and `auth_method=account_login`
uses OpenCode's native provider OAuth surface. This is the account path for
OpenAI / ChatGPT subscriptions and the corresponding GPT models selected by a
Binding; `gpt` is a model family, not a second provider identifier.

The flow is deliberately a thin adapter:

1. the trusted host starts one transient password-protected OpenCode server on loopback;
2. it asks OpenCode for the authentication methods currently advertised for the exact `openai` provider and selects an advertised OAuth method;
3. the frontend opens the returned HTTPS continuation URL; OpenCode owns PKCE, provider callback processing, access/refresh rotation and durable session storage;
4. for a code flow, the browser submits only the transient code to the trusted host; for an automatic callback it submits no code;
5. after callback, the transient server is closed and a fresh sanitized `opencode auth list` probe must observe `openai` before the Connection reports `available`.

The authorization URL and optional code exist only for the active bounded flow.
They are not written to sanitized state, TaskStore, browser storage, evidence or
logs. Reverse-agent never opens OpenCode's credential file and never receives an
access token, refresh token, cookie or PKCE verifier.

Cancel stops the transient server. OpenCode's provider OAuth HTTP API does not
currently expose credential removal, so the UI truthfully returns
`provider_logout_required` and directs the user to OpenCode `auth logout`; it
does not edit provider-owned storage or claim a logout that did not happen.

Existing OpenCode account or CLI sessions remain reusable without running a new
login flow. On trusted-host startup and before session-backed Binding resolution,
the same sanitized auth-list probe refreshes `external_session_status`; only
`available` is dispatchable.

## Security boundaries

- The model-control service is loopback-only.
- The browser does not call provider endpoints directly.
- OpenAI OAuth authorization is delegated to an authenticated loopback OpenCode server; only its HTTPS browser continuation leaves loopback.
- API keys are not written to localStorage, sessionStorage, fixtures, task objects, logs or API responses.
- In-process secrets disappear when the model-control service restarts; vault-backed secrets are resolved again from the OS credential store at point of use.
- No plaintext fallback exists: when the OS credential store is unavailable, saving, public status and execution all fail closed with an explicit typed state.
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
