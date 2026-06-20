# Local Reverse Training Capability Gap Matrix Report

Decision: `decision_20260620_training_capability_gap_matrix_v1`
Round: `round_20260620_training_capability_gap_matrix_v1`
Generated: 2026-06-20

## Scope

This is a metadata-only planning artifact for the local reverse training set. It did not execute samples, solvers, IDA, Ghidra, debuggers, emulators, runtime probes, sidecars, GUI workflows, or bulk `solve_reports/` scans. No sample is marked as solved, static_verified, or runtime_validated.

No `reverse_agent/` source files or `.codex-skills/` files were modified.

## Capability Gap Matrix Summary

| Type ID | Representative | Before | Current Evidence Status | Solver Ready | Blocked Reason |
| --- | --- | --- | --- | --- | --- |
| `string_comparison` | `cpp1_2f6fcb63` | `partial_validated_sample_plus_metadata_gap` | `ready_for_static_triage` | ready | - |
| `xor` | `xor_array_solver_v2_fb15e14c` | `gap_or_tool_only` | `metadata_only` | not_ready | No concrete PE target with XOR evidence |
| `shift_affine` | `affine_8cfebe03` | `metadata_level_unverified` | `ready_for_static_triage` | ready | - |
| `lookup_table` | `ascii_table_chinese_46efc7ea` | `gap_or_tool_only` | `blocked_missing_evidence_fields` | not_ready | tool_evidence_available=false; no table extraction fields |
| `rc4` | `rc4enc_a1897c10` | `metadata_level_unverified` | `ready_for_static_triage` | ready | - |
| `des` | `desenc_40cba418` | `metadata_level_unverified` | `ready_for_static_triage` | ready | - |
| `hash_md5_sha` | `sha_256_18019fca` | `metadata_level_unverified` | `blocked_bounded_domain` | not_ready | NO_BOUNDED_HASH_PREIMAGE_DOMAIN |
| `simple_antidebug` | `seh_52be8d5c` | `metadata_level_unverified` | `ready_for_static_triage` | ready | - |
| `mixed_unknown` | `samplereverse_ca74a786` | `metadata_level_unverified` | `ready_for_static_triage` | not_ready | Needs triage first to identify transform |
| `tea_xtea` | null | `gap_no_current_samples` | `blocked_missing_sample` | not_ready | No current sample exists |
| `base64` | null | `gap_no_current_samples` | `blocked_missing_sample` | not_ready | No current sample exists |
| `gui_validation` | null | `gap_no_current_samples` | `blocked_missing_sample` | not_ready | No current sample exists |

## Types Ready for a Later Static Triage Round

Seven types are `ready_for_static_triage`:

1. **string_comparison** (35 samples, 1 solved, 1 needs_triage): The most mature type. `cpp1_bcbd9979` is solved, `cpp1_2f6fcb63` has `static_triage_completed` evidence. `local_reverse_string_solver` and `local_reverse_direct_strcmp_handoff` exist and can be reused.

2. **shift_affine** (4 samples, 0 solved): `affine_8cfebe03` has current static triage evidence and transform material evidence per `artifact_index.json` (modified 2026-06-19), even though `training_status.json` still records it as `inventory_only` due to staleness. `local_reverse_affine_inverse_handoff` exists and can be reused.

3. **rc4** (8 samples, 0 solved): Multiple PE `rc4enc` targets exist. `RC4MaterialEvidence` module exists. No static triage has been run on RC4 targets yet.

4. **des** (5 samples, 0 solved): Multiple PE `desenc` targets exist. `single_sample_static_triage` and `tool_runners` exist. No static triage has been run on DES targets yet.

5. **simple_antidebug** (1 sample, 0 solved): `seh_52be8d5c` is a PE target. `olly_scripts.collect_evidence` exists but debugger execution remains forbidden until explicitly authorized. Static triage can identify anti-debug technique without running a debugger.

6. **mixed_unknown** (7 samples, 0 solved): `samplereverse_ca74a786` is a large PE (1762304 bytes). Static triage can identify or retain the unknown type. Solver readiness is not_ready because the actual transform type must be identified first.

## Types Blocked and Why

Five types are blocked:

1. **xor** (`metadata_only`): Only solver/support Python scripts expose XOR metadata (`xor_array_solver_v2_fb15e14c`, `xor_array_solver_4e6d25f0`). No concrete PE target sample with XOR transform evidence exists. Solver scripts are not target evidence.

2. **lookup_table** (`blocked_missing_evidence_fields`): `tool_evidence_available=false` per coverage matrix. Static triage output lacks lookup-table extraction fields. `ascii_table_chinese_46efc7ea` is a PDF, not a PE target. Field support must be added before claiming coverage.

3. **hash_md5_sha** (`blocked_bounded_domain`): `sha_256_18019fca` is blocked by `NO_BOUNDED_HASH_PREIMAGE_DOMAIN`. Hash constants alone are insufficient; bounded input domain evidence is required before any solver attempt. Unbounded bruteforce is forbidden.

4. **tea_xtea** (`blocked_missing_sample`): No current inventory samples with TEA/XTEA metadata. Tool capability exists but no target sample is available.

5. **base64** (`blocked_missing_sample`): No current inventory sample has Base64 metadata. `Base64MaterialEvidence` tool support exists but no target sample is available.

6. **gui_validation** (`blocked_missing_sample`): No current inventory sample has GUI-specific metadata. Console validator and pair validator tool support exists but no target sample is available.

## Metadata-Only Items That Must Not Be Promoted

The following items are metadata-only and must not be promoted without current static evidence:

- **xor**: `xor_array_solver_v2_fb15e14c` and `xor_array_solver_4e6d25f0` are Python solver scripts, not target binaries. Filename containing "xor" is not sufficient.
- **lookup_table**: `ascii_table_chinese_46efc7ea` is a PDF, not a PE target. `xor_array_solver` scripts are support code, not targets.
- **hash_md5_sha**: `sha_256_18019fca` filename containing "sha" is not sufficient. Blocked by missing bounded input domain.
- **simple_antidebug**: `seh_52be8d5c` filename containing "seh" is not sufficient. SEH.exe filename alone without static anti-debug evidence.
- **mixed_unknown**: `samplereverse_ca74a786` category "unknown" is not sufficient. No static triage has been run.
- **All cipher types** (rc4, des): Filenames containing "rc4" or "des" are not sufficient. No static triage has been run on these targets.

## Existing Routes to Reuse

The following existing tool/solver interfaces must be reused rather than recreated:

| Capability | Component Paths | Status |
| --- | --- | --- |
| inventory builder | `reverse_agent/local_reverse_inventory.py` | implemented, not run this round |
| training status builder | `reverse_agent/local_reverse_training_status.py` | implemented, read-only JSON supported |
| single-sample static triage | `reverse_agent/local_reverse_single_sample_static_triage.py`, `reverse_agent/ida_scripts/collect_evidence.py` | implemented, not executed this round |
| IDA static extraction | `reverse_agent/tool_runners.py`, `reverse_agent/ida_scripts/collect_evidence.py` | implemented, not executed this round |
| debugger dynamic extraction | `reverse_agent/tool_runners.py`, `reverse_agent/olly_scripts/collect_evidence.py` | implemented, out of scope this round |
| structured evidence | `reverse_agent/evidence.py`, `reverse_agent/tool_runners.py` | implemented |
| solver templates | `reverse_agent/local_reverse_string_solver.py`, `reverse_agent/local_reverse_solver_profiles.py`, `reverse_agent/local_reverse_semantic_rules.py`, `reverse_agent/local_reverse_constraint_recovery.py`, `reverse_agent/advanced_solvers.py` | implemented, mixed validation |
| harness candidate verification | `reverse_agent/harness.py`, `reverse_agent/local_reverse_console_validator.py`, `reverse_agent/local_reverse_console_pair_validator.py` | implemented, out of scope this round |
| affine inverse handoff | `reverse_agent/local_reverse_affine_inverse_handoff.py` | implemented |
| GUI/CLI entry points | `app.py`, `reverse_agent/gui.py`, `reverse_agent/pipeline.py` | implemented |

No new tools or capabilities were implemented in this round. No duplicate interfaces were created.

## Highest Priority Categories for Next Evidence-Producing Round

Based on the capability gap matrix, the highest priority categories for the next evidence-producing round are:

1. **string_comparison** or **shift_affine**: These can validate the simple static-triage path. `string_comparison` has a solved sample and a needs_triage sample with static evidence. `shift_affine` has `affine_8cfebe03` with current static triage evidence.

2. **rc4** or **des**: These exercise cipher evidence fields. Multiple PE targets exist and cipher material evidence modules are implemented. No static triage has been run on cipher targets yet.

3. **lookup_table** (planning row only): Records the field-support gap. Tool evidence is unavailable and static triage output lacks table extraction fields. This is a planning row, not solver work.

## Non-Promotion Safeguard

This round did not execute samples, solvers, IDA, Ghidra, debuggers, emulators, runtime probes, harnesses, or GUI workflows. No sample is marked as solved, static_verified, or runtime_validated. All rows reflect metadata-level planning over existing artifacts only.

## Limitations

- This matrix is a metadata-level planning artifact.
- The `training_status.json` was generated 2026-06-15 and may be stale for samples with later static triage evidence (e.g., `affine_8cfebe03`).
- The coverage matrix was generated 2026-06-18 and does not reflect `affine_8cfebe03` static triage evidence from 2026-06-19.
- XOR and lookup_table representatives may be support-code metadata rather than concrete targets.
- Hash work remains blocked for solver purposes until a bounded input domain is recovered.
- `bit_operations` is treated as a secondary/cross-cutting tag and does not have a standalone row in this matrix.
