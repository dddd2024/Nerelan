import json
from pathlib import Path

from reverse_agent.project_gate import (
    _generate_ci_run_evidence_and_local_ci_parity_required_audit,
    _generate_ci_workflow_coverage_required_audit,
    _generate_ci_workflow_readiness_required_audit,
    _generate_current_handoff_packet_required_audit,
    _generate_final_check_exit_and_audit_readiness_required_audit,
    _generate_local_execution_loop_required_audit,
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

CURRENT_HANDOFF_PACKET_QUESTIONS = [
    "Did startup commands confirm `F:\\reverse-agent`, repo root, and clean `git status --short` before any project gate?",
    "Was `startup-snapshot` still the immediate sixth command and first project gate?",
    "Did `decision_meta` remain valid and APPROVED on `engineering_branch`?",
    "Did `reverse-agent-iteration@v2` remain active in `.codex-skills/registry.json`?",
    "Did Codex treat `decision_packet.md` as authority and `task_packet.json` as background only?",
    "Did implementation stay within allowed source/test files?",
    "Were preserve-only and forbidden files not modified?",
    "Did Codex inspect existing handoff/runner artifacts or code before adding the current handoff packet?",
    "Did implementation avoid creating a new runner, dispatcher, scheduler, queue, service, Web/API layer, CI workflow, or external integration?",
    "Does `current_handoff_packet.json` exist with current decision ID, round ID, and report ID?",
    "Does the handoff packet identify `decision_packet.md` as the decision authority?",
    "Does the handoff packet identify `command_plan.json` as the command execution authority?",
    "Does the handoff packet include the required startup sequence and startup-snapshot-first rule?",
    "Does the handoff packet summarize allowed source/test paths and forbidden paths from the decision contract?",
    "Does the handoff packet summarize required tests and the pytest command including `tests/test_project_reports.py`?",
    "Does the handoff packet include expected generated artifacts and artifact freshness policy?",
    "Does the handoff packet summarize current `audit_inventory_result.json` status?",
    "Does the handoff packet summarize current `audit_readiness_packet.json` status?",
    "Does the handoff packet summarize closeout expectations and stop conditions?",
    "Is the handoff packet evidence-only, non-dispatching, non-executable, and non-mutating?",
    "Does final-check validate handoff packet freshness, evidence-only fields, and command-plan alignment?",
    "Does final-check reject stale handoff packet IDs when current handoff is required?",
    "Does final-check reject a handoff packet that claims authority over command-plan or omits command-plan authority?",
    "Did command-plan include the handoff packet gate and preserve explicit `execution_order_policy`?",
    "Did audit inventory remain current and validated?",
    "Did audit readiness remain `READY`, `PASSED`, and `no_action_required`?",
    "Did report-summary synthesis pass with no diffs?",
    "Did final report summary match pytest, changed files, generated artifacts, decision ID, round ID, current handoff status, audit inventory status, and audit readiness status?",
]

LOCAL_EXECUTION_LOOP_QUESTIONS = [
    "Did startup commands confirm `F:\\reverse-agent`, repo root, and clean `git status --short` before any project gate?",
    "Was `startup-snapshot` still the immediate sixth command and first project gate?",
    "Did `decision_meta` remain valid and APPROVED on `engineering_branch`?",
    "Did `reverse-agent-iteration@v2` remain active in `.codex-skills/registry.json`?",
    "Did Codex treat `decision_packet.md` as authority and `task_packet.json` as background only?",
    "Did implementation stay within allowed source/test files?",
    "Were preserve-only and forbidden files not modified?",
    "Did implementation avoid creating a runner, dispatcher, scheduler, service, Web/API layer, CI workflow, queue, database, external integration, API caller, or remote automation?",
    "Did Codex inspect the current handoff, command-plan, audit inventory, audit readiness, final-check, and closeout artifacts before implementing the bundle?",
    "Does `local_execution_bundle.json` exist with current decision ID, round ID, and report ID?",
    "Does the bundle declare `decision_packet.md` as the decision authority and `task_packet.json` as background only?",
    "Does the bundle declare `command_plan.json` as the only command execution authority?",
    "Does the bundle include startup contract and startup-snapshot-first rule?",
    "Does the bundle include allowed scope, forbidden scope, required tests, required artifacts, report update requirements, and stop conditions?",
    "Does the bundle reference `current_handoff_packet.json` and `codex_prompt_packet.json`?",
    "Is the bundle evidence-only, non-executable, non-dispatching, and non-mutating?",
    "Does `codex_prompt_packet.json` exist with current decision ID, round ID, and report ID?",
    "Is the prompt packet derived from current `local_execution_bundle.json` and current `current_handoff_packet.json`?",
    "Does the prompt packet include a complete copyable prompt or structured prompt sections?",
    "Does the prompt preserve `F:\\reverse-agent`, startup checks, decision authority, task_packet background status, command-plan authority, allowed scope, forbidden scope, required tests, pytest_result writing, codex_execution_report writing, and no-push/no-commit rules?",
    "Does `audit_precheck_result.json` exist with current decision ID, round ID, and report ID?",
    "Does audit precheck validate report/decision/round matching, pytest_result presence, pytest command coverage, final-check status, run-closeout status, close-round status, audit readiness, current handoff, local execution bundle, and prompt packet status?",
    "Does audit precheck return `READY_FOR_GPT_AUDIT` only when required evidence is present and aligned?",
    "Does audit precheck return `DO_NOT_ACCEPT` or equivalent blocking state when report, pytest, ID alignment, final-check, closeout, readiness, bundle, or prompt packet evidence is missing or failed?",
    "Does final-check validate local execution bundle freshness and evidence-only fields?",
    "Does final-check validate prompt packet freshness and derivation from the current bundle/handoff?",
    "Does final-check validate audit precheck status and recommendation?",
    "Did final report summary match pytest, changed files, generated artifacts, decision ID, round ID, current handoff status, local execution bundle status, prompt packet status, audit precheck status, audit inventory status, and audit readiness status?",
]

CI_WORKFLOW_COVERAGE_QUESTIONS = [
    "Did startup commands confirm `F:\\reverse-agent`, repository root, and clean `git status --short` before any project gate?",
    "Was `startup-snapshot` the immediate sixth recorded command and the first project gate command?",
    "Did `decision_meta` remain APPROVED on engineering_branch with `reverse-agent-iteration@v2` active?",
    "Did Codex treat `decision_packet.md` as authority and `task_packet.json` as background only?",
    "Were `.github/workflows/ci.yml` and `.github/workflows/state-gate.yml` inspected read-only without modification?",
    "Was `project_state/gates/ci_workflow_coverage_result.json` generated with the current decision ID, round ID, and report ID?",
    "What workflow coverage is present or missing for baseline pytest, `tests/test_project_reports.py`, preflight, command-plan, local-execution-bundle, codex-prompt-packet, audit-precheck, report-summary, execution-log, and final-check?",
    "Were unsafe workflow capabilities checked and were any unsafe patterns found?",
    "Do regression tests fail or report missing required coverage in a synthetic workflow?",
    "Do regression tests fail or report unsafe synthetic workflow patterns?",
    "Did implementation stay within allowed source and test files?",
    "Were forbidden and preserve-only files not modified?",
    "Does the local execution bundle remain current, evidence-only, non-executable, non-dispatching, and non-mutating?",
    "Does the Codex prompt packet remain current and non-executable?",
    "Does audit precheck preserve READY_FOR_GPT_AUDIT and DO_NOT_ACCEPT semantics?",
    "Does report-summary match pytest output, changed files, generated artifacts, and workflow coverage artifact status?",
    "Does execution-log align command-plan and pytest_result without omitting executed top-level commands?",
    "Did final-check pass with the CI workflow coverage artifact validated?",
    "Did run-closeout pass, close-round become CLOSED, and post-closeout final-check pass?",
    "Does the report state workflow files were not modified and coverage gaps are future-decision planning evidence?",
]

CI_WORKFLOW_READINESS_QUESTIONS = [
    "Were startup commands recorded before project gates?",
    "Was startup-snapshot the first project gate?",
    "Did decision metadata remain valid and approved?",
    "Was this decision treated as current authority?",
    "Was the narrower uploaded decision treated as superseded?",
    "Were changes limited to allowed workflow/source/test/artifact files?",
    "Do the workflow files cover the previous missing coverage items?",
    "Is `decision-preflight.yml` included in the readiness review?",
    "Is `ci_workflow_coverage_result.json` current and complete?",
    "Is `ci_workflow_readiness_result.json` current and complete?",
    "Did workflow validation tests cover omitted required snippets?",
    "Did workflow validation tests cover policy-disallowed workflow patterns?",
    "Did local execution bundle remain valid?",
    "Did codex prompt packet remain valid?",
    "Did audit precheck remain valid?",
    "Did audit readiness remain ready and accepted?",
    "Did report-summary include workflow coverage and readiness status?",
    "Did execution-log align with command-plan and pytest_result?",
    "Did final-check pass?",
    "Did run-closeout pass and close-round close?",
    "Did the report clearly state that the round stayed within CI validation infrastructure?",
]

CI_RUN_EVIDENCE_PARITY_QUESTIONS = [
    "Were startup commands recorded before project gates?",
    "Was startup-snapshot the first project gate?",
    "Did decision metadata remain valid and approved?",
    "Was this decision treated as current authority and `task_packet.json` as background only?",
    "Were changes limited to allowed workflow/source/test/artifact files?",
    "Was `ci_run_evidence_result.json` generated with current decision ID, round ID, and report ID?",
    "Does `ci_run_evidence_result.json` clearly state whether CI run evidence was observed, not observed, or supplied as bounded input?",
    "Is `ci_run_evidence_result.json` evidence-only and non-dispatching?",
    "Was `local_ci_parity_result.json` generated with current decision ID, round ID, and report ID?",
    "Does `local_ci_parity_result.json` compare workflow commands against command-plan, pytest_result, and execution-log evidence?",
    "Does `local_ci_parity_result.json` report no required parity gaps for this round, or clearly classify any nonblocking future live-CI observation gap?",
    "Did `ci_workflow_coverage_result.json` remain current and complete?",
    "Did `ci_workflow_readiness_result.json` remain current and READY?",
    "Did workflow validation tests cover omitted parity inputs and omitted run evidence fields?",
    "Did local execution bundle remain valid?",
    "Did codex prompt packet remain valid?",
    "Did audit precheck remain valid?",
    "Did audit readiness remain ready and accepted?",
    "Did report-summary include CI run evidence and local-CI parity status?",
    "Did execution-log align with command-plan and pytest_result?",
    "Did final-check pass?",
    "Did run-closeout pass and close-round close?",
    "Did the report clearly state that this round stayed within CI evidence/parity infrastructure?",
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


def test_current_handoff_packet_required_audit_generator_is_substantive() -> None:
    decision_text = (
        "# Decision\n\n"
        "current_handoff_packet current-handoff-packet\n\n"
        "## Required Audit\n\n"
        + "\n".join(
            f"{index}. {question}"
            for index, question in enumerate(CURRENT_HANDOFF_PACKET_QUESTIONS, start=1)
        )
    )
    audit = _generate_current_handoff_packet_required_audit(decision_text)
    result = _required_audit_coverage_check(
        decision_text=decision_text,
        report_text="# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + audit,
        report_status="SUCCESS",
    )

    assert audit.count("### ") == 28
    assert "(to be filled)" not in audit
    assert "project_state/gates/current_handoff_packet.json" in audit
    assert result["status"] == "PASS"
    assert result["alignment_failures"] == []
    assert result["placeholder_answers"] == []


def test_local_execution_loop_required_audit_generator_is_substantive() -> None:
    decision_text = (
        "# Decision\n\n"
        "local execution loop local_execution_bundle.json codex_prompt_packet.json audit_precheck_result.json\n\n"
        "## Required Audit\n\n"
        + "\n".join(
            f"{index}. {question}"
            for index, question in enumerate(LOCAL_EXECUTION_LOOP_QUESTIONS, start=1)
        )
    )
    audit = _generate_local_execution_loop_required_audit(decision_text)
    result = _required_audit_coverage_check(
        decision_text=decision_text,
        report_text="# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + audit,
        report_status="SUCCESS",
    )

    assert audit.count("### ") == 28
    assert "(to be filled)" not in audit
    assert "project_state/gates/local_execution_bundle.json" in audit
    assert "project_state/gates/codex_prompt_packet.json" in audit
    assert "project_state/gates/audit_precheck_result.json" in audit
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
    questions = [f"Placeholder final-check exit policy audit item {index}?" for index in range(1, 29)]
    questions[5] = "Did the implementation stay within allowed source/test files?"
    decision_text = (
        "# Decision\n\n"
        "final_check_exit_and_audit_readiness accepted_requires_audit_readiness_packet\n\n"
        "## Required Audit\n\n"
        + "\n".join(f"{index}. {question}" for index, question in enumerate(questions, start=1))
    )

    audit = _generate_final_check_exit_and_audit_readiness_required_audit(decision_text)
    item_6 = audit.split("### 6.", 1)[1].split("### 7.", 1)[0]
    result = _required_audit_coverage_check(
        decision_text=decision_text,
        report_text="# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + audit,
        report_status="SUCCESS",
    )

    assert audit.count("### ") == 28
    if "Does final-check block SUCCESS/ACCEPTED when startup source/test is dirty?" in decision_text:
        assert "dirty startup regression" in item_6
        assert "negative regression" in item_6
        assert "live clean startup alone" in item_6
    else:
        assert "Did the implementation stay within allowed source/test files?" in item_6
    assert result["status"] == "PASS"


def test_ci_workflow_coverage_required_audit_generator_is_substantive() -> None:
    decision_text = (
        "# Decision\n\n"
        "ci workflow coverage ci_workflow_coverage_result.json "
        "accepted_requires_ci_workflow_coverage_artifact "
        "accepted_requires_workflow_static_validation_tests "
        "accepted_requires_existing_workflows_read_only\n\n"
        "## Required Audit\n\n"
        + "\n".join(
            f"{index}. {question}"
            for index, question in enumerate(CI_WORKFLOW_COVERAGE_QUESTIONS, start=1)
        )
    )

    audit = _generate_ci_workflow_coverage_required_audit(decision_text)
    result = _required_audit_coverage_check(
        decision_text=decision_text,
        report_text="# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + audit,
        report_status="SUCCESS",
    )

    assert audit.count("### ") == len(CI_WORKFLOW_COVERAGE_QUESTIONS)
    assert "(to be filled)" not in audit
    assert "project_state/gates/ci_workflow_coverage_result.json" in audit
    assert ".github/workflows/ci.yml" in audit
    assert ".github/workflows/state-gate.yml" in audit
    assert "WORKFLOW_UPDATE_RECOMMENDED" in audit or "coverage gaps" in audit
    assert result["status"] == "PASS"


def test_ci_workflow_readiness_required_audit_generator_is_substantive() -> None:
    decision_text = (
        "# Decision\n\n"
        "ci workflow readiness ci_workflow_readiness_result.json "
        "ci_workflow_coverage_result.json\n\n"
        "## Required Audit\n\n"
        + "\n".join(
            f"{index}. {question}"
            for index, question in enumerate(CI_WORKFLOW_READINESS_QUESTIONS, start=1)
        )
    )

    audit = _generate_ci_workflow_readiness_required_audit(decision_text)
    result = _required_audit_coverage_check(
        decision_text=decision_text,
        report_text="# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + audit,
        report_status="SUCCESS",
    )

    assert audit.count("### ") == len(CI_WORKFLOW_READINESS_QUESTIONS)
    assert "(to be filled)" not in audit
    assert "project_state/gates/ci_workflow_readiness_result.json" in audit
    assert ".github/workflows/decision-preflight.yml" in audit
    assert "bounded CI validation infrastructure" in audit
    assert result["status"] == "PASS"


def test_ci_run_evidence_and_local_ci_parity_required_audit_generator_is_substantive() -> None:
    decision_text = (
        "# Decision\n\n"
        "ci-run-evidence local-ci-parity ci_run_evidence_result.json local_ci_parity_result.json "
        "accepted_requires_ci_run_evidence_artifact accepted_requires_local_ci_parity_artifact\n\n"
        "## Required Audit\n\n"
        + "\n".join(
            f"{index}. {question}"
            for index, question in enumerate(CI_RUN_EVIDENCE_PARITY_QUESTIONS, start=1)
        )
    )

    audit = _generate_ci_run_evidence_and_local_ci_parity_required_audit(decision_text)
    result = _required_audit_coverage_check(
        decision_text=decision_text,
        report_text="# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + audit,
        report_status="SUCCESS",
    )

    assert audit.count("### ") == len(CI_RUN_EVIDENCE_PARITY_QUESTIONS)
    assert "(to be filled)" not in audit
    assert "project_state/gates/ci_run_evidence_result.json" in audit
    assert "project_state/gates/local_ci_parity_result.json" in audit
    assert "NOT_OBSERVED" in audit
    assert "bounded CI evidence/parity infrastructure" in audit
    assert result["status"] == "PASS"
