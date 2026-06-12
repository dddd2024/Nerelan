```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260612_training_metadata_contract_repair_v1",
  "round_id": "round_20260612_training_metadata_contract_repair_v1",
  "based_on_decision_id": "decision_20260612_training_metadata_contract_repair_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "project_state/local_reverse_training_inventory_audit.md"
  ],
  "tests_ran": [
    "pwd",
    "powershell -NoProfile -Command \"Test-Path F:\\\\reverse-agent\"",
    "git rev-parse --show-toplevel",
    "git status --short",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_local_reverse_training_status.py -q",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_state doctor --state-dir project_state --json",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state --json",
    "python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260612_training_metadata_contract_repair_v1",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state --json",
    "git status --short"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_training_inventory_audit.md",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/preflight_result.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/rounds/round_20260612_training_metadata_contract_repair_v1/codex_execution_report.md",
    "project_state/rounds/round_20260612_training_metadata_contract_repair_v1/decision_packet.md",
    "project_state/rounds/round_20260612_training_metadata_contract_repair_v1/pytest_result.txt",
    "project_state/rounds/round_20260612_training_metadata_contract_repair_v1/round_manifest.json"
  ]
}
```

# CODEX_EXECUTION_REPORT

Completed the training metadata contract repair round.

- Amended `project_state/local_reverse_training_inventory_audit.md` in the
  "Metadata Contract for Future GitHub-Safe Training Work" section:
  - Added explicit `failure_reason` field row with guidance that it must not be
    aliased to `blocked_reason`.
  - Added explicit `solver_used` field row, marked as **unknown / not
    first-class**, with a clear prohibition against inferring it from
    `known_candidate`.
  - Added explicit `tool_evidence_used` field row, mapped from richer local
    output `evidence_sources`, and noted that the compact overlay omits it.
  - Added "Distinction: `blocked_reason` vs. `failure_reason`" subsection:
    - `blocked_reason` = current forward-looking blocker.
    - `failure_reason` = historical failed path.
    - Compact overlay only exposes `blocked_reason`.
  - Added "Distinction: `known_candidate` vs. `solver_used`" subsection:
    - `known_candidate` = validated answer.
    - `solver_used` = solver family/strategy (not first-class).
    - Codex must not infer one from the other.
- Updated "Recommended Next Bounded Step" to explicitly state that this round
  does **not** execute the static triage; only a future decision may select
  exactly one queue item.
- Verified no source code, test code, solver, IDA/Ghidra/debugger, or
  `.codex-skills/` changes were made.
- Verified the existing metadata facts remain intact:
  - inventory 50 entries, all `github_upload_policy: metadata_only`.
  - status overlay: 1 solved, 2 blocked, 1 needs_triage, 46 inventory_only.
  - evaluation queue: 41 items, policy `simple_static_first_unsolved_only`,
    allows only `static_triage`, forbids `runtime_probe`, `bruteforce`,
    `upload_binary`.
- All required tests were executed and recorded with real stdout/stderr/exit
  code in `project_state/pytest_result.txt`.
- The round was archived to
  `project_state/rounds/round_20260612_training_metadata_contract_repair_v1/`.
