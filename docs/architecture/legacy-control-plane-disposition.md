# Legacy control-plane disposition

## Decision

PR #5 is frozen as migration evidence at `6a2867467c90cf37929787be3ba6061fcbb81312`. It is not an implementation baseline and v10 remains `REWORK_REQUIRED`. The clean base is activation-time `main` at `5884cf2abb37945652ef166cf0e78fa24593b0d5`, augmented only through reviewed selective integration.

The comparison contains 88 changed files. The complete list and per-capability evidence are in `project_state/gates/pr5_capability_inventory.json`; dispositions are in `project_state/gates/pr5_migration_disposition.json`.

## Keep

- Minimal packaging metadata is independent and can be transplanted.
- Full-history checkout and consumed-decision preflight are useful as narrow workflow hunks.
- Decision/command allowlists, policy lint, prompt consistency, context indexes, User Solve, and binary evidence semantics remain useful when narrowed to their proper domain.
- The manual Decision/Codex path remains a temporary R2/R3 compatibility path.

## Replace or move

- GitHub owns branch, commit, PR, review, check, merge, and release truth. `project_state` may cache an observation with provenance; it does not decide the fact.
- BMAD is limited to product discovery, PRD, architecture, and story planning.
- LangGraph is the single primary Python workflow runtime and checkpoint/resume owner. Microsoft Agent Framework is not a simultaneous primary runtime.
- Binary observation, claims, counterevidence, validation state, command allowlists, and high-risk authorization move into a reverse-agent Trust Layer.

## Archive

The v2-v10 reports, mutable report aliases, closeout chain, remote-attestation mirrors, and final seal remain readable through PR #5 and Git history. They are not copied into the selective baseline. No v11/v12 legacy closeout repair is authorized.

## Baseline and rollback

The selected baseline is `SELECTIVE_INTEGRATION_BASELINE`: current main plus three packaging files and two reviewed workflow patches. Each capability is committed independently so it can be reverted without touching PR #5 or the Trust Layer roadmap.

The first implementation boundary is `decision_20260720_selective_capability_integration_v1`. It integrates packaging and the two workflow hunks, then stops. It installs no framework and does not transplant `project_gate.py` wholesale.
