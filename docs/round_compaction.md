# Round Compaction Dry-Run

Round compaction in this project is first represented as a dry-run plan. The current implementation selects only bounded known rounds from the current decision contract and current round metadata. It does not recursively scan all historical rounds.

Dry-run output describes what a future compaction decision would retain, summarize, reference, or reject. It does not write archives, move files, delete files, compress files, or mutate `project_state/archives/`.

Primary outputs:

- `project_state/gates/round_compaction_plan.json`
- `project_state/gates/round_compaction_dry_run.json`
- `project_state/gates/round_compaction_manifest_dry_run.json`

