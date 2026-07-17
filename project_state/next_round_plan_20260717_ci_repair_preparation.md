# Next Round Plan

## Status

Current v4 round result: REWORK_REQUIRED.

Reason:

- local governance evidence chain is closed;
- local validation passed;
- final state correctly refuses acceptance because remote GitHub checks failed.

This document is planning only. It is not an execution authority. A future DECISION_PACKET must be generated before any implementation round.

## Proposed Mainline

mainline: project_governance

## Goal

Create the next bounded round to restore remote validation capability without mixing it with previous evidence convergence work.

The next round should focus only on:

1. diagnosing GitHub Actions Install package failure;
2. determining whether the failure is caused by packaging metadata, dependency declaration, or CI environment mismatch;
3. preparing a minimal CI/package repair decision if required.

## Do Not Do

Do not:

- modify current v4 sealed artifacts;
- reopen previous rounds;
- change reverse-solving logic;
- modify Runner, User Solve, frontend, database, or roadmap systems;
- declare ACCEPTED before remote checks are green;
- modify workflows or packaging files without a dedicated approved Decision.

## Required Evidence Before New Decision

Inspect:

- GitHub Actions failed workflow logs;
- Install package step output;
- pyproject.toml;
- dependency files;
- workflow definitions;
- current PR #5 status.

## Expected Next Decision Scope

If the failure is confirmed as CI/package related:

Allowed scope:

- pyproject.toml;
- setup metadata;
- dependency declarations;
- CI workflow only when required.

Forbidden scope:

- application architecture;
- project_state redesign;
- reverse solving;
- tool integration.

## Acceptance Criteria

The future repair round is accepted only when:

1. GitHub CI passes;
2. State Gate passes;
3. Decision Preflight passes;
4. project_state records remote run IDs and conclusions;
5. final status propagation remains consistent;
6. no local PASS is used to override remote failure.

## Transition

Current state remains:

REWORK_REQUIRED

No merge is authorized until a future approved Decision completes remote validation.