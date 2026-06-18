# Local Reverse Training Coverage Gap Report

Decision: `decision_20260618_training_coverage_matrix_gap_report_v1`
Round: `round_20260618_training_coverage_matrix_gap_report_v1`
Generated: `2026-06-18T12:12:19Z`

## Scope

This is a metadata and source-capability coverage report for the local reverse training set. It did not execute samples, solvers, IDA, Ghidra, debuggers, emulators, runtime probes, sidecars, GUI workflows, or bulk `solve_reports` scans.

## Current Sample State

- Local project_state inventory: 65 metadata-only entries; metadata-only policy valid: `True`.
- GitHub-safe inventory mirror: 50 entries.
- Current read-only builder status: solved=1, blocked=2, needs_triage=0, inventory_only=62.
- Current read-only builder queue: 52 items, policy `simple_static_first_unsolved_only`.
- Existing live status file differs from the read-only builder: `True`; it is recorded but not silently overwritten in this round.

## Coverage Matrix Summary

| Type | Samples | Solved | Status | Confidence | Minimal next task |
| --- | ---: | ---: | --- | --- | --- |
| 字符串比较 | 35 | 1 | `partial_validated_sample_plus_metadata_gap` | medium | Select one high-priority cpp inventory_only sample and run only bounded static_triage in a later authorized round. |
| XOR | 2 | 0 | `gap_or_tool_only` | low | Promote XOR from solver/support metadata into first-class type tags during static triage; avoid assuming solver scripts are target evidence. |
| 移位/仿射 | 4 | 0 | `metadata_level_unverified` | low | Define affine/shift static evidence profile and apply it to one queued affine sample in a later static-only round. |
| 位运算 | 7 | 0 | `metadata_level_unverified` | low | Add metadata tags for bitwise transforms when static triage observes them; keep current row metadata-level. |
| 查表/数组 | 3 | 0 | `gap_or_tool_only` | low | Add lookup-table detection fields to static triage output before claiming coverage. |
| RC4 | 8 | 0 | `metadata_level_unverified` | low | Build cipher_static_evidence_profile for RC4 samples using static evidence only. |
| DES | 5 | 0 | `metadata_level_unverified` | low | Build cipher_static_evidence_profile for DES samples using static evidence only. |
| TEA/XTEA | 0 | 0 | `gap_no_current_samples` | low | Add or identify TEA/XTEA training material; none is visible in current inventory metadata. |
| Base64 | 0 | 0 | `gap_no_current_samples` | low | Add metadata/type tagging for Base64 when static evidence observes encoding constants or material fields. |
| hash/MD5/SHA | 2 | 0 | `metadata_level_unverified` | low | Recover bounded input domain evidence for SHA/MD5-style targets before solver attempts. |
| GUI 校验 | 0 | 0 | `gap_no_current_samples` | low | Add GUI-control/static UI evidence fields before planning GUI validation workflows. |
| 简单反调试/SEH | 1 | 0 | `metadata_level_unverified` | low | Static triage SEH/exception metadata first; do not run debugger in this training coverage round. |
| mixed/unknown | 7 | 0 | `metadata_level_unverified` | low | Triage unknown PE samples one at a time and backfill type tags from static evidence. |

## Solver And Tool Capability

- Static metadata/status: implemented via `reverse_agent/local_reverse_inventory.py` and `reverse_agent/local_reverse_training_status.py`.
- Static triage: implemented via `reverse_agent/local_reverse_single_sample_static_triage.py` and IDA evidence collection, but not executed in this round.
- StructuredEvidence: implemented for candidate, static string, constraint, runtime compare, Base64, RC4, and UTF-16LE material evidence.
- Harness/runtime validation: implemented but out of scope for this metadata-only decision.
- CLI gap closed this round: `python -m reverse_agent.local_reverse_training_status --json` now prints a read-only summary with `writes_files=false`.

## One-Week Priority Gaps

- **Inventory/status sync policy**: Local project_state inventory/status now carry 65 samples while the older GitHub-safe inventory target has 50 entries. Minimal next task: Decide whether to refresh GitHub-safe inventory/status from project_state in a dedicated metadata-only round, then run the existing builder with explicit outputs.
- **Type tag enrichment**: Large mixed/unknown and generic cpp buckets make the two-week plan depend on filename heuristics. Minimal next task: Add static-triage output fields for type tags and backfill only after evidence is observed.
- **Cipher static evidence profile**: RC4/DES samples exist, but current evidence is metadata-level and solver/tool capability is not sample-proven. Minimal next task: Define RC4/DES static evidence requirements and apply to one queued cipher sample in a later static-only round.
- **Simple transform recipes**: XOR/shift/affine/lookup rows are capability/tool-level more than sample-level. Minimal next task: Create minimal static recipes for string compare, XOR array, affine/shift, and lookup table detection before broad queue processing.
- **Hash bounded-domain policy**: SHA target is blocked by NO_BOUNDED_HASH_PREIMAGE_DOMAIN. Minimal next task: Recover length/domain hints or keep hash samples explicitly blocked instead of brute forcing.

## Two-Week Training Plan

1. Stabilize inventory/status sync and keep the read-only JSON status CLI as the audit capture path.
2. Backfill type tags from static evidence only: start with one string-compare sample and one affine/shift or XOR-family sample, then update the matrix from observed evidence.
3. Create RC4/DES static evidence profiles before touching cipher queues; keep cipher coverage metadata-level until a profile is exercised.
4. Define hash bounded-domain requirements and keep SHA/MD5 rows blocked when no input domain evidence exists.
5. Add GUI/anti-debug metadata fields to static triage output before planning runtime/debugger validation.

## Metadata-Level Only

The following rows are not live/static-triage verified for current samples: XOR, shift/affine, bit operations, lookup table, RC4, DES, TEA/XTEA, Base64, GUI validation, simple anti-debug, and most mixed/unknown samples. They should remain planning gaps until a later decision authorizes bounded static triage or runtime validation as appropriate.
