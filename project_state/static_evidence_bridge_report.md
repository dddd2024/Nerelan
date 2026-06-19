# Static Evidence Bridge Report

## Decision

Decision `decision_20260619_generic_static_evidence_bridge_v1` (round `round_20260619_generic_static_evidence_bridge_v1`) on mainline `tool_integration`.

## Summary

A generic static evidence bridge has been built that converts dict-like static tool artifacts (IDA/Ghidra/strings/objdump/static triage JSON) into `StructuredEvidence` records plus a `SolverDispatchPlan`. Detection is rule-based on artifact content and never branches on `sample_id`.

## Bridge Capability Audit

### Tool artifact schemas supported

- Static triage JSON (`triage.input_apis`, `triage.interesting_strings`, `triage.functions`, `triage.compare_contexts`, `triage.solver_hints`, `triage.decompiler_snippets`)
- Static evidence summary JSON (`evidence_summary.key_strings`, `evidence_summary.compare_contexts`)
- Cipher static profile JSON (`constants`, `constant_tables`)
- Generic dict with `functions`/`strings`/`compare_contexts`/`input_apis` keys

### Evidence families normalized

- `StaticInputEvidence` (input APIs: scanf, gets, fgets, ReadFile, GetDlgItemTextA/W, __input; prompt strings)
- `StaticCompareEvidence` (compare APIs: strcmp, strncmp, memcmp, CompareStringA; callsites)
- `StaticConstantEvidence` (constants, tables)
- `StaticTransformHintEvidence` (xor, affine, shift, lookup; loop evidence; arithmetic/bitwise ops)
- `StaticCryptoSignatureEvidence` (rc4, des, aes, md5, sha markers)
- `StaticGuiInputEvidence` (GUI APIs, dialog strings)
- `StaticAntiDebugEvidence` (IsDebuggerPresent, DebugBreak, etc.)

### Solver profile hints emitted

`string_compare`, `xor`, `affine_shift`, `lookup_table`, `rc4`, `des`, `aes`, `hash`, `gui_check`, `anti_debug_precondition`

### Insufficient evidence detection

- Missing `input_source_evidence` when no input/gui evidence
- Missing `comparison_sink_evidence` when no compare evidence
- Missing `key_or_constant_evidence` when crypto signature without constants
- Missing `transform_constant_evidence` when transform hint without constants

### Readiness states

- `not_solve_ready`
- `needs_current_static_provenance` (default for static-only evidence)
- `solver_profile_hint_only` (strongest; only with full evidence + current provenance)

## Acceptance Cases

1. Synthetic triage with `__input` + `_strncmp` + compare context returns input and compare evidence and recommends `string_compare` profile. (PASS)
2. Synthetic xor/arithmetic loop returns transform hint and recommends `xor` profile; remains not solve-ready without constants. (PASS)
3. Synthetic RC4-like artifact returns crypto signature evidence and recommends `rc4` profile as hint only. (PASS)
4. Historical `affine_8cfebe03` fixture parses into evidence + dispatch plan; readiness is `needs_current_static_provenance`. (PASS)
5. No test executes a binary or launches IDA/Ghidra/debugger. (PASS)

## Safety Scope

This round changed only the static evidence bridge, solver dispatch plan, evidence model extensions, their tests, and project_state report artifacts. It did not run samples, solvers, harnesses, IDA, Ghidra, debuggers, runtime probes, GUI workflows, or full `solve_reports`/progress-log reads.
