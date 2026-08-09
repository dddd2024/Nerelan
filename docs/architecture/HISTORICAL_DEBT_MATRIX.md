# Historical Debt Matrix — Repository Modernization V2

> Umbrella: #148  
> Baseline: `main@dd4cb074ab5b9baacf300706878b29bd745f12c3`  
> Classification is provisional until each owning phase performs an exact-code audit.

## Classification legend

- **KEEP** — current capability/problem is still valid.
- **REWRITE** — underlying need is valid, but current design/implementation assumptions are stale.
- **RETIRE** — remove from normal current architecture after replacement is proven.
- **ARCHIVE** — preserve as historical evidence only.
- **FIX** — concrete defect with a focused repair path.

## P0 — Safety / correctness

| Item | Current observation | Classification | Owner phase |
|---|---|---:|---:|
| OpenCode recursive redaction tuple/container path | recursive `result` is built, but tuple handling requires regression verification for possible raw-value return | **FIX / VERIFY** | 1A |
| Frontend real validation status fallback (#145) | `validation_exit_code=0` can still render `testStatus=PENDING` when frontend field is absent | **FIX** | 4B |
| Fixture-oriented `nextAction` on real tasks (#145) | real OpenCode task can inherit mock/provider-free wording | **FIX** | 4B |

## State / source-of-truth debt

| Item | Current observation | Classification | Owner phase |
|---|---|---:|---:|
| `project_state/decision_packet.md` | can remain a completed prior landing Decision on main | **REWRITE** | 1B |
| `project_state/mainline_merge_intents/active.json` | `active` can point at already-landed PR authority | **REWRITE** | 1B |
| legacy reverse `current_state.json` / state manifest | names imply global current truth although they belong to an older domain flow | **RETIRE from global truth / ARCHIVE** | 1B |
| generated gate artifacts in tracked state | useful audit evidence but currently intertwined with active authority semantics | **REWRITE** | 1B/2A |
| `.frontend_stage/**` / `.platform_v1_runtime/**` | long-lived local scratch leaks into governance path attribution | **REWRITE** | 1C/2B |

## Governance / policy debt

| Item | Current observation | Classification | Owner phase |
|---|---|---:|---:|
| Decision schema | required semantics distributed across parser, transition code and tests | **REWRITE** | 2A |
| #142 pre-activation Decision validation | problem valid; should become typed contract compiler validation rather than another side gate | **KEEP + REWRITE** | 2A |
| #147 baseline dirty vs current delta | problem valid and structurally important | **KEEP** | 2B |
| #143 outer Agent command-policy compatibility | problem valid; integrate into execution-surface capability validation | **KEEP + REWRITE** | 2C |
| #139 Windows background-process safety | host capability mismatch remains useful evidence but should not remain an isolated protocol family | **REWRITE / MERGE INTO 2C** | 2C |
| tests as implicit contract definition | late failures reveal fields not rejected by earlier validators | **RETIRE pattern** | 2A |

## CI / workflow debt

| Item | Current observation | Classification | Owner phase |
|---|---|---:|---:|
| permanent legacy + transition dual paths | migration logic has become normal architecture | **RETIRE after replacement** | 3A |
| historical PR-number bootstrap logic | old PR-specific exceptions remain in normal workflow code | **RETIRE** | 3A |
| duplicated Decision/Gate checks across workflows | same semantic responsibility executed in multiple places | **REWRITE** | 3A |
| duplicated pytest coverage across CI jobs | adds cost and makes failure ownership unclear | **REWRITE** | 3A |
| Git/GitHub merge mechanics reimplemented in project policy | some checks belong natively to repository rules | **REWRITE** | 3B |

## Runtime architecture debt

| Item | Current observation | Classification | Owner phase |
|---|---|---:|---:|
| Task API / TaskService | proven current foundation | **KEEP** | preserve |
| SQLite `TaskStore` | proven current foundation | **KEEP** | preserve |
| `run_store.py` filename | implementation now exposes `TaskStore`; naming reflects old RunStore architecture | **REWRITE naming if safe** | 4A |
| `ExecutorRouter` | useful current abstraction | **KEEP** | preserve |
| deterministic fixture executor | useful for tests, but should not define production defaults/worldview | **KEEP as test fixture / RECLASSIFY** | 4A |
| OpenCode executor | real executor path proven | **KEEP** | preserve + 1A safety audit |
| obsolete coordinator references in old plans | referenced files no longer represent current runtime | **ARCHIVE / REWRITE plans** | 4C |
| stale module docstrings/comments | describe fixture-only/no-database/no-frontend architecture | **FIX** | 4A/4C |

## Frontend debt

| Item | Current observation | Classification | Owner phase |
|---|---|---:|---:|
| main frontend Task API path | functional single-Agent task surface | **KEEP** | preserve |
| Agent Canvas v1.6.1 source fork in #146 | visually/runtime accepted but not landed | **KEEP as accepted branch capability** | landing bridge after 1/2 |
| broad `Record<string, unknown>` normalization | encourages fallback semantics and mock/real leakage | **REWRITE** | 4B |
| mock/provider-free defaults in real path | already produced visible status mismatch | **FIX / REWRITE** | 4B |
| second frontend state model | must not emerge while integrating Agent Canvas | **RETIRE/forbid** | invariant |

## Backlog / planning debt

| Issue | Observation | Classification | Target action |
|---|---|---:|---|
| #148 | current modernization umbrella | **KEEP** | primary modernization tracker |
| #147 | valid baseline/delta problem | **KEEP** | Phase 2B |
| #145 | valid UI truth bug | **KEEP** | Phase 4B |
| #144 | semantic artifact identity remains useful | **KEEP / fold into evidence hardening** | later Phase 2/4 |
| #143 | valid outer execution-surface mismatch | **REWRITE** | Phase 2C |
| #142 | valid preactivation validation need | **REWRITE** | Phase 2A |
| #141 | transport resilience problem may remain, but must be re-audited against new bootstrap path | **REWRITE / DEFER** | after Phase 2 |
| #139 | narrow historical symptom of execution-surface capability gap | **MERGE/SUPERSEDE** | Phase 2C |
| #138 | docs alignment goal now subsumed by modernization-wide source-of-truth rewrite | **SUPERSEDED by #148** | close after Phase 0 review |
| #137 | current mother-platform/capability direction | **KEEP** | resume after modernization core |
| #136 / PR #146 | accepted frontend product work, landing blocked by historical governance architecture | **KEEP + FREEZE** | modernization landing bridge |
| #135 | trusted Draft PR publication remains a valid missing V1 capability | **KEEP / DEFER** | resume after core landing bridge |
| #127 | real single-Agent vertical-slice parent contains historical statuses but core objective remains useful | **REWRITE/ARCHIVE status sections** | Phase 4C |
| #126 | multi-Agent compatibility research plan; not proof of product capability | **KEEP as research reference** | Phase 5 input |
| #120 | interruption/recovery problem remains valid; proposed coordinator paths are stale | **REWRITE** | reliability phase after state reset |
| #118 | future autonomous privileged window | **KEEP as future design** | post-V1/post-modernization |
| #105 | old Path-A restoration plan bound to historical PRs/main | **ARCHIVE/SUPERSEDE** | Phase 4C |
| #103 | cross-Agent context/source hierarchy remains conceptually useful; implementation status/history stale | **KEEP concepts / REWRITE status** | Phase 4C/5 |
| #90 | parent product direction still useful, but execution-state header is stale | **REWRITE** | Phase 4C |

## Branch / PR debt

| Item | Observation | Classification | Action |
|---|---|---:|---|
| Draft PR #146 | contains accepted Agent Canvas/OpenCode frontend evidence | **KEEP / FREEZE** | do not add v25/v26 patches; bridge later |
| `owner/issue136-agent-canvas-reuse-spike-v2` | product/evidence branch plus accumulated governance commits | **KEEP historical exact-head evidence** | no rebase/force rewrite |
| older governance migration branches | may contain useful experiments but are hundreds of commits stale | **ARCHIVE reference** | do not revive wholesale |
| future modernization implementation branches | must start from re-observed exact current main and be phase-scoped | **NEW CURRENT PATH** | create per phase |

## Capability truth table

| Capability | Main | Accepted branch | Planned only |
|---|---:|---:|---:|
| Task API / TaskService | YES | — | — |
| persistent TaskStore | YES | — | — |
| deterministic fixture execution | YES | — | — |
| real OpenCode linked-worktree execution | YES | — | — |
| frontend real task create/execute/readback | YES | — | — |
| Agent Canvas-derived corrected workbench | NO | YES (#146) | — |
| real task reaches READY_FOR_HUMAN through corrected workbench | NO | YES (#146 evidence) | — |
| trusted Draft PR publication controller | NO | NO | YES (#135) |
| checkpoint/resume | NO | NO | YES / rewrite (#120) |
| multi-Agent manager/worker orchestration | NO | NO | YES (#126/#137 Phase 5) |
| parallel multi-Agent task execution | NO | NO | YES |
| structured worker artifact join | NO | NO | YES |
| automatic merge/release/deploy | NO | NO | future only (#118) |

## Migration rule

A debt item may leave this matrix only when one of the following is recorded:

```text
FIXED at exact commit + regression evidence
RETIRED with replacement exact commit
ARCHIVED with authoritative replacement pointer
SUPERSEDED by explicit Issue/design
RECLASSIFIED with owner rationale
```

Simply becoming old is not sufficient.