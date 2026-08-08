# Issue #131 — OpenCode Real Executor Proof v1 (BLOCKED)

## Metadata

| Field | Value |
|-------|-------|
| Branch | `owner/issue131-opencode-real-executor-v1` |
| Base/main SHA | `e4e23028c6c78c4ab9a8e032677e71370ace7627` |
| Decision ID | `decision_20260808_issue131_opencode_real_executor_v1` |
| Decision commit | `e2a8af7a9a6a0af0c93fd95d2df3a86ac935cec7` |
| Gate commit | `3a5dadf7a5492efb3db15b5f994e41ed0176181c` |
| Report commit | `4a9362be` |
| Preflight result | `PRE_EXECUTION_AUTHORIZED` |
| Blocking reasons | `[]` |
| Risk tier | R3 |
| Status | **BLOCKED — CLI_NOT_FOUND** |

## OpenCode Installation Audit

### Desktop App (FOUND)

| Property | Value |
|----------|-------|
| Executable | `C:\Users\wjc27\AppData\Local\Programs\@opencode-aidesktop\OpenCode.exe` |
| Version | `1.18.14` |
| App type | Electron GUI application |
| Package | `@opencode-aidesktop` |
| Data dir | `%APPDATA%\ai.opencode.desktop\` |
| Current session | This session runs inside this OpenCode Desktop instance |

### CLI Tool (`opencode run`) — NOT FOUND

| Check | Result |
|-------|--------|
| `where.exe opencode` | NOT FOUND in PATH |
| `opencode --version` | CommandNotFoundException |
| `opencode run --help` | CommandNotFoundException |
| `opencode models` | NOT RUN (CLI absent) |
| `OpenCode.exe --version` (full path) | Launches GUI, no CLI version output |
| `npm view opencode` | 404 Not Found — no public npm CLI package exists |
| Global npm packages | `agent-browser`, `claude`, `codex` — no `opencode` CLI |
| App.asar contents | Electron GUI assets, `node_modules` for pty/watcher/msgpackr — no CLI entry point |

## OpenCode Capabilities (Decision-authorized CLI)

| Capability | Value |
|------------|-------|
| `opencode run` exists | **false** |
| `--model` flag | unverified (no CLI) |
| `--dir` flag | unverified (no CLI) |
| `--format json` flag | unverified (no CLI) |
| `--auto` flag | unverified (no CLI) |
| Provider/model identifiers | unavailable (CLI absent) |

## OpenCode Capabilities (Desktop App)

- **present**: true
- **version**: `1.18.14`
- **package**: `@opencode-aidesktop`
- **runtime**: Electron
- **CLI surface**: none exposed
- **Child-process `run` API**: unavailable
- **Exit code**: N/A (Desktop app launched, not a CLI child process)

## Architecture Finding

The Decision authorizes only the `OPENCODE_RUN_CHILD_PROCESS` integration surface — i.e., spawning `opencode run <model> --dir <path> --format json --auto "<task>"` as a child process.

**This integration surface does not exist on this machine.** The installed OpenCode (`@opencode-aidesktop` v1.18.14) is an Electron desktop GUI application with no exposed CLI `run` subcommand. The public npm registry has no `opencode` CLI package (HTTP 404).

The current session runs *inside* the OpenCode Desktop app, but that does not constitute a `run` subcommand that can be spawned as a child process. A different integration surface — e.g., Desktop app extension API, IPC bridge, or ACP protocol — would be required to execute the fixture task, but those surfaces are outside the Decision's scope (Decision forbids ACP testing and authorizes only `opencode run`).

## Fixture Preparation

**Not executed.** The `opencode run` command required by the Decision is not available. The disposable fixture directory `F:\reverse-agent-labs\issue131-opencode-executor` was not created or modified.

## Execution Result

| Item | Value |
|------|-------|
| Fixture directory | `F:\reverse-agent-labs\issue131-opencode-executor` (NOT CREATED) |
| OpenCode invocation shape | N/A (`opencode run` not available) |
| Process exit status | N/A |
| Event/action evidence | N/A |
| Input read | N/A |
| Tool/shell evidence | N/A |
| Output created | N/A |
| Exact-content verification | N/A |
| Verification action evidence | N/A |
| Credential exposure | **false** |
| Repository integrity | **preserved** |

## Repository Integrity

- `git diff --check e4e23028c6c78c4ab9a8e032677e71370ace7627..HEAD`: **PASSED** (no output)
- Changed paths from base to HEAD `4a9362be`:
  - `project_state/decision_packet.md` (pre-existing Decision)
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
- Product delta: **ZERO**
- Reverse-agent source mutation: **FALSE**

## Outcome

```
REAL_SINGLE_AGENT_EXECUTOR_PATH_ESTABLISHED = FALSE
SELECTED_EXECUTOR_PATH = NONE
INTEGRATION_SURFACE_RECOMMENDATION = BLOCKED_CLI_NOT_FOUND
PRIMARY_BLOCKER = CLI_NOT_FOUND
ARCHITECTURAL_NOTE = OPENCODE_DESKTOP_APP_PRESENT_NO_CLI_RUN_SUBCOMMAND
```

**Rationale**: OpenCode Desktop v1.18.14 (`@opencode-aidesktop`) IS installed and is the running environment for this session. However, it exposes no `opencode run` CLI subcommand. The public npm registry has no `opencode` CLI package. The Decision's authorized integration surface (`OPENCODE_RUN_CHILD_PROCESS`) is therefore unavailable. Per Decision constraints, package installation, provider configuration mutation, and ACP testing are all forbidden.

## Recommended Action

1. **If the intent is to use OpenCode Desktop as the executor**, a revised Decision must authorize a Desktop-app integration surface (extension API, IPC, or equivalent) and define the equivalent of `opencode run` for that surface.
2. **If the intent is to use a `run` CLI subcommand**, confirm the correct package name, install source, and verify availability before re-authorizing.
3. No configuration, credential, or product changes were made during this round.

```
ISSUE131_OPENCODE_EXECUTOR_BLOCKED_CLI_NOT_FOUND
```
