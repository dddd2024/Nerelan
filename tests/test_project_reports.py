import json
from pathlib import Path

from reverse_agent.project_gate import (
    _generate_final_check_exit_and_audit_readiness_required_audit,
    _generate_required_audit_alignment_rework_required_audit,
    _required_audit_alignment_failures,
    _required_audit_coverage_check,
    command_plan,
)


REQUIRED_AUDIT_ALIGNMENT_QUESTIONS = [
    "Did the first five recorded commands exactly confirm `F:\\reverse-agent`, repository root, and `git status --short`?",
    "Was `startup-snapshot` the immediate sixth recorded command and the first project gate command?",
    "Was `preflight` absent before startup-snapshot?",
    "Did startup `git status --short` show no dirty `reverse_agent/` or `tests/` files?",
    "Did `startup_snapshot.source_test_clean_start` match the actual startup source/test dirtiness?",
    "Does final-check block SUCCESS/ACCEPTED when startup source/test is dirty?",
    "Does final-check block SUCCESS/ACCEPTED when preflight or any gate appears before startup-snapshot?",
    "Is decision metadata valid: APPROVED, engineering_branch, active `reverse-agent-iteration@v2`?",
    "Did Codex treat `decision_packet.md` as authority and `task_packet.json` as background only?",
    "Did this round repair the previous Required Audit answer misalignment rather than only reporting generic pass status?",
    "Does report taxonomy include generated/updated, referenced, historical_nonblocking, and archived artifacts or equivalent fields?",
    "Are `phase1_completion_result.json`, `policy_impact_audit.json`, `policy_lint_result.json`, `state_hygiene_inventory.json`, `audit_inventory_result.json`, and `naming_migration_plan.json` excluded from generated/generated_or_updated unless actually regenerated in this round with current IDs?",
    "Does report-summary synthesis validate taxonomy and report no diffs?",
    "Does final-check detect stale/historical-only artifacts being placed in generated/current artifact lists?",
    "Does final-check or report-summary detect Required Audit placeholder/template/misaligned answers?",
    "Are Required Audit answers in `codex_execution_report.md` directly aligned with their question and evidence?",
    "Was `tests/test_project_reports.py` included in the focused pytest command recorded in `pytest_result.txt`?",
    "Did focused pytest exit 0 and include report/alignment tests?",
    "Are existing dry-run, handoff bundle, and replay validation artifacts still current, local, non-executing, and non-dispatching if regenerated this round?",
    "Did the rework avoid adding any new real runner, dispatch, external invocation, model API, Web/API/DB/queue/scheduler, GitHub Actions mutation, runtime probe, or reverse-solving capability?",
    "Did the implementation stay within allowed source/test files?",
    "Were preserve-only and forbidden files not modified?",
    "Did required top-level commands exit with expected codes, with pass/fail counts recorded in `pytest_result.txt`?",
    "Did `report_summary_fields_match_synthesis` pass with no diffs?",
    "Did `execute_decision_contract` pass?",
    "Did `execution_log` provenance remain current-round aligned?",
    "Did `run-closeout` exit 0 with `closeout_status: PASSED` and close-round `CLOSED`?",
    "Did final-check pass after archive/closeout, not only before archive?",
    "If any internal final-check command exits `1` while status is treated as PASSED, is the expected-exit and non-blocking semantics explicitly documented and validated?",
    "Did `closeout_nested_failures_absent` pass?",
    "Does `codex_report_summary` match `pytest_result.txt`, artifact taxonomy, generated/updated artifacts, changed files, decision ID, and round ID?",
]


def _decision_text() -> str:
    return (
        "# Decision\n\n"
        "decision_20260630_required_audit_alignment_rework_v1 required_audit_alignment_rework\n\n"
        "## Required Audit\n\n"
        + "\n".join(
            f"{index}. {question}"
            for index, question in enumerate(REQUIRED_AUDIT_ALIGNMENT_QUESTIONS, start=1)
        )
    )


def test_required_audit_alignment_rework_generator_is_substantive() -> None:
    decision_text = _decision_text()
    audit = _generate_required_audit_alignment_rework_required_audit(decision_text)
    result = _required_audit_coverage_check(
        decision_text=decision_text,
        report_text="# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + audit,
        report_status="SUCCESS",
    )

    assert audit.count("### ") == 31
    assert result["status"] == "PASS"
    assert result["alignment_failures"] == []
    assert result["placeholder_answers"] == []


def test_required_audit_rejects_rotated_evidence_templates() -> None:
    questions = [
        "Did startup `git status --short` show no dirty `reverse_agent/` or `tests/` files?",
        "Does report taxonomy include generated/updated, referenced, historical_nonblocking, and archived artifacts or equivalent fields?",
        "Are Required Audit answers in `codex_execution_report.md` directly aligned with their question and evidence?",
    ]
    section = """### 1. Did startup `git status --short` show no dirty `reverse_agent/` or `tests/` files?

- Evidence: project_state/gates/report_summary_synthesis.json generated_or_updated and historical_nonblocking fields.
- Status: PASS
- Answer: Startup was clean.

### 2. Does report taxonomy include generated/updated, referenced, historical_nonblocking, and archived artifacts or equivalent fields?

- Evidence: project_state/decision_packet.md decision_meta and project_state/task_packet.json background role.
- Status: PASS
- Answer: Taxonomy is present.

### 3. Are Required Audit answers in `codex_execution_report.md` directly aligned with their question and evidence?

- Evidence: project_state/gates/run_closeout_result.json closeout_status and final_gate_result.json gate_status.
- Status: PASS
- Answer: Required Audit answers are aligned.
"""

    failures = _required_audit_alignment_failures(questions, section)

    assert [failure["reason"] for failure in failures].count("evidence_domain_mismatch") >= 3


def test_command_plan_keeps_required_project_reports_pytest(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    decision = {
        "schema_version": 1,
        "decision_id": "decision_reports_pytest",
        "round_id": "round_reports_pytest",
        "status": "APPROVED",
        "mainline": "engineering_branch",
    }
    contract = {"accepted_requires_tests_project_reports_py": True}
    command = (
        "python -m pytest tests/test_project_gate.py tests/test_project_reports.py "
        "tests/test_project_agent_runner.py tests/test_project_control_plane.py "
        "tests/test_project_state.py -q"
    )
    (state_dir / "decision_packet.md").write_text(
        "```json decision_meta\n"
        + json.dumps(decision)
        + "\n```\n\n"
        + "```json decision_contract\n"
        + json.dumps(contract)
        + "\n```\n\n"
        + "# Decision\n\n## 7. Tests\n\n```powershell\n"
        + command
        + "\n```\n",
        encoding="utf-8",
    )

    result = command_plan(state_dir=state_dir, write_result=False)
    commands = [entry["command"] for entry in result["commands"]]

    assert result["plan_status"] == "PASSED"
    assert command in commands


def test_final_check_exit_audit_generator_uses_dirty_startup_negative_evidence() -> None:
    decision_text = Path("project_state/decision_packet.md").read_text(encoding="utf-8")

    audit = _generate_final_check_exit_and_audit_readiness_required_audit(decision_text)
    item_6 = audit.split("### 6.", 1)[1].split("### 7.", 1)[0]
    result = _required_audit_coverage_check(
        decision_text=decision_text,
        report_text="# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + audit,
        report_status="SUCCESS",
    )

    assert audit.count("### ") == 28
    assert "dirty startup regression" in item_6
    assert "negative regression" in item_6
    assert "live clean startup alone" in item_6
    assert result["status"] == "PASS"
