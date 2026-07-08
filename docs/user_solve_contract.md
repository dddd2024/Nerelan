# User Solve Contract

## Purpose

This document defines the user-facing solve result contract and explains the boundary between the **user layer** (what users see) and the **engineering evidence layer** (internal governance files).

This is a contract/schema foundation round. It does not implement solving, Web runtime, tool invocation, or sample execution.

## Schema Version

Current schema version: `1` (defined in `CONTRACT_SCHEMA_VERSION`).

All JSON payloads include a `schema_version` field. Unknown optional fields are ignored for forward compatibility. Missing optional fields default to their dataclass defaults for backward compatibility.

## Core Types

### UserSolveTask

Represents a user-submitted solve task.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_id` | `str` | Yes | Unique task identifier |
| `sample_label` | `str` | No | Human-readable sample label |
| `mode` | `UserSolveMode` | No | `fast`, `deep`, or `auto` (default: `auto`) |
| `requested_validation` | `ValidationStatus` | No | User-requested validation level (default: `pending`) |
| `user_context` | `dict` | No | Arbitrary user-provided context |

### UserSolveResult

Represents the result of a solve attempt.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | `UserSolveStatus` | Yes | User-facing solve status |
| `validation_status` | `ValidationStatus` | No | Validation level achieved |
| `evidence_status` | `EvidenceStatus` | No | Evidence completeness |
| `mode` | `UserSolveMode` | No | Solve mode used |
| `answer` | `str` | No | Final answer (if available) |
| `candidates` | `list[UserSolveCandidate]` | No | Candidate results |
| `confidence` | `float` | No | Confidence score (0.0–1.0) |
| `message` | `str` | No | User-readable message |
| `reason` | `str` | No | Reason for failed/blocked states |
| `developer_trace_ref` | `str` | No | Internal trace reference (developer only) |
| `internal_references` | `list[str]` | No | Internal evidence references (developer only) |

### CandidateResult

Represents a candidate answer without implying runtime validation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `value` | `str` | Yes | Candidate value |
| `confidence` | `float` | No | Confidence score (0.0–1.0) |
| `label` | `str` | No | Human-readable label |
| `validation_status` | `ValidationStatus` | No | Default: `candidate_only` |
| `evidence_refs` | `list[str]` | No | Evidence references (developer only) |
| `developer_trace_ref` | `str` | No | Internal trace reference (developer only) |

**Safety:** `CandidateResult` rejects `validation_status=runtime_validated` at construction time.

## Status Enums

### UserSolveStatus

User-facing solve lifecycle states:

| Status | Description |
|--------|-------------|
| `uploaded` | Sample uploaded, analysis not started |
| `fast_analyzing` | Fast analysis in progress |
| `candidate_found` | At least one candidate found |
| `static_verified` | Candidate verified via static analysis |
| `runtime_validation_pending` | Waiting for runtime validation |
| `runtime_validated` | Candidate verified via runtime validation |
| `validating` | (Legacy) Validation in progress |
| `verified` | (Legacy) General verified state |
| `deep_analysis_running` | Deep analysis in progress |
| `failed` | Solve failed (requires reason) |
| `blocked` | Solve blocked (requires reason) |

### ValidationStatus

Validation levels:

| Status | Description |
|--------|-------------|
| `not_started` | Validation not started |
| `pending` | Validation pending |
| `candidate_only` | Candidate found, no validation |
| `static_verified` | Static analysis verification |
| `runtime_validated` | Runtime validation completed |
| `passed` | (Legacy) General pass |
| `failed` | Validation failed |
| `blocked` | Validation blocked |
| `unsupported` | Validation unsupported |
| `unavailable` | (Legacy) Validation unavailable |

## Safety Semantics

```text
candidate_found != verified
static_verified != runtime_validated
runtime_validated requires runtime validation evidence
failed requires a reason
blocked requires a reason (policy/tool/environment/sample_format/unsupported)
user-layer result does not equal engineering-layer ACCEPTED
```

## State Transitions

Allowed transitions (see `ALLOWED_TRANSITIONS` in `user_solve_state.py`):

```text
uploaded → fast_analyzing, deep_analysis_running, blocked, failed
fast_analyzing → candidate_found, deep_analysis_running, blocked, failed
candidate_found → static_verified, runtime_validation_pending, validating, verified, deep_analysis_running, blocked, failed
static_verified → runtime_validation_pending, validating, verified, deep_analysis_running, blocked, failed
runtime_validation_pending → runtime_validated, static_verified, verified, deep_analysis_running, blocked, failed
runtime_validated → verified, blocked, failed
validating → verified, static_verified, runtime_validated, deep_analysis_running, blocked, failed
deep_analysis_running → candidate_found, static_verified, runtime_validation_pending, validating, blocked, failed
verified → (terminal)
failed → (terminal)
blocked → (terminal)
```

Evidence-requiring states (`static_verified`, `runtime_validated`, `verified`) require `evidence_refs` or a message with evidence when transitioning.

## Failed/Blocked Reason Codes

### BlockedReason

| Code | Retryable | Description |
|------|----------|-------------|
| `policy` | No | Blocked by policy |
| `tool` | Yes | Required tool unavailable |
| `environment` | Yes | Environment requirements not met |
| `sample_format` | No | Sample format not supported |
| `unsupported` | No | Operation not supported |

### FailedReason

| Code | Retryable | Description |
|------|----------|-------------|
| `policy` | No | Policy violation |
| `tool` | Yes | Tool error |
| `environment` | Yes | Environment error |
| `sample_format` | No | Invalid sample format |
| `unsupported` | No | Unsupported operation |
| `analysis` | No | Analysis failure |
| `validation` | No | Validation failure |

## User Layer vs Engineering Evidence Layer

### User Layer (public)

- Contains only user-visible fields: `status`, `validation_status`, `candidates`, `message`, `reason`, `confidence`
- Internal governance file references are redacted to `[internal]`
- Accessible via `to_user_dict()` and `to_json()`

### Engineering Evidence Layer (developer only)

- Contains `developer_trace_ref` and `internal_references` fields
- May reference internal governance files (`project_state/`, `decision_packet.md`, etc.)
- Accessible via `to_developer_dict()`
- Never exposed in user-facing payloads

### Internal Reference Tokens

The following tokens are automatically redacted in user-facing payloads:

```text
project_state/
decision_packet.md
command_plan.json
artifact_index.json
negative_results.json
codex_execution_report.md
pytest_result.txt
```

## JSON Serialization

All payloads include `schema_version=1`. Use `to_json()` / `from_json()` for schema-versioned serialization:

```python
result = UserSolveResult(status="candidate_found", ...)
data = result.to_json()
# {"schema_version": 1, "payload": {...}}
restored = UserSolveResult.from_json(data)
```

Unknown optional fields are ignored for forward compatibility. Missing optional fields use dataclass defaults for backward compatibility.
