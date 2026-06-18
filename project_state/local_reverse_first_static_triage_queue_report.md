# Local Reverse First Static Triage Queue Report

Decision: `decision_20260618_training_first_static_triage_queue_v1`
Round: `round_20260618_training_first_static_triage_queue_v1`
Generated: `2026-06-18T16:20:00Z`

## Scope

This report summarizes the first metadata-level static triage queue for the local reverse training set. It is a planning/schema artifact only. This round did not execute samples, solvers, harnesses, IDA, Ghidra, debuggers, emulators, runtime probes, sidecars, GUI workflows, or a full `solve_reports/` scan.

No `reverse_agent/` source files or `.codex-skills/` files were modified.

## Queue Policy

- Select at most one representative sample per primary type for the first queue.
- Select only sample ids already present in `project_state/local_reverse_training_coverage_matrix.json`.
- Treat `bit_operations` as a secondary/cross-cutting tag in this queue, not as a separate duplicate representative.
- Keep all queue items metadata-only until a later authorized round produces static triage or manual static evidence.
- Never promote from filename, sample id, category, solver module name, inventory metadata, or coverage row membership alone.

## Selected Queue Items

| Queue ID | Type | Sample ID | Before Triage | Notes |
| --- | --- | --- | --- | --- |
| `first_static_triage_string_comparison_001` | `string_comparison` | `cpp2_fc735338` | `partial_validated_sample_plus_metadata_gap` | First inventory-only cpp representative in the current row. |
| `first_static_triage_xor_001` | `xor` | `xor_array_solver_v2_fb15e14c` | `gap_or_tool_only` | Records the XOR solver/support metadata gap; not target proof. |
| `first_static_triage_shift_affine_001` | `shift_affine` | `affineenc_333f8ca9` | `metadata_level_unverified` | PE representative for later affine/shift static evidence profiling. |
| `first_static_triage_lookup_table_001` | `lookup_table` | `ascii_table_chinese_46efc7ea` | `gap_or_tool_only` | Queued only as `needs_static_triage_field_support_or_manual_static_evidence` because tool evidence is unavailable. |
| `first_static_triage_rc4_001` | `rc4` | `rc4enc_a1897c10` | `metadata_level_unverified` | First PE RC4 target after solver-support scripts in the current row. |
| `first_static_triage_des_001` | `des` | `desenc_40cba418` | `metadata_level_unverified` | First PE DES target after solver-support script in the current row. |
| `first_static_triage_hash_md5_sha_001` | `hash_md5_sha` | `sha_256_18019fca` | `metadata_level_unverified` | Keeps `bounded_domain_required=true` before any solver attempt. |
| `first_static_triage_simple_antidebug_001` | `simple_antidebug` | `seh_52be8d5c` | `metadata_level_unverified` | Static SEH/anti-debug triage only; debugger execution remains forbidden. |
| `first_static_triage_mixed_unknown_001` | `mixed_unknown` | `samplereverse_ca74a786` | `metadata_level_unverified` | One-sample static triage seed for later evidence-based re-tagging. |

## Blocked Categories

| Type | Coverage Row | Reason | Next Allowed Action |
| --- | --- | --- | --- |
| `tea_xtea` | `tea` | `blocked_no_current_sample` | Add or identify TEA/XTEA material before planning static triage. |
| `base64` | `base64` | `blocked_no_current_sample` | Add metadata/type tagging only after current sample or static evidence exists. |
| `gui_validation` | `gui_validation` | `blocked_no_current_sample` | Add GUI/static UI evidence fields only after a current GUI sample is identified. |

## Required Evidence Themes

- String comparison: compare gate, callsite, operand source, compared value or producer.
- XOR: XOR operation, key or derivation, loop bounds and operand width.
- Shift/affine: transform operation, constants, loop structure.
- Lookup table: table access, base/size, contents; support fields or manual static evidence are required first.
- RC4/DES: cipher structure, constants/state, key material or schedule.
- Hash: hash structure, comparison point, and bounded input domain.
- Simple anti-debug: technique, check location, branch condition, static bypass plan.
- Mixed unknown: one static triage pass to identify or explicitly retain the unknown type.

## Limitations

- This queue does not mark any sample as solved, static-verified, or runtime-validated.
- Current coverage matrix and inventory rows are metadata-level selection sources, not static evidence.
- `lookup_table` and `xor` rows include support-artifact or solver-script shaped ids; this report preserves that limitation rather than promoting them.
- Hash work remains blocked for solver purposes until a bounded input domain is recovered.
- `bit_operations` is represented only as a secondary tag on affine/anti-debug style queue items where later static evidence may observe bit operations.

## Next Authorized Round Types

- A later `tool_integration` or `training_dataset` round may add static triage output fields for lookup-table and type-tag evidence.
- A later `reverse_solving` round may run one bounded static triage item only if the decision explicitly authorizes the tool route.
- A later metadata-only intake round may add current samples for `tea_xtea`, `base64`, or `gui_validation`.
