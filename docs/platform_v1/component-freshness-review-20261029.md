# Component freshness review — 2026-10-29

> Status: R1 evidence maintenance on accepted main
> `4c4abe868227e820ef01878e2fc367c3a6a3d544`, separate from PR #1189.
> It refreshes the `checked_at` review date of the four existing
> `governance/freshness-registry.json` entries. It does not change any runtime
> pin, vendored source, `current_version`, `owner`, `max_age_days`,
> `source_url` or `require_version_in_evidence` semantics, and it does not edit
> the historical 2026-09-19 review in
> `docs/architecture/FRESHNESS_AND_DRIFT_GOVERNANCE.md` §15.

## Why

All four entries carried `checked_at` 2026-09-19, which is 40 days old on
2026-10-29 against the unchanged 30-day `max_age_days`.

## Observation and its limits

Upstream observations were captured read-only by the host at
**2026-10-29T02:24:09Z** from official GitHub release and PyPI metadata, and
supplied to this review as data. This review did not perform network access,
install, import or execute any upstream package, CLI or model.

The observations are metadata only (release tag, publication time,
draft/prerelease flags, repository archive flag, PyPI version visibility).
Metadata does not establish compatibility, security posture, behavior,
maintenance status or runtime integration of any version, pinned or newer. No
compatibility test suite was run for this review; the 2026-09-19 compatibility
evidence remains the most recent recorded test evidence and is not re-claimed
here.

## Per-component findings

| Registry entry | Repository checkout evidence | Upstream observation (2026-10-29T02:24:09Z) | Decision |
|---|---|---|---|
| `langgraph` 1.0.10 | `pyproject.toml` declares `langgraph==1.0.10` | Pinned 1.0.10 observed on official PyPI. Latest GitHub release `1.2.18`, https://github.com/langchain-ai/langgraph/releases/tag/1.2.18, published 2026-10-26T20:04:45Z, draft=false, prerelease=false | Retain pin 1.0.10 |
| `langgraph-checkpoint-sqlite` 3.1.0 | `pyproject.toml` declares `langgraph-checkpoint-sqlite==3.1.0` | Pinned 3.1.0 observed on official PyPI. Latest PyPI version observed `3.1.2` | Retain pin 3.1.0; no automatic dependency upgrade |
| `openhands-agent-canvas` 1.6.1 | Vendored directory `frontend/src/vendor/agent-canvas-v1.6.1` with five files, each headed as a direct source fork of Agent Canvas v1.6.1 | Repository `OpenHands/agent-canvas`, https://github.com/OpenHands/agent-canvas, **archived=true**. Latest release `v1.6.1`, https://github.com/OpenHands/agent-canvas/releases/tag/v1.6.1, published 2026-07-24T19:31:56Z, draft=false, prerelease=false | Retain vendored 1.6.1 unchanged |
| `github-spec-kit` compatible | `reverse_agent/platform_v1/capability_registry.py` declares capability `spec-kit-planning` with provider `GitHub Spec Kit` and version descriptor `compatible` | Latest release `v1.2.5`, https://github.com/github/spec-kit/releases/tag/v1.2.5, published 2026-10-28T19:27:43Z, draft=false, prerelease=false | Retain descriptor |

Registry `source_url` values reviewed: https://github.com/langchain-ai/langgraph/releases
(both LangGraph entries), https://github.com/OpenHands/agent-canvas/releases and
https://github.com/github/spec-kit/releases. The supplied PyPI records state that
the official PyPI index was observed but do not include the exact request URL;
the canonical project pages are https://pypi.org/project/langgraph/ and
https://pypi.org/project/langgraph-checkpoint-sqlite/, named here as
references only, not as recorded request endpoints.

### Notes

- **OpenHands Agent Canvas archived=true.** The upstream repository is archived.
  The vendored release v1.6.1 equals the latest observed release. Archive status
  is recorded as observed; no maintenance guarantee, replacement, deletion or
  code upgrade is inferred or performed.
- **Spec Kit `compatible` is only a capability descriptor.** It names a
  planning convention implemented by the repository's own `GoalService`. It is
  not proof of an installed Spec Kit CLI, of tested live integration, or of
  compatibility with v1.2.5 or any other upstream release.
- **markdown-it-py.** Version 4.0.0 was observed upstream. Accepted base
  `4c4abe86` does not declare `markdown-it-py` in `pyproject.toml` (its only
  dependencies are the two LangGraph pins), and PR #1189 is unmerged. No
  registry entry is added; unmerged runtime state is not registered as landed.

## Upgrade candidates (not adopted)

Identified separately for a future, independently tested dependency change.
Each would be an R2 dependency change, and no compatibility, cost or security
claim is made:

- `langgraph` 1.0.10 → 1.2.18 (GitHub release).
- `langgraph-checkpoint-sqlite` 3.1.0 → 3.1.2 (PyPI).

No upgrade candidate exists for Agent Canvas (vendored version equals latest
observed release; upstream archived). Spec Kit v1.2.5 is recorded as the latest
upstream release; the repository does not pin a Spec Kit version.

## Supplied local evidence SHA256 records

These hashes were captured by the host and supplied with this task. This review
used only file read/search tools and **did not recompute any hash**; host
verification against checkout bytes remains required. No hash below was
derived by this review.

| Path | Supplied SHA256 |
|---|---|
| `pyproject.toml` | `6a79be119ec8a9742c36583459ba6e6cde4307fb4ce4eb96766f7560db26abe9` |
| `governance/freshness-registry.json` | `cbe7285fee4397ab4b459c314954be083dc8422a808fdd55b53a31684baa5603` |
| `reverse_agent/platform_v1/capability_registry.py` | `ee4f92455acf2b2323f8dd870c706c5d7f2aaca919f4eb5eb35d51abd103bace` |
| `frontend/src/vendor/agent-canvas-v1.6.1/agent-canvas-sidebar-frame.tsx` | `f7179931233477d47406433ed3c83a10faa4fb667662480904bdafa60ad5ce34` |
| `frontend/src/vendor/agent-canvas-v1.6.1/agent-canvas-workbench-frame.tsx` | `d2eb7a6aa77a5dae06fe7ef749fc7b3c9a78ce5c9105b3ba4849bdbc2e5bf50b` |
| `frontend/src/vendor/agent-canvas-v1.6.1/resize-handle.tsx` | `31b0a61f29300fcd7cbe425234e90f3891a1dce3ef58cfb9b279cf81ef5ef190` |
| `frontend/src/vendor/agent-canvas-v1.6.1/sidebar-collapsed-icon-slot.tsx` | `011c257efb39a3e6585f5bb446e36ff9903131f2d602d3295da05cf3eab9c9d2` |
| `frontend/src/vendor/agent-canvas-v1.6.1/sidebar-layout.ts` | `996ec414d566a54a9beb8c6629a1190a25a97a8b6d02d7d00ed4a460a7d02f8f` |

The `governance/freshness-registry.json` hash describes the pre-review bytes.
This review intentionally edits that file (`checked_at` dates and an added
evidence path), so its post-review bytes are expected to differ from that
record. No other listed file is modified by this review.

## Registry change

- `checked_at`: 2026-09-19 → 2026-10-29 for all four entries.
- This document is appended to each entry's `evidence_paths`; it contains each
  entry's `current_version` literal (1.0.10, 3.1.0, 1.6.1, compatible).
- Entry count stays at four and `max_age_days` stays at 30.

Validation (`tests/test_freshness.py`), independent review, CI and publication
are owned by the host and supervisor; this document does not claim them.
