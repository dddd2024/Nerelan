# Owner verification — Frontend V1

## Status

```text
IMPLEMENTATION: OWNER_DIRECT_FIX_APPLIED
PR: #119
BRANCH: agent/frontend-v1-openhands-ui
PUBLICATION: NOT_AUTHORIZED
MERGE: NOT_AUTHORIZED
```

This document supersedes self-declared completion checkmarks in earlier visual notes. A criterion is accepted only when supported by exact-head source inspection and fresh command evidence.

## Owner-direct repairs

The Owner takeover corrected the following defects:

1. Mobile drawer opening no longer triggers its own route-close effect.
2. Drawer `aria-hidden` now reflects the actual open state.
3. The drawer receives initial focus, traps Tab focus, restores focus on close and locks body scrolling.
4. Background menu/workspace regions are inert and hidden from assistive technology while the modal drawer is open.
5. Escape, backdrop, close-button and SPA navigation close paths use one stable lifecycle.
6. Mobile task detail uses one state variable for Activity, Changed Files, Evidence and Authority and can return to Activity.
7. The duplicate hidden mobile tab/content implementation was removed.
8. The resize control uses separator semantics and changes actual panel widths.
9. Pointer resizing measures the complete split container rather than the four-pixel handle.
10. Regression tests now assert the broken user interactions rather than component presence alone.

## Exact verification commands

The following must all be executed on the same final Head:

```bash
npm --prefix frontend test
npm --prefix frontend run typecheck
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix frontend run build:mock
git diff --check 1142dd324fdd4c4bf2a1353d9d5e93bc04b33507..HEAD
```

Do not replace these results with an Agent summary. Record command, exit code and exact Head.

## Visual evidence status

Committed reverse-agent target captures currently include:

- `artifacts/screenshots/task-inbox-desktop.png`
- `artifacts/screenshots/task-inbox-mobile.png`
- `artifacts/screenshots/task-detail-desktop.png`
- `artifacts/screenshots/task-detail-mobile.png`
- `artifacts/screenshots/custom-permission-editor.png`
- `artifacts/screenshots/overnight-authorization-summary.png`

The earlier `OPENHANDS_VISUAL_ACCEPTANCE.md` is a structural comparison document. It does not by itself prove that an OpenHands 1.8.0 reference screenshot and an exact-head reverse-agent screenshot were captured side by side. Final visual acceptance still requires a fresh exact-head browser review.

## Governance boundary

The repository-wide CI may remain red because the committed active mainline intent is bound to Issue #111 while this engineering branch carries Issue #117 Decision v4. That mismatch is separate from frontend validation and must not be repaired by changing `tests/**`, `reverse_agent/**`, workflows or `project_state/mainline_merge_intents/**` under this Work Item.

PR #119 must remain Draft until independent exact-head acceptance. No merge, mark-ready, auto-merge, main push, tag, release, publication or deployment is authorized.
