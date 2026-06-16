# Local Reverse Training Resume Plan

## Scope

Decision: `decision_20260616_local_reverse_training_resume_plan_v1`

Round: `round_20260616_local_reverse_training_resume_plan_v1`

This resume plan is metadata-only. It does not execute local samples, run solver candidate generation, run runtime probes, upload binaries, read bulk `solve_reports/`, or treat stale project_state facts as current training evidence.

## Status Snapshot

| Status | Count |
| --- | ---: |
| solved | 1 |
| blocked | 2 |
| needs_triage | 1 |
| inventory_only | 46 |
| **Total** | **50** |

## Solved Samples

| sample_id | category | known_candidate |
| --- | --- | --- |
| cpp1_bcbd9979 | cpp | hookapi |

## Blocked Samples

| sample_id | category | blocked_reason | resume_priority | resume_prerequisite |
| --- | --- | --- | --- | --- |
| cpp2_4c69f173 | cpp | MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005 | medium | bounded_static_triage to extract sub_401005 |
| sha_256_18019fca | crypto/hash | NO_BOUNDED_HASH_PREIMAGE_DOMAIN | low | problem_statement_hint or bounded_input_length_evidence |

## Needs Triage Samples

| sample_id | category | blocked_reason | resume_priority | resume_prerequisite |
| --- | --- | --- | --- | --- |
| affine_8cfebe03 | unknown | STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON | high | bounded_static_triage with IDA re-run or alternative static tool |

## Active Investigation Samples

| sample_id | category | investigation_status | contradiction | resume_priority |
| --- | --- | --- | --- | --- |
| cpp1_2f6fcb63 | cpp | TARGET_REANCHOR_NEEDED | CURRENT_TARGET_PATH_REJECTED: Destination[16]==byte_429A30[16]==0x00 makes success path unreachable | high |

## Resume Priorities

### High Priority

1. **affine_8cfebe03** — needs_triage with IDA tool blocker; resolving blocker unlocks static triage
2. **cpp1_2f6fcb63** — active investigation with success boundary contradiction; resolving contradiction unblocks solving path

### Medium Priority

3. **cpp2_4c69f173** — blocked by missing transform function; bounded_static_triage may extract sub_401005

### Low Priority

4. **sha_256_18019fca** — blocked by unbounded hash preimage; requires external hint or domain evidence

## Primary Queue Resume Candidates

| sample_id | allowed_next_action | reason |
| --- | --- | --- |
| cpp1_2f6fcb63 | bounded_static_triage | resolve success boundary contradiction |
| cpp1_378eeffd | bounded_static_triage | no prior triage; cpp category |
| cpp1_7b504c54 | bounded_static_triage | no prior triage; cpp category |
| cpp2_32f1713e | bounded_static_triage | next_queue_hint from status_summary_sync |

## Type Coverage Gaps

| type_category | total | solved | blocked | needs_triage | inventory_only | gap_reason |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| crypto/cipher | 9 | 0 | 0 | 0 | 9 | pending_cipher_static_evidence_profile blocks all |
| crypto/hash | 1 | 0 | 1 | 0 | 0 | unbounded hash preimage domain |
| unknown | 12 | 0 | 0 | 1 | 11 | category unknown prevents targeted triage |

## Recommended Resume Sequence

1. Resolve affine_8cfebe03 IDA tool blocker (high priority, unblocks needs_triage)
2. Resolve cpp1_2f6fcb63 success boundary contradiction (high priority, active investigation)
3. Run bounded_static_triage on cpp1_378eeffd and cpp1_7b504c54 (primary queue, no prior triage)
4. Build cipher_static_evidence_profile for DES and RC4 samples (unblocks secondary queue)
5. Attempt sub_401005 extraction for cpp2_4c69f173 (medium priority, blocked sample)
