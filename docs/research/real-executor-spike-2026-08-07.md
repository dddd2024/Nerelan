# Issue 130 — Quota-Independent Real Executor Spike v1

Date: 2026-08-07/08 (local host clock)
Risk tier: R3 (Path B, bounded Decision)
Report files:
- `docs/research/real-executor-spike-2026-08-07.md`
- `docs/research/real-executor-spike-2026-08-07.json`

## 1. Authority

| Field | Value |
|-------|-------|
| Repository | dddd2024/reverse-agent |
| Branch | `owner/issue130-real-executor-spike-v1` |
| Current main / base SHA | `e4e23028c6c78c4ab9a8e032677e71370ace7627` |
| Decision commit | `5cde87646228895c0b604311dd61a5ff1e164587` |
| Gate commit (this run) | `234ad0dbd3134a64e49a70d028aa700ae2981d71` |
| Decision ID | `decision_20260807_issue130_real_executor_spike_v1` |
| Round ID | `round_20260807_issue130_real_executor_spike_v1` |
| Merge-base (HEAD..origin/main) | `e4e23028c6c78c4ab9a8e032677e71370ace7627` (matches base) |

## 2. Gate results

| Gate | Status |
|------|--------|
| `startup-snapshot` | PASSED |
| `transition-command-plan` | PASSED (21 commands) |
| `transition-lint` | PASSED (6/6 checks) |
| `transition-preflight --mode pre` | `PRE_EXECUTION_AUTHORIZED` |

- `gate_status`: `PRE_EXECUTION_AUTHORIZED`
- `blocking_reasons`: `[]`
- All 16 preflight checks PASS.
- `startup_snapshot.json` captured pre-existing untracked artifacts under `.frontend_stage/`, `.platform_v1_runtime/`, `task_workspaces/` and preserved them without mutation.

## 3. Host

- OS: Windows_NT
- Python: present
- Pre-existing untracked local artifacts preserved (not deleted, not stashed, not cleaned):
  - `.frontend_stage/**`
  - `.platform_v1_runtime/**`
  - `task_workspaces/**`

## 4. Candidate A — CODEX_CUSTOM_PROVIDER

### Presence

- `where.exe codex` -> `C:\Users\wjc27\AppData\Roaming\npm\codex{,.cmd}` (present)
- `codex --version` -> `codex-cli 0.147.0`
- `codex exec --help` confirmed invocation shape:
  - `codex exec [OPTIONS] [PROMPT]`
  - relevant flags: `-m/--model`, `-p/--profile`, `-c/--config`, `--oss`, `--local-provider`, `-C/--cd`, `--sandbox`, `--json`, `--ephemeral`, `--skip-git-repo-check`

### Secret-safe provider metadata (whitelisted fields only)

Metadata obtained via Python parser that reads `~/.codex/config.toml` only to emit whitelisted identifiers. No env dump, no raw config dump, no credential value emission.

| Field | Value |
|-------|-------|
| config file | `~/.codex/config.toml` (base config only) |
| profile config files | none (no `<name>.config.toml` under `~/.codex/`) |
| provider_id | `openai` (built-in official provider; no `base_url` / no non-OpenAI endpoint override) |
| model_id | `gpt-5.6-sol` |
| wire_api | `openai-chat-completions` (default, no override) |
| base_url | default OpenAI endpoint (no override) |
| env_key present | not applicable (no env-keyed provider config) |
| credential_present | `true` (OAuth token inside `~/.codex/auth.json`, `auth_mode=openai`) |
| requires_openai_auth | `true` (auth.json auth_mode == openai) |
| `SECRET_BEARING_CONFIG_FIELD_PRESENT` | `false` (config.toml itself has no literal secret-bearing keys; auth kept in separate `auth.json`, contents not printed) |

### Eligibility check (per Decision §10B)

| Condition | Outcome |
|-----------|---------|
| provider is not built-in official OpenAI | FAIL — provider is built-in OpenAI |
| profile exists before this task | FAIL — only `config.toml` exists |
| base URL / endpoint non-OpenAI | FAIL — default OpenAI endpoint |
| required env credential presence true | n/a |
| credential value never needs to be printed | PASS |
| provider config does not need modification | PASS |

Two of the three mandatory conditions fail, and the task explicitly forbids invoking the official OpenAI provider.

### Classification

- `CODEX_CUSTOM_PROVIDER = NOT_CONFIGURED`
- Reason: host only exposes the built-in official OpenAI provider path. No custom non-OpenAI provider profile is present. No `base_url` override. Since the task prohibits the official OpenAI provider, this candidate cannot be used.
- Fixture for Candidate A was **not executed** — classification is determined at configuration/eligibility time, before any model call.

## 5. Candidate B — OPENHANDS_CLI

### Presence

- `where.exe openhands` -> file-not-found (not on PATH)
- `import openhands` -> `ModuleNotFoundError` (Python package not installed)

### Classification

- `OPENHANDS_CLI = NOT_CONFIGURED`
- Reason: neither the `openhands` executable nor the Python package is installed on this host. Task forbids installation.

### Fixture

Not executed (no installed CLI to run).

## 6. Disposable fixtures prepared (no candidate ran inside them)

Per the allowed path `F:/reverse-agent-labs/issue130-real-executor/**`, prepared:

- `F:/reverse-agent-labs/issue130-real-executor/codex-custom/input.txt` = `alpha` (5 bytes, UTF-8, no trailing newline)
- `F:/reverse-agent-labs/issue130-real-executor/openhands/input.txt` = `alpha` (5 bytes, UTF-8, no trailing newline)

No `output.txt` was created by any candidate (no candidate ran).

## 7. Fixture task evidence

| Field | Value |
|-------|-------|
| input_read | `false` (no live session) |
| tool_used | `false` (no live session) |
| output_created | `false` |
| output_exact_match == `alpha-ok` | `false` |
| verification_executed | `false` |
| candidate_exit_status | n/a |
| credential_exposure | `false` |

## 8. Selection rule application

- Codex custom provider did not PASS → proceed to OpenHands.
- OpenHands did not PASS → selection rule falls through to `FALSE`.

```text
REAL_SINGLE_AGENT_EXECUTOR_PATH_ESTABLISHED = FALSE
SELECTED_EXECUTOR_PATH = null
terminal classification = ISSUE130_NEEDS_ONE_PRECONFIGURED_REAL_EXECUTOR
```

## 9. Does NOT imply #126 complete

This result does not touch #126 architecture questions (OpenAI control, heterogeneous providers, native MultiAgent). `ISSUE126_ARCHITECTURE_DECISION = INCONCLUSIVE` remains unchanged.

## 10. Repository integrity

`git diff --check 5cde8764..HEAD` -> exit 0 (clean).

Changed repository paths (all within the Decision's `allowed_mutated_paths`):

```text
project_state/gates/bootstrap_state.json
project_state/gates/command_plan.json
project_state/gates/startup_snapshot.json
project_state/gates/transition_command_plan_preview.json
project_state/gates/transition_preflight_result.json
docs/research/real-executor-spike-2026-08-07.md
docs/research/real-executor-spike-2026-08-07.json
```

Product delta: **ZERO**.
Forbidden paths mutated: none.
`reverse_agent/**`, `frontend/**`, `tests/**`, `.github/**`, dependency files, provider config files, credential files, `project_state/mainline_merge_intents/**` — all untouched.

## 11. Local HEAD vs remote HEAD (pre-push snapshot)

- Local HEAD: `234ad0dbd3134a64e49a70d028aa700ae2981d71`
- Remote HEAD (`origin/owner/issue130-real-executor-spike-v1`): `5cde87646228895c0b604311dd61a5ff1e164587` (the Decision commit; local is ahead by 1 gate commit, to be pushed)
- `origin/main`: `e4e23028c6c78c4ab9a8e032677e71370ace7627`
- Merge-base local/origin-main: `e4e23028c6c78c4ab9a8e032677e71370ace7627`

## 12. Development / verification Agent model used

The verification Agent driving this round is the opencode/sensenova-lite session (not a Codex or OpenHands session). It did not attempt any model inference as an executor candidate.

## 13. Recommendation for #127

Before #127 can proceed on a real single-Agent executor path, provision one of:

1. a Codex custom non-OpenAI provider profile already authorized in `~/.codex/<profile>.config.toml` with env-keyed credential present and a non-OpenAI `base_url`, or
2. an installed `openhands` CLI with a non-OpenAI provider preconfigured.

Then re-run this spike (Issue 130 v2 or a re-entrant round) to produce a real `read -> shell -> edit -> deterministic verify` trace.
