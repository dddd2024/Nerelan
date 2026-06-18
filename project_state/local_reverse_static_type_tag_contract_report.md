# Local Reverse Static Type Tag Contract Report

Decision: `decision_20260618_static_type_tag_contract_scope_wording_repair_v1`
Round: `round_20260618_static_type_tag_contract_scope_wording_repair_v1`
Generated: 2026-06-18

## Scope

This is a contract/schema artifact. It defines the static type tag contract for the local reverse training set. It did not execute samples, solvers, IDA, Ghidra, debuggers, emulators, runtime probes, sidecars, GUI workflows, or bulk `solve_reports` scans.

## Previous Round Blocker Resolution

Previous round `decision_20260618_static_type_tag_contract_scope_repair_v1` was BLOCKED because the Implementation Scope contained a "明确禁止修改" header that the gate parser `_allowed_scope_paths` did not recognize as a stop-word. This caused `.codex-skills/*` and `solve_reports/*` from the forbidden block to be parsed as allowed paths.

This round's decision_packet.md removed the forbidden path bullets from the Implementation Scope section entirely. The Implementation Scope now only lists allowed paths. Preflight PASSED with `forbidden_paths_not_allowed: allowed scope contains no forbidden paths`.

## Contract Artifact

- Path: `project_state/local_reverse_static_type_tag_contract.json`
- Schema version: 1
- Required tag ids: 13
- Required fields per tag: 8 (`evidence_requirements`, `allowed_evidence_sources`, `confidence_rules`, `solver_or_tool_route`, `not_sufficient_conditions`, `next_minimal_task`, `metadata_only_allowed`, `static_verified_requires`)
- Global rules: 4 (filename hint never static_verified, solver module name never static_verified, metadata-only is not static evidence, sample name pattern never upgrades confidence)

## Coverage Matrix Cross-Reference

| Tag ID | Coverage Matrix type_id | Samples | Solved | Coverage Status | Contract metadata_only_allowed |
| --- | --- | ---: | ---: | --- | --- |
| string_comparison | string_comparison | 35 | 1 | partial_validated_sample_plus_metadata_gap | true |
| xor | xor | 2 | 0 | gap_or_tool_only | true |
| shift_affine | shift | 4 | 0 | metadata_level_unverified | true |
| bit_operations | bit_operations | 7 | 0 | metadata_level_unverified | true |
| lookup_table | lookup_table | 3 | 0 | gap_or_tool_only | true |
| rc4 | rc4 | 8 | 0 | metadata_level_unverified | true |
| des | des | 5 | 0 | metadata_level_unverified | true |
| tea_xtea | tea | 0 | 0 | gap_no_current_samples | true |
| base64 | base64 | 0 | 0 | gap_no_current_samples | true |
| hash_md5_sha | hash_md5_sha | 2 | 0 | metadata_level_unverified | true |
| gui_validation | gui_validation | 0 | 0 | gap_no_current_samples | true |
| simple_antidebug | simple_antidebug | 1 | 0 | metadata_level_unverified | true |
| mixed_unknown | mixed_unknown | 7 | 0 | metadata_level_unverified | true |

Note: The coverage matrix uses `shift` and `tea` as type_ids; the contract uses `shift_affine` and `tea_xtea` per decision_packet.md requirements.

## Global Rules

1. **Filename hint alone never static_verified**: A sample filename containing a type keyword (e.g., "rc4", "des", "affine") is not sufficient to mark the sample as static_verified for that type.
2. **Solver module name alone never static_verified**: A solver module name containing a type keyword (e.g., "rc4_material_evidence", "affine_inverse_handoff") is not sufficient to mark the sample as static_verified.
3. **Metadata-only is not static evidence**: Inventory metadata (category, tags, filename) is not equivalent to static triage evidence.
4. **Sample name pattern alone never upgrades confidence**: A sample name pattern match cannot upgrade confidence from low to medium or high.

## Per-Tag Evidence Requirements Summary

### string_comparison
- Requires: compare callsite identified, operand source identified, operand producer or value extracted
- Not sufficient: filename contains "cpp", category is "cpp", solver module name contains "string_solver"
- Static verified requires: static_triage success + compare callsite + operand source + runtime validation

### xor
- Requires: XOR instruction/loop identified, XOR key identified, loop bounds determined
- Not sufficient: filename contains "xor", solver script filename contains "xor_array_solver"
- Static verified requires: static_triage success + XOR instruction + key + runtime validation

### shift_affine
- Requires: shift/affine instruction identified, transform constants extracted, loop structure determined
- Not sufficient: filename contains "affine" or "shift", solver module name contains "affine_inverse_handoff"
- Static verified requires: static_triage success + shift/affine instruction + constants + runtime validation

### bit_operations
- Requires: bitwise operations identified, operation sequence traced, chain from input to comparison
- Not sufficient: derived from xor/affine/seh metadata without direct bit operation evidence
- Static verified requires: static_triage success + bit operation instructions + chain traced + runtime validation

### lookup_table
- Requires: table access identified, table base/size determined, table contents extracted
- Not sufficient: filename contains "table" or "array", solver script filename contains "xor_array_solver"
- Static verified requires: static_triage success + table access + base/size + contents + runtime validation

### rc4
- Requires: RC4 KSA/PRGA loop identified, S-box initialization identified, key material identified
- Not sufficient: filename contains "rc4", solver module name contains "rc4_material_evidence"
- Static verified requires: static_triage success + KSA/PRGA + S-box + key + runtime validation

### des
- Requires: DES round/S-box identified, permutation tables identified, key schedule identified
- Not sufficient: filename contains "des", solver module name contains "des"
- Static verified requires: static_triage success + DES round + constants + key schedule + runtime validation

### tea_xtea
- Requires: TEA/XTEA round function identified, delta constant identified, 128-bit key identified
- Not sufficient: filename contains "tea", no current inventory samples with TEA metadata
- Static verified requires: static_triage success + round function + delta constant + key + runtime validation

### base64
- Requires: Base64 table/constant identified, transform function identified, I/O identified
- Not sufficient: filename contains "base64", solver module name contains "base64_material_evidence"
- Static verified requires: static_triage success + table + function + I/O + runtime validation

### hash_md5_sha
- Requires: hash constants identified, input domain bounded, comparison point identified
- Not sufficient: filename contains "sha" or "md5", hash identified but input domain unbounded
- Static verified requires: static_triage success + hash constants + comparison + bounded domain + runtime validation

### gui_validation
- Requires: GUI framework API identified, input control identified, validation handler identified
- Not sufficient: filename contains "gui", solver module name contains "console_validator"
- Static verified requires: static_triage success + GUI API + input control + handler + runtime validation

### simple_antidebug
- Requires: anti-debug technique identified, check location identified, bypass strategy determined
- Not sufficient: filename contains "seh" or "debug", SEH.exe filename alone
- Static verified requires: static_triage success + anti-debug technique + check location + bypass + runtime validation

### mixed_unknown
- Requires: static triage must be run, at least one transform type assigned or documented as unrecognized
- Not sufficient: filename contains "main" or "pwd", category is "unknown", no static triage run
- Static verified requires: static_triage success + re-tagged to specific type or documented as mixed_unknown + runtime validation

## Metadata-Level Only Categories

The following categories remain metadata-level only (no current static triage evidence):
- xor (2 samples, gap_or_tool_only)
- shift_affine (4 samples, metadata_level_unverified)
- bit_operations (7 samples, metadata_level_unverified)
- lookup_table (3 samples, gap_or_tool_only)
- rc4 (8 samples, metadata_level_unverified)
- des (5 samples, metadata_level_unverified)
- tea_xtea (0 samples, gap_no_current_samples)
- base64 (0 samples, gap_no_current_samples)
- hash_md5_sha (2 samples, metadata_level_unverified)
- gui_validation (0 samples, gap_no_current_samples)
- simple_antidebug (1 sample, metadata_level_unverified)
- mixed_unknown (7 samples, metadata_level_unverified)

Only `string_comparison` has a partial_validated_sample_plus_metadata_gap status with 1 solved sample.

## Forbidden Path Modifications

No `reverse_agent/` source files, `.codex-skills/` files, or `solve_reports/` files were modified in this round. All modifications are within the allowed scope: `project_state/` artifacts and `tests/` files.

## Capability Map Audit

Existing capabilities were audited from `project_state/local_reverse_solver_tool_capability_map.json`:
- inventory_builder: implemented, not run this round
- training_status_builder: implemented, read-only JSON supported
- single_sample_static_triage: implemented, not executed this round
- ida_static_extraction: implemented, not executed this round
- debugger_dynamic_extraction: implemented, out of scope this round
- structured_evidence: implemented
- solver_templates: implemented, mixed validation
- harness_candidate_verification: implemented, out of scope this round
- gui_cli_entrypoints: implemented, CLI JSON gap closed

No new tools or capabilities were implemented. The contract references existing capabilities as allowed evidence sources.

## Test Coverage

Tests in `tests/test_local_reverse_static_type_tags.py` verify:
1. Contract covers all 13 required tag ids
2. Each tag has all 8 required fields
3. Filename/metadata hints are not sufficient for static_verified (global rules)
4. string_comparison, xor, shift_affine, lookup_table, rc4, des, hash_md5_sha, simple_antidebug have clear evidence requirements
5. Cipher/hash/anti-debug types do not get upgraded to static_verified based on sample name or solver module name alone
