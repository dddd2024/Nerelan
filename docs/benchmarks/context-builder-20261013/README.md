# Context Builder: frozen development trials and production follow-up

Owner requested #1151 priorities 2 and 4 on 2026-10-13 and authorized GPT/Claude
baselines, all existing B resources and no monetary ceiling. Observation and
export completed on 2026-10-14. These records grant no execution authority.

## Outcome

P0-2's production follow-up implements bounded context reconstruction over the
existing TaskStore/Git state and integrates both normal and durable execution.
The real Task API probe, after the preparation process exited, invoked the
managed GPT CLI in a separate process. Its five reported facts matched the
persisted Goal/revision/digest, live Run and exact Git head. This is real model
consumption of a reconstructed packet; it does not establish general model
utility, task-quality improvement, or a successful cost benchmark.

P0-4's measurement/acceptance infrastructure and real trials are implemented,
but **no qualifying accepted A/B pair was obtained**. There is no measured cash
saving, no qualified end-to-end cost comparison, and no claim of general savings.
P0-4 remains open for a separately frozen, independently accepted comparison.

## Trial records

All implementation workers started from
`3e841a4ff4f1582efc3abd44c1294f8a23749f44` with separate clones/databases and
received the same requirements within each round. Independent tests stayed
outside their workspaces. Production repairs were made after freezing outputs
and never replaced their verdicts.

| Round | What actually happened | Interpretation |
| --- | --- | --- |
| 1 | Windows long paths prevented worktree preparation before model dispatch. | Infrastructure failure; retained. |
| 2 | Native progress/final/usage events were rejected by the TaskStore whitelist. | Measurement failure; not a comparable baseline. |
| 3 | Claude and B's stronger implementation produced artifacts. Independent review found configured Git clean filters executed; B also failed visibility/evidence/scoping review. GPT stopped at native permission admission. | Rejected outputs; no accepted pair. |
| 4 | Restricted Windows sandbox selection restored GPT command access, but protocol processing failed. | Failed GPT attempt; retained. |
| 5 | GPT produced a testable implementation; controlled filter verification still rejected it. | Rejected output. |
| 6 | Shared requirements were clarified before new runs. GPT and B artifacts passed the calibrated basic tests but leaked excluded peer instructions in a real Goal plan. Claude encountered API 429; GLM and B's one GPT upgrade reached their bounded deadlines. | No accepted pair; no additional benchmark turns or retroactive repair. |

The final clarified round's role wall times include local preparation/transport
overhead and can exceed the model subprocess's 600-second deadline:

| Arm | Real route | Role wall time | Terminal result |
| --- | --- | --- | --- |
| A-GPT | GPT native implementation | 533.089 s | CLI completed; independent visibility/source-contract rejection. |
| A-Claude | Opus native implementation | 496.925 s | API 429; partial module. |
| B | Sonnet planner | 101.333 s | Planner completed. |
| B | GLM implementation | 618.803 s | Bounded timeout. |
| B | One GPT upgrade | 603.637 s | Bounded timeout; artifact also failed independent plan visibility. |

There are **20 startup/executor attempt records**, not 20 proven provider
requests. Physical provider request count and supervisor model usage were not
observable. Native token counters and executor-reported usage are retained in
their own definitions; incomplete counters remain unknown. Reported zero
executor cost for an unpriced model is not an actual zero invoice.

Cash cost, subscription quota remaining, human time and full coordination cost
are UNKNOWN. Native tool engines also differ, so tool equivalence is unverified.
The reducer refuses savings claims when these comparison requirements fail.
Successful artifact tests after a timeout do not turn the delivery workflow
into a successful result; its explicit delivery task must have completed.

## Independent acceptance and calibration

Original hidden evaluator errors were preserved: two fixtures used unsupported
event types, and two comparisons assumed an unspecified `changed_paths` shape.
The separate calibrated evaluator fixed those four defects, removed no semantic
assertions and added a controlled filter marker. A separate real GoalService
plan probe subsequently found the peer-content leak that basic tests missed.
Every candidate received the same applicable checks; hashes and original
verdicts remain recorded.

Windows symlink cases skipped when the OS denied creation. Some native test
scratch directories could not be enumerated. Product file hashes/scopes were
observed; scratch scope remains UNKNOWN. No ACL, ownership or cleanup change
was made to erase those limitations.

## Artifacts

- [results.json](results.json): bounded metrics, source receipt hashes, output
  hashes, independent verdicts and comparison blockers; no prompts, answers or credentials.
- [acceptance-calibration.json](acceptance-calibration.json): precise evaluator corrections and hashes.
- [live-context-restart.json](live-context-restart.json): real authenticated Task
  API/GPT follow-up on product head
  `e5c92c570bd966520d0d38c9f093a687d5d0e896`, distinct process IDs and exact fact matching.
- [Frozen original contract](../../context-cost-benchmark.md): baseline slice and initial stops.
- [Clarified round 6 contract](clarified-contract-v6.md): identical requirements delivered to all arms in that round.

The newer protocol hashes are in the results manifest. Original local runtime
records, source snapshots and diagnostic failures remain preserved separately;
none are committed as a second task database. A future cost experiment needs a
new frozen protocol/evaluator and available resources, and must account for
earlier failures and validation/coordination costs rather than select only wins.
