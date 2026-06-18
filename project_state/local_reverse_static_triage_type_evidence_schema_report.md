# Local Reverse Static Triage Type Evidence Schema Report

Decision: `decision_20260619_static_triage_type_evidence_schema_v1`
Round: `round_20260619_static_triage_type_evidence_schema_v1`
Generated: `2026-06-19T00:00:00Z`

## Scope

This round extends the existing single-sample static triage adapter. It does not add a new IDA, Ghidra, debugger, emulator, solver, harness, sidecar, GUI, or runtime interface.

No sample, IDA, Ghidra, debugger, runtime probe, solver, harness, or GUI workflow was executed. The new tests use synthetic dictionaries only.

## Adapter Change

`reverse_agent/local_reverse_single_sample_static_triage.py` now normalizes type evidence into `triage.type_evidence`.

The helper is pure and consumes already-collected IDA evidence plus parsed triage fields. It does not run external tools. Success artifacts include the normalized field, and blocked artifacts include the same field with default `not_observed` profiles so downstream consumers can rely on the schema.

## Schema Fields

`triage.type_evidence` contains:

- `schema_version`
- `source`
- `status_vocabulary`
- `type_tag_observations`
- `profiles`
- `promotion_safety`

Profiles are stable for:

- `string_comparison`
- `xor`
- `shift_affine`
- `bit_operations`
- `lookup_table`
- `rc4`
- `des`
- `hash_md5_sha`
- `simple_antidebug`
- `mixed_unknown`

## Status Vocabulary

Allowed profile statuses:

- `not_observed`
- `candidate_static_signal`
- `observed_static_signal`
- `blocked_missing_required_evidence`

The helper never emits `static_verified`, `runtime_validated`, or `solved`.

## Special Policies

- Hash evidence always carries `bounded_domain_required=true`.
- Hash profiles remain `solver_ready=false`; hash constants alone are blocked if no length, charset, or format evidence exists.
- Lookup-table evidence records table access, base, size, and contents separately, including explicit missing states.
- Anti-debug evidence records static API/SEH signal only and does not authorize debugger execution.
- Keyword, filename, sample id, category, solver module name, and queue membership are not enough for static verification.

## Unsupported In This Round

- No real sample static triage was run.
- No IDA/Ghidra output was collected.
- No inventory, training status, coverage matrix, solver, harness, GUI, project gate, or `.codex-skills` logic was modified.
- `reverse_agent/ida_scripts/collect_evidence.py` was inspected but not changed because the adapter can consume existing fields.

## Test Coverage

`tests/test_local_reverse_static_triage_type_evidence_schema.py` covers synthetic paths for:

- compare context -> `string_comparison`
- XOR/decompiler text -> `xor` and `bit_operations`
- shift/affine text -> `shift_affine`
- lookup table access without base/size/contents -> blocked missing evidence
- RC4 KSA/PRGA/S-box/key text -> `rc4`
- DES S-box/permutation/key schedule text -> `des`
- hash constants without bounded domain -> blocked missing evidence
- hash constants with length/charset/format evidence -> bounded-domain evidence present while still not static verified
- anti-debug API/SEH text -> `simple_antidebug`
- blocked artifact -> default empty `type_evidence`
