# Issue #131 — OpenCode Real Executor Proof v1 (BLOCKED)

## Metadata

| Field | Value |
|-------|-------|
| Branch | `owner/issue131-opencode-real-executor-v1` |
| Base/main SHA | `e4e23028c6c78c4ab9a8e032677e71370ace7627` |
| Decision ID | `decision_20260808_issue131_opencode_real_executor_v1` |
| Decision commit | `e2a8af7a9a6a0af0c93fd95d2df3a86ac935cec7` |
| Gate commit | `3a5dadf7a5492efb3db15b5f994e41ed0176181c` |
| Preflight result | `PRE_EXECUTION_AUTHORIZED` |
| Blocking reasons | `[]` |
| Risk tier | R3 |
| Status | **BLOCKED — CLI_NOT_FOUND** |

## OpenCode CLI Audit

| Check | Result |
|-------|--------|
| `where.exe opencode` | NOT FOUND |
| `opencode --version` | CommandNotFoundException |
| `opencode run --help` | CommandNotFoundException |
| `opencode models` | NOT RUN (CLI absent) |
| Global npm | no `opencode` package |
| Common paths | no `opencode` binary in Program Files, `%APPDATA%\npm`, `%USERPROFILE%\.opencode` |

## OpenCode Capabilities

- **present**: false
- **version**: unknown
- **provider_id**: unknown
- **model_id**: unknown
- **non_openai**: unverified (CLI absent)
- **exit_code**: N/A (CLI not found)

## Observed System State

npm global packages include `agent-browser`, `claude`, `codex` but no `opencode`.

The machine has Python with the reverse-agent gate module, git, and npm, but OpenCode is not installed.

## Fixture Preparation

**Not executed.** Per Step 7, no fixture creation or OpenCode execution was performed because the CLI was not found. The disposable fixture directory `F:\reverse-agent-labs\issue131-opencode-executor` was not created or modified.

## Execution Result

| Item | Value |
|------|-------|
| Fixture directory | `F:\reverse-agent-labs\issue131-opencode-executor` (NOT CREATED) |
| OpenCode invocation shape | N/A |
| Process exit status | N/A |
| Event/action evidence | N/A |
| Input read | N/A |
| Tool/shell evidence | N/A |
| Output created | N/A |
| Exact-content verification | N/A |
| Verification action evidence | N/A |
| Credential exposure | false |
| Repository integrity | Preserved |

## Repository Integrity

- `git diff --check` from base to HEAD: **NOT RUN** (no OpenCode changes to validate)
- Changed repository paths from base `e4e23028c6c78c4ab9a8e032677e71370ace7627` to HEAD `3a5dadf7a5492efb3db15b5f994e41ed0176181c`:
  - `project_state/gates/bootstrap_state.json`
  - `project_state/gates/command_plan.json`
  - `project_state/gates/startup_snapshot.json`
  - `project_state/gates/transition_command_plan_preview.json`
  - `project_state/gates/transition_preflight_result.json`
  - `docs/research/opencode-real-executor-2026-08-08.md`
  - `docs/research/opencode-real-executor-2026-08-08.json`
- `reverse_agent/**`: untouched
- `frontend/**`: untouched
- `tests/**`: untouched
- `.github/**`: untouched
- Product delta: ZERO
- Reverse-agent source mutation: FALSE

## Outcome

```
REAL_SINGLE_AGENT_EXECUTOR_PATH_ESTABLISHED = FALSE
SELECTED_EXECUTOR_PATH = NONE
INTEGRATION_SURFACE_RECOMMENDATION = BLOCKED_CLI_NOT_FOUND
PRIMARY_BLOCKER = CLI_NOT_FOUND
```

**Rationale**: The OpenCode CLI executable was not found on the current machine. It is not installed globally via npm, not present in PATH, and not found in common installation locations. Per the Decision, provider configuration mutation and package installation are forbidden (`provider_configuration_mutation_allowed: false`, `package_installation_allowed: false`). Without the OpenCode CLI, the real executor proof cannot proceed.

## Recommended Action

Install OpenCode CLI from an authorized, verified source, then re-run this round. No configuration or credential changes were made during this round.

```
ISSUE131_OPENCODE_EXECUTOR_BLOCKED_CLI_NOT_FOUND
```
