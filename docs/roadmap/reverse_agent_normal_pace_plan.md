# Reverse Agent Normal-Pace Plan

> **Roadmap material — not execution authority.** Only `project_state/decision_packet.md`
> is the execution authority for any given round. This document records the intended
> normal phase order so contributors can see where the current round sits in the
> longer sequence. It does not authorize commands, file changes, or capabilities.

## Purpose

Establish a deliberate, staged pace for reverse-agent evolution that prioritizes
governance stabilization, state-metadata hygiene, and decision-gate truthfulness
before any higher-risk capability (User Solve replay, Web runtime, tool
integration, remote runners, or automation) is enabled.

This plan replaces the earlier rushed MVP framing that attempted to advance
reverse-solving and Web capabilities before state metadata and audit gates were
trustworthy. The previous framing is superseded; nothing in this document
authorizes reopening those capabilities.

## Authority

- Execution authority: `project_state/decision_packet.md` (per round).
- Command authority: `project_state/gates/command_plan.json` (per round).
- Roadmap authority: this document and `docs/roadmap/project_state_domain_taxonomy_supplement.md`.
- Roadmap entries are **not** execution authority and must not be cited as
  justification to skip a gate, run an unauthorized command, or modify a
  forbidden path.

## Normal Phase Order

1. **Governance stabilization.** Decision packets, command-plan, preflight,
   final-check, report-summary, execution-log, and run-closeout must be
   consistent and truthful. Status fields must reflect observed evidence, not
   aspirations. (Accepted baseline.)
2. **State-metadata foundation (Phase A).** Add scope/domain/mainline/role/
   freshness metadata to `state_manifest`, `artifact_index`, and
   `negative_results` without moving, deleting, or migrating state files.
   Missing metadata on legacy entries is a non-blocking warning.
   (Active round: `round_20260706_scoped_state_metadata_foundation_big_step_v1`.)
3. **State domain taxonomy (Phases B–F).** Create the domain skeleton, copy
   reverse-solving `current_state`, split `negative_results`, turn top-level
   `current_state.json` into a global summary, then harden final-check to
   require scope metadata on new records. Each phase is its own future decision.
4. **User Solve layer foundation.** Already has an accepted baseline; not
   reopened by the metadata rounds.
5. **Evidence replay.** Replay captured evidence without live reverse-solving
   only after metadata coverage is sufficient to scope evidence by domain.
6. **Tool integration.** IDA/Ghidra/debugger integration remains deferred until
   evidence replay and state metadata can scope tool output safely.
7. **Web/frontend runtime.** Manual-mode Web orchestrator has an accepted
   baseline; full Web runtime is deferred until tool integration and state
   scoping are in place.
8. **CI/state-gate hardening.** Read-only CI/state-gate foundation exists;
   workflow mutation remains out of scope.
9. **Runner dispatch and automation.** Deferred; this plan does not authorize
   runner dispatch, workflow dispatch, or auto-iteration.

## Non-Goals

- This plan does not commit to a date for any phase.
- This plan does not authorize sample solving, runtime validation, candidate
  search, external reverse tools, Web runtime, database creation, cleanup
  apply, file deletion, or file moves.
- This plan does not supersede any active decision packet.

## Relationship to the State Taxonomy Supplement

See `docs/roadmap/project_state_domain_taxonomy_supplement.md` for the detailed
Phase A–F breakdown of the state domain taxonomy work. This normal-pace plan
sets the order; the supplement defines the state-metadata phases.
