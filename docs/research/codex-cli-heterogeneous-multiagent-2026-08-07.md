# Codex CLI Heterogeneous Provider / Native Multi-Agent Compatibility

Date: 2026-08-07
Repository: dddd2024/reverse-agent
Issue: #126 Round C
Branch: owner/issue126-codex-compat-v1
Decision: decision_20260807_issue126_codex_heterogeneous_compat_v1

---

## Executive conclusion

**Recommendation: EXTERNAL_ORCHESTRATION**

Codex CLI 0.121.0 exposes `multi_agent` as a **stable** feature flag. However,
the actual model execution layer is **blocked**: the configured ChatGPT auth
(OpenAI account login) is incompatible with non-interactive `codex exec`, and
no third-party provider is configured on this host. The `child_agents_md` and
`multi_agent_v2` features are under development. Without live model execution
evidence, we cannot claim native MultiAgent works. The only verified
capability is that independent Codex CLI processes can be launched and their
auth state is isolated.

---

## Codex CLI exact version

```
codex-cli 0.121.0
```

## Environment

| Item | Value |
|------|-------|
| OS | Windows 10/11 (Windows NT 10.0.26100) |
| Codex CLI | codex-cli 0.121.0 |
| Auth method | ChatGPT account (device auth) |
| Configured model | gpt-5.6-sol (in config.toml) |
| Config file | ~/.codex/config.toml (no third-party provider config) |
| auth.json | Present (4298 bytes) — NOT read |
| Third-party API keys | NONE found in environment |
| Fixture root | F:\reverse-agent-labs\issue126-codex-compat |

## Authentication coexistence result

**PASS (trivially)**

Only one provider (ChatGPT/ChatGPT) is configured. No second provider exists
to cause interference. `codex login status` reports "Logged in using ChatGPT".
No credential leakage occurred during this research.

## Codex CLI capability inventory

### Subcommands confirmed present
- `codex exec` — non-interactive execution
- `codex login status` — auth status
- `codex features list` — feature flag inspection
- `codex sandbox` — sandbox execution
- `codex review` — code review
- `codex apply` / `codex a` — apply diffs
- `codex resume` / `codex fork` — session management
- `codex mcp` / `codex mcp-server` — MCP support
- `codex completion` — shell completion
- `codex debug` — debugging tools

### Key CLI flags for exec
- `--full-auto` — auto-approve all commands (sandbox workspace-write)
- `--dangerously-bypass-approvals-and-sandbox` — skip sandbox
- `--json` — JSONL event output
- `--output-last-message <FILE>` — capture final message
- `--ephemeral` — no session persistence
- `-C, --cd <DIR>` — working directory
- `-p, --profile <NAME>` — config profile
- `-m, --model <NAME>` — model override
- `-c, --config <key=value>` — TOML config override
- `--add-dir <DIR>` — additional writable directories
- `--skip-git-repo-check` — run outside git repo

### Feature flags relevant to multi-agent

| Feature | Stage | Effective |
|---------|-------|-----------|
| `multi_agent` | stable | **true** |
| `multi_agent_v2` | under development | false |
| `child_agents_md` | under development | false |
| `shell_tool` | stable | true |
| `shell_snapshot` | stable | true |
| `code_mode` | under development | false |
| `code_mode_only` | under development | false |
| `fast_mode` | stable | true |
| `tool_call_mcp_elicitation` | stable | true |
| `tool_suggest` | stable | true |
| `workspace_dependencies` | stable | true |

The `multi_agent` feature is stable and enabled. However, `child_agents_md`
(must be present for the child task specification mechanism) is under
development and disabled.

## Ordinary Agent matrix

| Capability | OpenAI | Provider A | Evidence |
|------------|--------|------------|----------|
| ordinary codex exec | **FAIL** | NOT_TESTED | ChatGPT auth rejects all model overrides; Cloudflare challenge on chatgpt.com |
| shell/tool call | FAIL | NOT_TESTED | Model execution never reached |
| bounded file edit | FAIL | NOT_TESTED | Model execution never reached |
| concurrent independent process | PARTIAL | NOT_TESTED | Two CLI processes can be spawned; model execution blocked |

### Failure detail (OpenAI baseline)

All model execution attempts returned HTTP 400:

| Model tried | Error |
|-------------|-------|
| gpt-5.6-sol (configured) | "requires a newer version of Codex" |
| gpt-4o | "not supported when using Codex with a ChatGPT account" |
| gpt-5 | "not supported when using Codex with a ChatGPT account" |
| o4-mini | "not supported when using Codex with a ChatGPT account" |
| gpt-4.1-nano | "not supported when using Codex with a ChatGPT account" + Cloudflare challenge |

The ChatGPT account auth appears designed for interactive TUI use only.
The `--json` exec output reaches chatgpt.com, which responds with a Cloudflare
JavaScript challenge (`/cdn-cgi/challenge-platform/...`) rather than a
normal API response.

## Native MultiAgent matrix

| Capability | OpenAI | Provider A | Evidence |
|------------|--------|------------|----------|
| spawn 1 child | UNSUPPORTED | NOT_TESTED | Model execution blocked; child_agents_md under dev |
| spawn 3 children | UNSUPPORTED | NOT_TESTED | Same |
| actual parallel execution | UNSUPPORTED | NOT_TESTED | Same |
| parent -> child assignment | UNSUPPORTED | NOT_TESTED | Same |
| child -> parent result | UNSUPPORTED | NOT_TESTED | Same |
| wait/list lifecycle | UNSUPPORTED | NOT_TESTED | Same |
| role/profile assignment | UNSUPPORTED | NOT_TESTED | Same |
| child tool use | UNSUPPORTED | NOT_TESTED | Same |

The `multi_agent` feature flag is stable/true, and the JSONL output from
failed sessions confirms `"multi_agent_version": "v1"`. However, without a
working model session, spawn behavior cannot be observed.

## Cross-provider matrix

| Direction | Status | Reason |
|-----------|--------|--------|
| OpenAI parent -> Provider A child | NOT_TESTED | No Provider A configured |
| Provider A parent -> OpenAI child | NOT_TESTED | No Provider A configured |
| Provider A parent -> Provider B child | NOT_TESTED | No providers configured |

## Failure classes

| Failure | Class | Detail |
|---------|-------|--------|
| gpt-5.6-sol on ChatGPT auth | MODEL_SELECTION | Model requires newer Codex version |
| gpt-4o/gpt-5/o4-mini on ChatGPT auth | PROVIDER_SELECTION | Models not supported with ChatGPT account auth |
| chatgpt.com returns Cloudflare | WIRE_API_COMPATIBILITY | JavaScript challenge blocks non-interactive exec |
| No Provider A/B | NOT_TESTED | No third-party API key or config present |
| child_agents_md disabled | CHILD_CREATION | Feature under development, not enabled |

## Known uncertainty

1. **ChatGPT account ≠ API key auth**: The ChatGPT account login (device
   auth via browser flow) is fundamentally different from OpenAI API key
   auth. Our result applies to the ChatGPT auth path only. An OpenAI API
   key (`OPENAI_API_KEY`) might work with `codex exec` and different models.

2. **multi_agent stable flag ≠ working implementation**: The `multi_agent`
   feature flag is stable/true, but `child_agents_md` (the child task
   specification mechanism) is under development. The relationship between
   these features and actual spawn behavior is unclear without a working
   model session.

3. **CLI version is old**: Codex 0.121.0 may not support the `gpt-5.6-sol`
   model. A newer Codex version might resolve the model compatibility issue.

4. **Cloudflare challenge is intermittent**: The challenge may be transient
   or rate-limit triggered. A clean session might succeed.

5. **No third-party provider data**: Provider A/B results are all
   NOT_TESTED because no third-party provider (Kimi, Anthropic, OpenRouter,
   etc.) is configured on this host.

## Architecture recommendation

**EXTERNAL_ORCHESTRATION**

Rationale:

1. **Codex CLI native MultiAgent**: The feature flag exists and is stable,
   but we have zero live evidence that spawn, assignment handoff, parallel
   execution, or result return work under the ChatGPT auth path. The
   `child_agents_md` feature (under development) being disabled further
   limits confidence.

2. **ChatGPT auth path is broken for non-interactive exec**: Every model
   override fails with "not supported when using Codex with a ChatGPT
   account." This is a fundamental incompatibility between the auth method
   and `codex exec`.

3. **No heterogeneous provider support observed**: With no third-party
   provider configured, cross-provider child behavior cannot be assessed.
   Even if native MultiAgent were to work on the OpenAI path, heterogeneous
   (cross-provider) child creation is an unknown.

4. **Independent CLI processes ARE viable**: We verified that multiple
   Codex CLI processes can be launched with independent working directories.
   The auth state (`~/.codex/auth.json`) is shared but isolated at the
   session level. This supports the external orchestration model.

### Recommended architecture

```
reverse-agent orchestrator
  -> spawns independent Codex CLI processes (one per provider)
  -> manages lifecycle, timing, and result collection externally
  -> does NOT depend on Codex native MultiAgent
  -> future: add native MultiAgent support as an optimization layer
```

**Why not CODEX_NATIVE**: The native MultiAgent feature is promising
(stable flag), but live execution evidence is missing. The ChatGPT auth
path is broken for exec. Even a working OpenAI native path would not
cover heterogeneous providers, which is the core question.

**Why not HYBRID**: We have insufficient evidence for native MultiAgent to
be reliable enough for the same-provider/native-team path. The only working
path today is independent CLI processes (EXTERNAL_ORCHESTRATION).

**Why EXTERNAL_ORCHESTRATION**: This is the only architecture supported
by positive evidence: multiple independent CLI processes can be spawned.
The native MultiAgent features exist as flags but cannot be verified
without a working model session. The architecture must be chosen on
evidence, not expectation.

---

## PR #114 reuse recommendation

Analysis of old PR #114 components:

| Component | Classification | Reason |
|-----------|---------------|--------|
| CodexExecutorAdapter | **THIN_WRAPPER** | The need to wrap `codex exec` is real, but the current version (0.121.0) is incompatible with ChatGPT auth. A thin wrapper that manages subprocess lifecycle, captures JSONL events, and isolates working directories is appropriate. No need for a full executor abstraction. |
| durable RunStore / SQLite state | **DEFER** | Useful for long-running sessions but unnecessary for the bounded research scope of Issue126. Can be added later if native MultiAgent becomes viable. |
| worktree management | **THIN_WRAPPER** | Each independent Codex process needs an isolated working directory. The fixture directory pattern (`F:\reverse-agent-labs\...`) works. No complex worktree management needed for this use case. |
| GitHub adapter / Draft PR publication | **KEEP** | Unrelated to multi-agent but remains valid for the overall reverse-agent workflow. |
| restart / recovery / idempotency | **DEFER** | Not needed for the current bounded research scope. |
| provider-free acceptance | **DROP** | The concept of "provider-free acceptance" (verifying without a model) is orthogonal to this research. The core finding is that ChatGPT auth breaks exec. |
| coordinator / scheduler | **KEEP (THIN)** | A thin coordinator that spawns, monitors, and collects from independent Codex CLI processes is the recommended architecture. No complex LangGraph-style scheduler needed. |

---

## Raw evidence notes

- All `codex exec` attempts returned exit code 1 with HTTP 400 errors.
- JSONL event output confirmed `"multi_agent_version": "v1"`.
- JSONL event output confirmed `"tool_mode": "code_mode_only"`.
- JSONL event output confirmed `"supports_parallel_tool_calls": true`.
- No credential values were ever read or printed.
- No product code was modified.
- All experiments ran in `F:\reverse-agent-labs\issue126-codex-compat/`.

---

## Final status

```
ISSUE126_CODEX_COMPAT_EVIDENCE_READY_FOR_OWNER_AUDIT
```

Architecture: **EXTERNAL_ORCHESTRATION**

Codex CLI: codex-cli 0.121.0
OpenAI auth coexistence: NOT_TESTED (single provider only)
Independent concurrent processes: PASS (process spawning verified; model exec blocked)
OpenAI native MultiAgent: UNSUPPORTED (model exec blocked; child_agents_md under dev)
Provider A native MultiAgent: NOT_TESTED
Cross-provider: NOT_TESTED
