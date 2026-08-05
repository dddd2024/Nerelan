# OpenHands Reuse Map

This document maps OpenHands 1.8.0 source concepts to the patterns adapted in
the reverse-agent Frontend V1. reverse-agent does **not** fork OpenHands, does
not copy its frontend or Agent Loop, and does not build a second control
platform. The reuse is conceptual adaptation only.

## Adaptation principles

- **Thin adapter, not a fork.** Only the user-facing policy/permission concepts
  are adapted. No OpenHands source files are vendored.
- **No executor / agent loop / sandbox / database / frontend copy.** All data in
  this frontend is fixture-driven; no real operations are invoked from the
  browser.
- **Delegation request, not authority.** Frontend policy selection is a
  delegation request. Real authorization is enforced by the server-side
  Authority system.

## Source-to-target reuse map

| OpenHands 1.8.0 concept | reverse-agent Frontend V1 adaptation | Notes |
| --- | --- | --- |
| Permission profile / mode selector | `PermissionSelector` + `profile-mapper.ts` | 4 modes: ASK_FOR_APPROVAL, CONTROLLER_REVIEW, OWNER_CONTROL, CUSTOM |
| Policy / capability contract | `types/index.ts` `PolicyContract`, `ResourceAccess`, `GithubCapability`, `PublicationCapability` | Domain types only; no runtime enforcement in browser |
| Policy validation | `schemas/policy.ts` `policySchema`, `validatePolicy` | Zod refinements for merge_pr/deploy_production/secrets/budgets/window |
| Plain-language authorization summary | `lib/policy-summary.ts` `summarPolicy` + `AuthorizationSummary` | Includes delegation-request disclaimer |
| Agent canvas / task inbox | `TaskInbox`, `TaskCard`, `TaskDetail` (tabs: Overview, Activity, Changes, Evidence, Permissions) | Summary-first, evidence-provenance aware |
| Activity timeline | `ActivityStream`, `Timeline` | Raw logs collapsed by default; expandable |
| Diff / changes view | `ChangesPanel`, `DiffViewer` | Simple add/remove coloring, no external highlighter |
| Evidence provenance | `EvidencePanel` | Full SHA / raw JSON collapsed by default |
| Custom policy editor | `CustomPolicyEditor` + sub-editors (`ResourceAccessEditor`, `GithubCapabilitiesEditor`, `PublicationEditor`, `AutonomousWindowEditor`) | All fields independently configurable; focus-trapped modal |
| Responsive shell | `AppShell`, `Sidebar` | Collapsible on mobile; keyboard accessible |

## Invariants preserved from the repository governance model

- `merge_pr` and `push_main` are independent toggles (no implicit enabling).
- Deployment is not implied by network write access.
- `secrets` must not be `raw_values`.
- `autonomousWindow.expiresAt` must be a valid future ISO date when enabled.
- All budgets must be positive integers.

## What is NOT reused

- OpenHands Agent Loop / runtime executor.
- OpenHands sandbox / runtime / database.
- OpenHands frontend components or styling assets (verbatim copy).
- Any merge / push / tag / release / deploy execution from the browser.
