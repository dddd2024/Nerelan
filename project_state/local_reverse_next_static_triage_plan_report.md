# Local Reverse Next Static Triage Plan Report

Decision: `decision_20260620_training_capability_gap_matrix_v1`
Round: `round_20260620_training_capability_gap_matrix_v1`
Generated: 2026-06-20

## Scope

This report explains the selected bounded batch for the next static triage plan and what the next `tool_integration` or `training_dataset` decision should authorize. It is a planning artifact only. This round did not execute samples, solvers, IDA, Ghidra, debuggers, emulators, runtime probes, sidecars, GUI workflows, or a full `solve_reports/` scan.

No `reverse_agent/` source files or `.codex-skills/` files were modified.

## Selected Bounded Batch

Three items are selected for the next evidence-producing round, following the decision's recommended priority order:

| # | Queue ID | Type | Sample ID | Priority Reason |
| --- | --- | --- | --- | --- |
| 1 | `next_static_triage_string_comparison_001` | `string_comparison` | `cpp2_fc735338` | Validate the simple static-triage path |
| 2 | `next_static_triage_rc4_001` | `rc4` | `rc4enc_a1897c10` | Exercise cipher evidence fields |
| 3 | `next_static_triage_lookup_table_planning_001` | `lookup_table` | `ascii_table_chinese_46efc7ea` | Planning row for field-support gap (not solver work) |

## Item 1: string_comparison - cpp2_fc735338

**Why selected**: First inventory_only cpp representative in the current string_comparison coverage row. The string_comparison type has 35 samples, 1 solved (`cpp1_bcbd9979`), and 1 needs_triage (`cpp1_2f6fcb63`) with `static_triage_completed` evidence. This sample can validate the simple static-triage path for string comparison.

**Required static evidence**:
- Identify compare function or inline compare that gates success/failure branch.
- Record compare callsite address and operand source from static analysis.
- Identify compared value or producer function from static decompilation or string extraction.

**Existing route to attempt first**: `reverse_agent.local_reverse_single_sample_static_triage` with IDA collect_evidence, then `reverse_agent.local_reverse_string_solver` or `reverse_agent.local_reverse_direct_strcmp_handoff` after compare callsite is identified.

**Expected output artifacts**:
- `project_state/local_reverse_cpp2_fc735338_static_triage.json`
- `project_state/local_reverse_cpp2_fc735338_static_triage_report.md`

**Forbidden actions**: runtime_probe, sample_runner, debugger, harness, blind_bruteforce, claim_static_verified from cpp filename or category.

**Stop condition**: Keep metadata_only if static triage does not identify a concrete compare gate. Do not promote from filename, category, or solver module name alone.

## Item 2: rc4 - rc4enc_a1897c10

**Why selected**: First PE rc4enc target after solver-support scripts in the current RC4 coverage row. RC4 has 8 samples, 0 solved. `RC4MaterialEvidence` module exists. This sample exercises cipher evidence fields (KSA/PRGA loop, S-box, key material). No static triage has been run on RC4 targets yet.

**Required static evidence**:
- Identify RC4 KSA (key scheduling) or PRGA (pseudo-random generation) loop structure.
- Identify RC4 S-box (256-byte state array) initialization from static analysis.
- Identify RC4 key material or key derivation from static decompilation or string extraction.

**Existing route to attempt first**: `reverse_agent.local_reverse_single_sample_static_triage` with IDA collect_evidence, then `reverse_agent.evidence.RC4MaterialEvidence` and `reverse_agent.local_reverse_solver_profiles` with RC4 profile after KSA/PRGA and key material are identified.

**Expected output artifacts**:
- `project_state/local_reverse_rc4enc_a1897c10_static_cipher_profile.json`
- `project_state/local_reverse_rc4enc_a1897c10_static_cipher_profile_report.md`

**Forbidden actions**: runtime_probe, sample_runner, debugger, harness, blind_key_search, claim_static_verified from rc4 filename.

**Stop condition**: Keep metadata_level_unverified if RC4 structure or key source is not statically identified. Do not promote from filename containing 'rc4' alone.

## Item 3: lookup_table - ascii_table_chinese_46efc7ea (Planning Row Only)

**Why selected**: Planning row only, not solver work. `lookup_table` has `tool_evidence_available=false` per coverage matrix. Static triage output lacks lookup-table extraction fields. This item records the field-support gap and must not be promoted without adding table detection fields to static triage output first. `ascii_table_chinese_46efc7ea` is a PDF, not a PE target; a concrete PE target with table access must be identified in a later round.

**Required static evidence**:
- Add lookup-table detection fields to static triage output (tool_integration round required first).
- Identify a concrete PE target sample with table access or array indexing operation.
- Identify table base address and size from static analysis.
- Extract or verify table contents from static analysis.

**Existing route to attempt first**: No existing route is ready until lookup-table detection fields are added to static triage output. `reverse_agent.local_reverse_single_sample_static_triage` and `reverse_agent.tool_runners` (IDA collect_evidence) exist but lack table extraction fields.

**Expected output artifacts**:
- `project_state/local_reverse_lookup_table_field_support_plan.json`
- `project_state/local_reverse_lookup_table_field_support_plan_report.md`

**Forbidden actions**: runtime_probe, sample_runner, debugger, harness, blind_bruteforce, claim_static_verified from table/array filename, claim_tool_ready when tool_evidence_available is false, solver_work before field support is added.

**Stop condition**: Remain `blocked_missing_evidence_fields` until lookup-table detection fields are added to static triage output and a concrete PE target with table access is identified. This is a planning row only, not solver work.

## Items Not Selected and Why

| Type | Reason |
| --- | --- |
| `shift_affine` | `affine_8cfebe03` already has current static triage evidence per `artifact_index.json`. A later round can select `affineenc_333f8ca9` for additional affine/shift static triage if needed. |
| `des` | DES is a valid cipher candidate but RC4 was selected to exercise cipher evidence fields first. DES can be selected in a subsequent round. |
| `hash_md5_sha` | Blocked by `NO_BOUNDED_HASH_PREIMAGE_DOMAIN`. Cannot be selected for static triage until bounded input domain evidence is recovered. |
| `simple_antidebug` | Valid candidate but lower priority than string comparison and cipher types for the next round. |
| `mixed_unknown` | Valid candidate but requires static triage first to identify the actual transform type. |
| `xor` | `metadata_only`: No concrete PE target sample with XOR transform evidence exists. |
| `tea_xtea` | `blocked_missing_sample`: No current sample exists. |
| `base64` | `blocked_missing_sample`: No current sample exists. |
| `gui_validation` | `blocked_missing_sample`: No current sample exists. |

## What the Next Decision Should Authorize

The next `tool_integration` or `training_dataset` decision should authorize:

1. **For Item 1 (string_comparison)**: A bounded static triage round using `reverse_agent.local_reverse_single_sample_static_triage` with IDA collect_evidence on `cpp2_fc735338`. The decision must explicitly authorize IDA execution for this single sample and specify the expected output artifacts. The decision should prohibit runtime probes, debuggers, harnesses, and blind bruteforce.

2. **For Item 2 (rc4)**: A bounded static cipher profile round using `reverse_agent.local_reverse_single_sample_static_triage` with IDA collect_evidence on `rc4enc_a1897c10`. The decision must explicitly authorize IDA execution for this single sample and specify the expected cipher profile artifacts. The decision should prohibit runtime probes, debuggers, harnesses, and blind key search.

3. **For Item 3 (lookup_table)**: A `tool_integration` round to add lookup-table detection fields to static triage output. This is a source modification round, not a sample execution round. The decision must explicitly authorize modifying `reverse_agent/local_reverse_single_sample_static_triage.py` or related tool runner code to add table extraction fields. No sample execution is authorized.

## Non-Promotion Safeguard

This plan is a metadata-only planning artifact. It did not execute samples, solvers, IDA, Ghidra, debuggers, emulators, runtime probes, harnesses, or GUI workflows. No sample is marked as solved, static_verified, or runtime_validated. All selected items remain metadata_only until a later explicitly authorized round produces static triage evidence.

## Limitations

- This plan is a planning artifact, not a solver result or static triage evidence.
- All selected items remain metadata_only until a later explicitly authorized round produces static triage evidence.
- The lookup_table item is a planning row only; field support must be added before any static triage or solver work.
- Selection is justified by current metadata only; it does not prove that selected samples are verified targets of their type.
