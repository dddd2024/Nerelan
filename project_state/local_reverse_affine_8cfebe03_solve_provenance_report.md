# Solve Provenance Report

## Sample: affine_8cfebe03

**Round:** round_20260619_affine_reverse_solving_ciphertext_handoff_v1
**Decision:** decision_20260619_affine_reverse_solving_ciphertext_handoff_v1
**Mainline:** reverse_solving
**Generated:** 2026-06-19T10:23:00Z

## 1. Summary

The reverse-solving handoff for `affine_8cfebe03` is **BLOCKED** on missing expected ciphertext evidence. The affine transform material is fully resolved, and the existing affine inverse handoff interface was reused without modification. A bounded search of 12 locations found no expected ciphertext with trusted provenance. No candidate was derived and no final answer is claimed.

## 2. Transform Material Provenance

- **Status:** resolved (prior accepted round)
- **Source round:** round_20260619_affine_static_material_artifact_enrichment_v1
- **Source tool:** IDA
- **Affine parameters:** a=5, b=5, modulus=26, a_inverse=21
- **Forward formula:** `c = (5 * p + 5) mod 26`
- **Inverse formula:** `p = 21 * (c - 5) mod 26`
- **Input domain:** lowercase ASCII 'a'-'z' (97..122)
- **Program type:** encoder (no compare/success branch in `_main_0`)

## 3. Inverse Handoff Provenance

- **Interface used:** `reverse_agent.local_reverse_affine_inverse_handoff.run_affine_inverse_handoff`
- **Interface path:** `reverse_agent/local_reverse_affine_inverse_handoff.py`
- **Interface unchanged:** yes (no source modifications this round)
- **Input artifact:** `project_state/local_reverse_affine_main0_targeted_ida_decompile.json`
- **Output artifact:** `project_state/local_reverse_affine_8cfebe03_inverse_handoff_current.json`
- **Status:** BLOCKED
- **Blocked reason:** MISSING_EXPECTED_CIPHERTEXT

## 4. Expected Ciphertext Search

- **Found:** no
- **Trusted provenance:** none
- **Search evidence artifact:** `project_state/local_reverse_affine_8cfebe03_expected_ciphertext_evidence.json`
- **Searched location count:** 12

### Searched Locations

| # | Location | Kind | Result |
|---|----------|------|--------|
| 1 | `training_materials/local_reverse/cases/affine_8cfebe03.json` | local_sample_metadata | `expected_flag` is empty |
| 2 | `local_reverse_affine_8cfebe03_transform_material_static_extract.json` | current_static_evidence | no expected ciphertext field |
| 3 | `local_reverse_affine_8cfebe03_transform_material_evidence.json` | current_static_evidence | StaticConstantEvidence only |
| 4 | `local_reverse_affine_8cfebe03_transform_material_dispatch_plan.json` | current_static_evidence | has_compare_site=false |
| 5 | `local_reverse_affine_main0_targeted_ida_decompile.json` | current_static_evidence | candidate_compare_sites empty; pure encoder |
| 6 | `local_reverse_affine_8cfebe03_current_static_triage.json` | current_static_evidence | compare_contexts reference CRT heap marker only |
| 7 | `local_reverse_affine_8cfebe03_static_evidence_summary.json` | current_static_evidence | candidate=null, no_candidate=true |
| 8 | `local_reverse_affine_8cfebe03_current_static_bridge_result.json` | current_static_evidence | expected_value_location empty |
| 9 | `E:\reverse\逆向课程2024春补考03` | challenge_statement_directory | only affine.exe, cpp3.exe, IDA files; no problem statement |
| 10 | `E:\reverse\逆向课程2022春补考03` | challenge_statement_directory | only affine.exe, cpp3.exe, IDA files; no problem statement |
| 11 | `E:\reverse\逆向课程2023春补考03` | challenge_statement_directory | no text/md/json/pdf/doc files |
| 12 | `E:\reverse` (root) | challenge_statement_directory | only ascii_table_chinese.pdf; not an affine problem statement |

## 5. Solve Blocker

- **Artifact:** `project_state/local_reverse_affine_8cfebe03_solve_blocker.json`
- **Status:** BLOCKED
- **Blocked reason:** MISSING_EXPECTED_CIPHERTEXT_WITH_TRUSTED_PROVENANCE

## 6. Candidate

- **Candidate:** none
- **Candidate label:** none
- No candidate was derived because no trusted expected ciphertext is available.

## 7. Provenance Notes

- Transform material was resolved in a prior accepted tool_integration round.
- This round reused the existing affine inverse handoff interface without modification.
- A bounded search of 12 locations found no expected ciphertext with trusted provenance.
- No candidate was derived; no final answer is claimed.
- The target binary was not executed; no dynamic analysis was performed.
- No source files were modified in this round.

## 8. Next Recommended Mainline

`reverse_solving` (blocked on missing expected ciphertext evidence).

## 9. Next Recommended Action

Obtain expected ciphertext from the original challenge statement (provenance=`challenge_statement`) or have the user explicitly provide one (provenance=`user_provided`), then rerun `reverse_agent.local_reverse_affine_inverse_handoff` with the ciphertext input to produce a READY handoff and a `static_candidate`.
