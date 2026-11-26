# OllyDbg Backend Setup Contract

This document defines the user-facing environment setup required for the OllyDbg single-step debugging backend used by `reverse-agent`. The backend enables bounded runtime observation of compare-window handoff paths via OllyDbg's single-step (`step_into`) capability.

## Prerequisites

1. **OllyDbg 1.10** (or compatible) installed on the local machine
2. **OllyDbg Python scripting bridge** (`olly.ollyscript` module or equivalent) installed in the Python environment used by `reverse-agent`
3. **Target sample binary** (`samplereverse.exe` or equivalent) accessible on disk

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `REVERSE_AGENT_OLLYDBG_PATH` | Yes | Absolute path to `ollydbg.exe` |
| `REVERSE_AGENT_SAMPLE_PATH` | Yes | Absolute path to the target sample binary |

### `REVERSE_AGENT_OLLYDBG_PATH`

Must point to the OllyDbg executable file. Examples:

```
# Windows (typical)
REVERSE_AGENT_OLLYDBG_PATH=C:\Tools\OllyDbg\ollydbg.exe

# Windows (Program Files)
REVERSE_AGENT_OLLYDBG_PATH=C:\Program Files\OllyDbg\ollydbg.exe
```

If not set, the preflight checks these common locations automatically:
- `C:\Program Files\OllyDbg\ollydbg.exe`
- `C:\Program Files (x86)\OllyDbg\ollydbg.exe`
- `C:\Tools\OllyDbg\ollydbg.exe`
- `%USERPROFILE%\Tools\OllyDbg\ollydbg.exe`

### `REVERSE_AGENT_SAMPLE_PATH`

Must point to the target sample binary. Example:

```
REVERSE_AGENT_SAMPLE_PATH=F:\reverse-agent\samples\samplereverse.exe
```

If not set, the preflight checks `samples/samplereverse.exe` relative to the repository root.

## OllyDbg Python Module

The preflight checks for the `olly.ollyscript` Python module (and alternative names `ollyscript`, `OllyScript`, `olly`). This module provides the Python-to-OllyDbg scripting bridge.

If this module is not installed, the preflight will report `olly_script_module_importable: false` and the backend will not be considered ready.

## Running the Preflight

After configuring the environment variables, run the preflight check:

```bash
python -m reverse_agent.ollydbg_preflight --out project_state/ollydbg_preflight_result.json
```

Validate the output JSON:

```bash
python -m json.tool project_state/ollydbg_preflight_result.json
```

## Interpreting Preflight Results

The preflight output contains three readiness flags:

| Flag | Meaning |
|------|---------|
| `backend_ready` | OllyDbg executable found AND Python module importable AND scripts directory exists AND step audit script exists |
| `runtime_ready` | `backend_ready` AND sample path resolvable |
| `ready` | Alias for `runtime_ready` — the overall readiness for bounded runtime probing |

### Readiness Matrix

| `backend_ready` | `sample_path_resolvable` | `runtime_ready` | `ready` | Interpretation |
|:-:|:-:|:-:|:-:|---------|
| false | — | false | false | OllyDbg tooling not configured |
| true | false | false | false | OllyDbg configured but sample missing |
| true | true | true | true | Fully ready for bounded runtime probing |

### Recommendation Categories

| Recommendation | Meaning |
|----------------|---------|
| `preflight_ready_for_bounded_ollydbg_runtime_decision` | Environment fully configured; a future decision can authorize bounded runtime probing |
| `preflight_not_configured_user_env_needed` | Environment not configured; user must set up variables and/or install tooling before runtime probing is allowed |

## Existing Script Infrastructure

The following OllyDbg scripts are already present in the repository:

| Script | Location | Purpose |
|--------|----------|---------|
| `compare_handoff_post_entry_step_audit.py` | `reverse_agent/olly_scripts/` | Single-step audit inside the handoff helper |
| `compare_handoff_narrower_post_entry_breakpoint_audit.py` | `reverse_agent/olly_scripts/` | Breakpoint-based audit (fallback when single-step unavailable) |

These scripts are called by `reverse_agent/strategies/compare_aware_search.py` and do not need to be modified.

## When Is Runtime Probing Allowed?

A future bounded runtime probe decision (e.g., single-step inside the `0x401b50` handoff helper) is only allowed when:

1. The preflight reports `ready: true` (equivalently `runtime_ready: true`), **OR**
2. A manual blocker is explicitly accepted in a decision packet (acknowledging that the environment is not configured but proceeding anyway)

If the preflight reports `ready: false` with recommendation `preflight_not_configured_user_env_needed`, the correct next step is to configure the environment and rerun the preflight — not to attempt runtime probing.

## Example: Full Setup Workflow

```bash
# 1. Set environment variables (Windows PowerShell)
$env:REVERSE_AGENT_OLLYDBG_PATH = "C:\Tools\OllyDbg\ollydbg.exe"
$env:REVERSE_AGENT_SAMPLE_PATH = "F:\reverse-agent\samples\samplereverse.exe"

# 2. Run preflight
python -m reverse_agent.ollydbg_preflight --out project_state/ollydbg_preflight_result.json

# 3. Check result
python -m json.tool project_state/ollydbg_preflight_result.json

# 4. If ready=true, a future decision can authorize bounded runtime probing
```
