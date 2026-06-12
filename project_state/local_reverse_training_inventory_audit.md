# Local Reverse Training Inventory Audit

## Scope

Decision: `decision_20260612_training_local_reverse_inventory_audit_v1`

Round: `round_20260612_training_local_reverse_inventory_audit_v1`

This audit is metadata-only. It does not execute local samples, run solver
candidate generation, run runtime probes, upload binaries, read bulk
`solve_reports/`, or treat stale project_state facts as current training
evidence.

## Files Inspected

- `reverse_agent/local_reverse_inventory.py`
- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- `reverse_agent/tool_runners.py`
- `tests/test_local_reverse_training_status.py`
- `training_materials/local_reverse/inventory.json`
- `training_materials/local_reverse/status_overlay.json`
- `project_state/local_reverse_evaluation_queue.json`
- Project gates and current status files under `project_state/`

## Current Inventory Facts

- `training_materials/local_reverse/inventory.json` contains 50 metadata entries.
- All 50 entries use `github_upload_policy: metadata_only`.
- Guessed file type distribution: 42 `pe`, 7 `python`, 1 `text`.
- Category distribution: 28 `cpp`, 12 `unknown`, 9 `crypto/cipher`, 1 `crypto/hash`.
- The inventory records include stable metadata such as `sample_id`,
  `display_name`, `relative_path`, `sha256`, `size_bytes`, `extension`,
  `guessed_file_type`, `category`, `tags`, `status`, and
  `github_upload_policy`.
- The inventory is a metadata mirror of local material. Raw samples remain
  outside the repository and are referenced through `LOCAL_REVERSE_ROOT`.

## Current Training Status Overlay

`training_materials/local_reverse/status_overlay.json` reports:

| Status | Count |
| --- | ---: |
| `solved` | 1 |
| `blocked` | 2 |
| `needs_triage` | 1 |
| `inventory_only` | 46 |
| Total | 50 |

Non-inventory-only records:

| sample_id | status | evidence summary |
| --- | --- | --- |
| `cpp1_bcbd9979` | `solved` | Known candidate `hookapi`. |
| `cpp2_4c69f173` | `blocked` | `MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005`. |
| `sha_256_18019fca` | `blocked` | `NO_BOUNDED_HASH_PREIMAGE_DOMAIN`. |
| `affine_8cfebe03` | `needs_triage` | Static tool failure: `STATIC_TOOL_NO_OUTPUT: IDA produced no evidence JSON`. |

The overlay is intentionally compact for GitHub: it keeps sample IDs,
relative paths, categories, tags, training status, known candidate when
already validated, and blocked reasons. It does not include raw sample bytes.

## Status Builder Contract

`reverse_agent/local_reverse_training_status.py` merges inventory with existing
evidence sources:

- validated candidate handoff facts from
  `project_state/local_reverse_validated_candidate_handoff.json`;
- blocked/solved constraint facts from
  `project_state/local_reverse_constraint_recovery_result.json`;
- prior IDA solver classifications from
  `project_state/local_reverse_ida_solver_result.json`;
- current runtime validation, runtime blocked, mature backend blocked, static
  handoff, and static tool blocked overlays from
  `project_state/artifact_index.json`.

The module explicitly does not upload original samples, run solvers, run
dynamic analysis, generate candidates, or create a second corpus scanner. Its
output surface is metadata: local training status, evaluation queue, and the
GitHub-safe status overlay.

## Evaluation Queue Contract

`project_state/local_reverse_evaluation_queue.json` currently contains 41
items under queue policy `simple_static_first_unsolved_only`.

Queue construction:

- excludes `solved` and `blocked` samples;
- includes only `inventory_only` samples;
- skips obvious solver/support material by sample ID or relative path terms
  such as `solver`, `script`, `decrypt`, `encrypt`, and `interactive`;
- ranks simple static tags first, crypto ciphers second, deferred tags later,
  and otherwise sorts deterministically by sample ID;
- permits only `static_triage`;
- forbids `runtime_probe`, `bruteforce`, and `upload_binary`.

This means the next operational step after this audit should select exactly
one queue item for static triage, not start a broad solver/runtime campaign.

## Static Triage and Tool Capability Surface

`reverse_agent/local_reverse_single_sample_static_triage.py` is the current
single-sample adapter. It locates a sample through the queue/inventory and
`LOCAL_REVERSE_ROOT`, then reuses the existing IDA evidence collector path via
`reverse_agent.tool_runners._resolve_ida_executable` and
`reverse_agent.tool_runners._resolve_ida_script`.

Relevant capability facts:

- The default IDA script path is
  `reverse_agent/ida_scripts/collect_evidence.py`.
- Existing OllyDbg collection/probe scripts also exist under
  `reverse_agent/olly_scripts/`, but they are outside this metadata-only
  audit's execution scope.
- Static triage does not execute the target binary and does not generate
  candidates.
- On unavailable tools, timeout, parse failure, or missing evidence output, it
  emits a blocked metadata artifact instead of promoting the sample to solved.
- `tool_runners.py` can parse static strings, comparison contexts, validation
  function candidates, and solver hints from IDA evidence, but those are
  evidence records, not proof of a runtime-valid candidate.

## Metadata Contract for Future GitHub-Safe Training Work

The current contract is sufficient for inventory and status visibility, but
future training rounds should make the following fields explicit whenever they
are known:

| Field | Current source | Current state |
| --- | --- | --- |
| `sample_id` | inventory | Present for all entries. |
| `display_name` | inventory | Present for inventory entries. |
| `relative_path` | inventory/status overlay | Present; may include local course directory names. |
| `sha256` | inventory | Present in inventory; excluded from compact overlay. |
| `size_bytes` | inventory | Present in inventory; excluded from compact overlay. |
| `extension` | inventory | Present in inventory; excluded from compact overlay. |
| `guessed_file_type` | inventory heuristics | Present, but heuristic. |
| `platform` | not first-class | Unknown unless inferred externally. |
| `architecture` | not first-class | Unknown unless static tooling records it. |
| `category` | inventory heuristics | Present, but broad. |
| `tags` | inventory heuristics | Present; should remain non-sensitive metadata. |
| `training_status` | status overlay | Present for all overlay samples. |
| `known_candidate` | solved overlays only | Present only when already validated. |
| `blocked_reason` | blocked/static tool overlays | Present when applicable. |
| `failure_reason` | runtime/blocked artifacts | Present in richer local output when a prior attempt produced a non-blocking failure (e.g., `AMBIGUOUS_OUTPUT`, `VALIDATED_FAILURE`). Must not be aliased to `blocked_reason`; see distinction below. |
| `classification` | local training status only | Present in richer local output, absent from compact overlay. |
| `evidence_sources` | local training status only | Present in richer local output, absent from compact overlay. |
| `solver_used` | not first-class | **Unknown / not first-class** in the compact GitHub overlay. The overlay records `known_candidate` only when a candidate has already been validated; it does **not** record which solver family or search strategy produced it. Richer local output may contain `solver_profile_hypotheses` from static triage, but these are hypotheses, not confirmed `solver_used`. Codex must not infer `solver_used` from `known_candidate`. |
| `tool_evidence_used` | local training status / artifact_index | Present in richer local output as `evidence_sources` (e.g., `ida_solver_classification`, `runtime_validation`, `static_handoff`, `source:artifact_index.json`). The compact overlay omits this list. Future contract references should use the field name `tool_evidence_used` and map it from `evidence_sources` when available. |
| `expected_input` / `expected_output` | not first-class | Unknown for most inventory-only samples. |
| `run_history` | artifact_index-derived | Partial and should not be inferred from stale artifacts. |
| `github_upload_policy` | inventory | Present and currently `metadata_only` for all entries. |

### Distinction: `blocked_reason` vs. `failure_reason`

- `blocked_reason` describes the **current blocker** that prevents further progress on a sample (e.g., `MISSING_UPSTREAM_TRANSFORM_FUNCTION`, `NO_BOUNDED_HASH_PREIMAGE_DOMAIN`, `STATIC_TOOL_NO_OUTPUT`). It is a forward-looking statement: "we cannot proceed because X."
- `failure_reason` describes a **historical failed path** that was attempted but did not succeed (e.g., `AMBIGUOUS_OUTPUT` from a runtime validation, `VALIDATED_FAILURE` from a candidate check). It is a backward-looking statement: "we tried Y and it failed."
- The compact overlay only exposes `blocked_reason`. Richer local output may contain both fields via runtime validation artifacts. Codex must not conflate them or write a `blocked_reason` when the intent is `failure_reason`.

### Distinction: `known_candidate` vs. `solver_used`

- `known_candidate` is a **validated answer or flag** that has passed runtime or manual confirmation. It is output-level metadata.
- `solver_used` would be the **solver family, strategy, or tool chain** that produced the candidate (e.g., `compare_aware_search`, `xor_array_static_solver`, `IDA_decompile_guided`). This is **not** a first-class field in the current compact overlay or status builder.
- Codex must not infer `solver_used` from `known_candidate`. If a future round needs `solver_used`, it must be introduced as a new first-class field with explicit provenance tracking, not backfilled from existing candidate values.

## Gaps and Risks

- `platform` and `architecture` are not first-class fields in the current
  GitHub-safe inventory/status overlay.
- `guessed_file_type`, `category`, and tags are heuristic and should not be
  treated as confirmed reverse-engineering findings.
- Expected input/output contracts are mostly unknown for `inventory_only`
  samples.
- The compact GitHub overlay omits richer local-only fields such as
  `classification`, `evidence_sources`, and queue rank.
- Stale runtime or solver artifacts can exist in `project_state/`; current
  training evidence must flow through the current overlay/build functions.
- Existing static tool failure on `affine_8cfebe03` is a tool/output failure,
  not a semantic proof that the sample is unsolvable.

## Recommended Next Bounded Step

1. Keep the GitHub-safe contract metadata-only.
2. If metadata is stale, refresh inventory/status using the existing builders
   without adding new scanners or uploading samples.
3. After this contract repair is accepted, the next operational decision may
   select **exactly one** queue item from
   `project_state/local_reverse_evaluation_queue.json` and run only static
   triage. **This round does not execute that triage.**
4. Record any static triage result as metadata, preserving blocked/tool-failure
   status when evidence is incomplete.
5. Defer solver generation, runtime validation, brute force, and binary upload
   until a later decision explicitly authorizes them.
