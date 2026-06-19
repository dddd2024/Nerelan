# Current Static Provenance Report - affine_8cfebe03

**Round:** round_20260619_affine_current_static_bridge_validation_v1
**Generated:** 2026-06-19T05:15:49Z

## Current Static Triage Artifact

- **Path:** `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
- **SHA256:** `1fbecf76c0ceaa1149d6f894d3006b8ee4b5345dc7162a14210854af7f0426c1`
- **Size:** 34645 bytes
- **Source Run:** `round_20260619_affine_current_static_bridge_validation_v1`
- **Tool Status:** `success`
- **Source Tool:** `IDA`
- **Executed Sample:** False
- **Static Only:** True
- **Runtime Validated:** False
- **IDA Evidence Regenerated This Round:** True

## Evidence Counts

| Family | Count |
|--------|-------|
| input | 1 |
| compare | 1 |
| constants | 0 |
| transform_hints | 1 |
| crypto_signatures | 0 |
| gui | 0 |
| anti_debug | 1 |

## Solver Dispatch Plan

- **Readiness:** `needs_current_static_provenance`
- **Recommended Profiles:** ['string_compare', 'anti_debug_precondition']
- **Required Missing Evidence:** ['transform_constant_evidence']

## Provenance Notes

- source_artifact: local_reverse_affine_8cfebe03_current_static_triage
- runtime_validated=false; static-only artifact

## Next Recommended Mainline

`tool_integration`
