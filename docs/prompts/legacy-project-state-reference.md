# Explicit legacy project-state contract

Conditional compatibility reference, not a default startup prompt or new authority. Use only when the active task selects the project-state report/round contract and explicitly grants the relevant reads, writes and operations. Current [AGENTS.md](../../AGENTS.md) and the applicable authority path prevail over historical prompt wording.

## State and scope

For a Decision-driven round, resolve the APPROVED immutable Decision before suggested tasks. `task_packet.task` and `derived_task` are background, not replacements for the Decision. Read `current_state`, the current artifact index and applicable negative results only as needed; reports and test results are evidence, not authorization. Do not treat engineering/reverse-solving as the universal current product model or infer permission for sample execution.

Use the currently selected transition kernel and generated plan for Path B. Older `preflight`/`command-plan` recipes are historical and must not override it. Commands in an omitted list are not authorized. A conflicting prose test section does not grant a command excluded by the generated plan; report the conflict rather than widening scope.

## Reports and closeout

Only when their paths and writes are explicitly authorized:

- `project_state/pytest_result.txt` records Decision/round identity, actual test commands, stdout, stderr, exit code and conclusion.
- `project_state/codex_execution_report.md` contains the required `codex_report_summary` fenced JSON, linkage, changed files/artifacts, actual checks, recommendation and limitations.

The summary status is `SUCCESS`, `PARTIAL`, `FAILED` or `BLOCKED`; do not use `COMPLETED_WITH_LIMITATIONS` as that JSON status. A human-facing conclusion may use `COMPLETED`, `COMPLETED_WITH_LIMITATIONS`, `REWORK_REQUIRED` or `BLOCKED` where the active report schema calls for it. Neither format grants acceptance or landing permission.

Run closeout only when the generated plan authorizes it. If authorized closeout runs, rerun the required report-summary/final-check steps afterward. Preserve the report fields the active contract actually requires, including directory/surface, Decision/round, changed/generated paths, commands/results, report status, applicable path checks, Git status/diff and conclusion. Do not force twelve legacy fields onto every ordinary R1 response.

Valid legacy profile names are `fast`, `standard` and `full`, not `medium`. Discover the actual authorized repository root; no particular Windows drive is required. Preserve/classify existing work with current worktree guards rather than demanding every untracked runtime file disappear. Remote mutations always need the applicable current authority; this reference itself authorizes none.
