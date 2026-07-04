import json
from pathlib import Path

from reverse_agent.project_gate import (
    _generate_ci_run_evidence_and_local_ci_parity_required_audit,
    _generate_ci_observation_bridge_required_audit,
    _generate_ci_workflow_coverage_required_audit,
    _generate_ci_workflow_readiness_required_audit,
    _generate_current_handoff_packet_required_audit,
    _generate_final_check_exit_and_audit_readiness_required_audit,
    _generate_local_execution_loop_required_audit,
    _generate_required_audit_direct_evidence_rework_required_audit,
    _generate_required_audit_alignment_rework_required_audit,
    _generate_user_solve_control_plane_required_audit,
    _generate_user_solve_local_frontend_mvp_required_audit,
    _generate_user_solve_workbench_required_audit,
    _generate_user_solve_session_bundle_required_audit,
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

REQUIRED_AUDIT_DIRECT_EVIDENCE_QUESTIONS = [
    "Was the current `decision_packet.md` treated as the only execution authority and `task_packet.json` as background only?",
    "Did decision metadata remain valid, approved, and aligned with an active skill profile?",
    "Were startup commands recorded before project gates?",
    "Was startup-snapshot recorded before substantive gate/test execution?",
    "Were changes limited to allowed source/test/generated artifact paths?",
    "Did the implementation avoid reverse-solving, sample execution, User Solve Layer work, remote CI dispatch/polling, UI/API, database, queue, and scheduler work?",
    "Did the report generator produce Required Audit answers for every item in this decision?",
    "Did each Required Audit answer cite direct artifacts specific to its claim?",
    "Did the implementation prevent `ci_audit_handoff_bundle.json` from being used as a generic substitute for unrelated Required Audit claims?",
    "Did item-specific CI evidence questions cite `ci_run_evidence_result.json`, `local_ci_parity_result.json`, `ci_workflow_coverage_result.json`, or `ci_workflow_readiness_result.json` directly where appropriate?",
    "Did local execution bundle claims cite `local_execution_bundle.json` directly?",
    "Did codex prompt packet claims cite `codex_prompt_packet.json` directly?",
    "Did audit precheck claims cite `audit_precheck_result.json` directly?",
    "Did audit readiness claims cite `audit_readiness_packet.json` directly?",
    "Did final-check claims cite `final_gate_result.json` directly?",
    "Did run-closeout and close-round claims cite `run_closeout_result.json` and current round archive evidence directly?",
    "Did reconcile claims cite `ci_observation_reconcile_result.json` directly and mention `reconcile_status`, `final_consistency_status`, and `pending_diagnostic_sources` when relevant?",
    "Did audit handoff bundle claims cite `ci_audit_handoff_bundle.json` directly only when the claim is actually about the bundle?",
    "Did Required Audit item 30 from the previous decision stop using `ci_audit_handoff_bundle.json` as the sole/generic evidence for direct-evidence compliance?",
    "Did final-check or audit-readiness harden against placeholder, generic, or repeated Required Audit answers?",
    "Did tests include a failing fixture for generic bundle-substitute Required Audit answers?",
    "Did tests include a passing fixture for direct artifact-specific Required Audit answers?",
    "Did report-summary synthesis remain consistent with `execution_report.md` and `codex_execution_report.md`?",
    "Did `pytest_result.txt` match `tests_ran` in the execution report?",
    "Did execution-log align with command-plan and pytest_result?",
    "Did command-plan authorize all executed commands and omit no executed commands?",
    "Did `ci_observation_reconcile_result.json` remain current and final-consistent after this report-quality rework?",
    "Did `ci_audit_handoff_bundle.json` remain current and ready for audit after this report-quality rework?",
    "Did `final_gate_result.json` pass only after corrected Required Audit prose was produced?",
    "If run-closeout was authorized and executed, did it pass and archive the corrected report artifacts?",
    "Did the final report avoid generic/template prose and provide direct, claim-specific evidence for every Required Audit answer?",
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

USER_SOLVE_SESSION_BUNDLE_QUESTIONS = [
    "Was the current `decision_packet.md` treated as execution authority and `task_packet.json` as background only?",
    "Did decision metadata remain valid, approved, on `engineering_branch`, and aligned with active `reverse-agent-iteration@v2`?",
    "Were startup commands recorded before project gates/tests?",
    "Were current IDs used in reports, pytest_result, gate artifacts, and closeout artifacts?",
    "Were the previous audit limitations explicitly addressed?",
    "Does the final report avoid duplicate entries in `Allowed Changed Source/Test Files`, `files_changed`, and summary-derived changed-file sections?",
    "Are Required Audit answers precise, item-specific, and supported by direct source/test/gate/report evidence rather than generic filler?",
    "Did the fallback step coverage answer explicitly account for all six required fallback steps?",
    "Was `UserSolveSessionBundle` or equivalent session-level contract implemented?",
    "Does the session bundle include user-facing result, trace summary, fallback decision, validation status, evidence status, missing-evidence summary, public message, and developer-only trace/artifact references?",
    "Does default session user serialization hide internal project paths and developer trace references?",
    "Does session developer/debug serialization preserve internal references explicitly for audit use?",
    "Does session validation reject inconsistent states such as `verified` without passed validation or a verified result with missing evidence marked as unresolved?",
    "Does the session builder/factory use existing `FastSolveWrapper`, `UserSolveTaskTrace`, `FallbackLadder`, and `EvidenceQualityMapper` instead of duplicating pipeline/solver/harness/job/runner responsibilities?",
    "Does the session builder/factory remain in-memory and non-executing?",
    "Does fallback metadata remain non-executing, with local/dynamic/high-risk steps blocked unless explicit synthetic policy allows them?",
    "Does explicit synthetic permission still avoid actual tool/sample execution in this round?",
    "Does the bundle preserve previous `candidate_found` pending-validation behavior?",
    "Does the bundle preserve previous `verified` requires passed validation behavior?",
    "Does the bundle preserve previous missing-evidence to deep-analysis/fallback behavior?",
    "Does the bundle produce a clear user-facing `next_action` or equivalent field without exposing internal gate/report paths?",
    "Does the bundle produce developer-only audit references without making them default user output?",
    "Was a current gate artifact generated, for example `project_state/gates/user_solve_session_bundle_result.json`?",
    "Does the gate artifact prove no external invocation or dispatch capability was added?",
    "Did tests cover session user/developer serialization and redaction?",
    "Did tests cover session validation errors?",
    "Did tests cover session creation from candidate-found payloads?",
    "Did tests cover session creation from verified payloads?",
    "Did tests cover session creation from missing-evidence payloads with fallback recommendation?",
    "Did tests cover changed-file/report deduplication?",
    "Did tests cover Required Audit answer precision, including six-step fallback coverage wording?",
    "Did existing user-solve/trace/fallback/evidence tests continue passing?",
    "Did pytest_result record the real commands and exit codes?",
    "Did command-plan authorize all executed commands and omit no executed commands?",
    "Did final-check pass with current decision/report/round IDs?",
    "Did run-closeout pass and archive corrected reports if command-plan authorized closeout?",
    "Were forbidden files untouched?",
    "Did the final report avoid claiming solved/static_verified/runtime_validated/audit_verified for any sample?",
]

USER_SOLVE_CONTROL_PLANE_QUESTIONS = [
    "Was the current decision treated as execution authority and task_packet as background only?",
    "Did decision metadata remain valid and aligned with active `reverse-agent-iteration@v2`?",
    "Did this decision supersede the smaller handoff/provenance plan without mixing scopes?",
    "Were startup commands recorded before gates/tests?",
    "Was prework provenance captured and enforced?",
    "Did undeclared startup dirty source/test/doc files block `SUCCESS`?",
    "Was `prework_provenance_result.json` or equivalent generated with current IDs?",
    "Was `UserSolveRequest` implemented and tested?",
    "Does request validation reject real-file execution semantics and unsafe internal references?",
    "Was `UserSolveResponseEnvelope` implemented and tested?",
    "Does response serialization include status, answer/candidate, confidence, validation status, evidence status, public message, next action, fallback summary, warnings/errors, and developer audit fields?",
    "Was `UserSolveHandoffPacket` implemented and derived from `UserSolveSessionBundle`?",
    "Does handoff serialization preserve user/developer boundaries?",
    "Was `UserSolveController` implemented and tested?",
    "Does the controller compose existing result/trace/fallback/evidence/session/handoff components?",
    "Does the controller avoid external tool execution, persistence, dispatch, and real binary processing?",
    "Was fixture-only CLI preview implemented and tested?",
    "Does CLI preview emit safe response envelopes for candidate and missing-evidence demos?",
    "Does CLI preview avoid persistence, external calls, real-file processing, and dispatch?",
    "Does the control plane preserve candidate_found pending-validation behavior?",
    "Does the control plane preserve verified requires passed validation behavior?",
    "Does the control plane preserve missing-evidence to fallback/deep-analysis behavior?",
    "Does user serialization hide internal paths and developer trace refs by default?",
    "Does developer serialization retain audit references explicitly?",
    "Was `user_solve_control_plane_result.json` or equivalent generated with current IDs?",
    "Does the gate artifact prove non-invasive behavior and fixture-only operation?",
    "Did tests cover prework provenance clean start, dirty-start block, and explicit inherited baseline?",
    "Did tests cover request, response, handoff, controller, CLI, and report generation?",
    "Did existing user-solve/session/trace/fallback/evidence tests continue passing?",
    "Did pytest_result record real commands and exit codes?",
    "Did command-plan authorize all executed commands and omit no executed commands?",
    "Did final-check pass with current IDs?",
    "Did run-closeout pass and archive corrected reports if authorized?",
    "Were forbidden files untouched?",
    "Did the final report avoid any solved/static/runtime/audit verification claim for concrete samples?",
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


def _direct_evidence_decision_text() -> str:
    return (
        "# Decision\n\n"
        "decision_20260703_required_audit_direct_evidence_rework_v1 "
        "Required Audit Direct Evidence Rework accepted_requires_required_audit_direct_evidence\n\n"
        "## Required Audit\n\n"
        + "\n".join(
            f"{index}. {question}"
            for index, question in enumerate(REQUIRED_AUDIT_DIRECT_EVIDENCE_QUESTIONS, start=1)
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


def test_required_audit_direct_evidence_rework_generator_is_substantive() -> None:
    decision_text = _direct_evidence_decision_text()
    audit = _generate_required_audit_direct_evidence_rework_required_audit(decision_text)
    result = _required_audit_coverage_check(
        decision_text=decision_text,
        report_text="# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + audit,
        report_status="SUCCESS",
    )

    assert audit.count("### ") == 31
    assert "project_state/gates/ci_run_evidence_result.json" in audit
    assert "project_state/gates/local_ci_parity_result.json" in audit
    assert "project_state/gates/ci_workflow_coverage_result.json" in audit
    assert "project_state/gates/ci_workflow_readiness_result.json" in audit
    assert "project_state/gates/local_execution_bundle.json" in audit
    assert "project_state/gates/codex_prompt_packet.json" in audit
    assert "project_state/gates/audit_precheck_result.json" in audit
    assert "project_state/gates/audit_readiness_packet.json" in audit
    assert "project_state/gates/final_gate_result.json" in audit
    assert "project_state/gates/run_closeout_result.json" in audit
    assert "project_state/gates/ci_observation_reconcile_result.json" in audit
    assert "project_state/gates/ci_audit_handoff_bundle.json" in audit
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


def test_required_audit_rejects_generic_bundle_substitute_answers() -> None:
    questions = [
        "Did item-specific CI evidence questions cite `ci_run_evidence_result.json`, `local_ci_parity_result.json`, `ci_workflow_coverage_result.json`, or `ci_workflow_readiness_result.json` directly where appropriate?",
        "Did local execution bundle claims cite `local_execution_bundle.json` directly?",
        "Did final-check claims cite `final_gate_result.json` directly?",
        "Did Required Audit item 30 from the previous decision stop using `ci_audit_handoff_bundle.json` as the sole/generic evidence for direct-evidence compliance?",
    ]
    section = """### 1. Did item-specific CI evidence questions cite `ci_run_evidence_result.json`, `local_ci_parity_result.json`, `ci_workflow_coverage_result.json`, or `ci_workflow_readiness_result.json` directly where appropriate?

- Evidence: project_state/gates/ci_audit_handoff_bundle.json summarizes all CI evidence.
- Status: PASS
- Answer: The bundle summarizes CI evidence.

### 2. Did local execution bundle claims cite `local_execution_bundle.json` directly?

- Evidence: project_state/gates/ci_audit_handoff_bundle.json summarizes all execution evidence.
- Status: PASS
- Answer: The bundle summarizes local execution evidence.

### 3. Did final-check claims cite `final_gate_result.json` directly?

- Evidence: project_state/gates/ci_audit_handoff_bundle.json summarizes final-check status.
- Status: PASS
- Answer: The bundle summarizes final-check status.

### 4. Did Required Audit item 30 from the previous decision stop using `ci_audit_handoff_bundle.json` as the sole/generic evidence for direct-evidence compliance?

- Evidence: project_state/gates/ci_audit_handoff_bundle.json summarizes direct evidence.
- Status: PASS
- Answer: The bundle proves direct-evidence compliance.
"""

    failures = _required_audit_alignment_failures(questions, section)

    assert [failure["reason"] for failure in failures].count("evidence_domain_mismatch") >= 4


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


def test_user_solve_session_bundle_required_audit_generator_is_substantive() -> None:
    decision_text = (
        "# Decision\n\n"
        "User Solve Session Bundle accepted_requires_user_solve_session_bundle_contract "
        "accepted_requires_public_private_serialization_boundary "
        "accepted_requires_session_bundle_gate_artifact\n\n"
        "## Required Audit\n\n"
        + "\n".join(
            f"{index}. {question}"
            for index, question in enumerate(USER_SOLVE_SESSION_BUNDLE_QUESTIONS, start=1)
        )
    )

    audit = _generate_user_solve_session_bundle_required_audit(decision_text)
    result = _required_audit_coverage_check(
        decision_text=decision_text,
        report_text="# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + audit,
        report_status="SUCCESS",
    )

    assert audit.count("### ") == len(USER_SOLVE_SESSION_BUNDLE_QUESTIONS)
    assert "(to be filled)" not in audit
    assert "project_state/gates/user_solve_session_bundle_result.json" in audit
    for step_name in [
        "fast_strings",
        "ida_summary",
        "targeted_decompile",
        "constant_material_extract",
        "solver_attempt",
        "runtime_validation",
    ]:
        assert step_name in audit
    assert "generic filler" in audit
    assert result["status"] == "PASS"
    assert result["alignment_failures"] == []


def test_user_solve_control_plane_required_audit_generator_is_substantive() -> None:
    decision_text = (
        "# Decision\n\n"
        "Offline User Solve Control Plane Big Step "
        "accepted_requires_prework_provenance_hardening "
        "accepted_requires_offline_controller "
        "accepted_requires_fixture_only_cli_preview "
        "accepted_requires_control_plane_gate_artifact\n\n"
        "## Required Audit\n\n"
        + "\n".join(
            f"{index}. {question}"
            for index, question in enumerate(USER_SOLVE_CONTROL_PLANE_QUESTIONS, start=1)
        )
    )

    audit = _generate_user_solve_control_plane_required_audit(decision_text)
    result = _required_audit_coverage_check(
        decision_text=decision_text,
        report_text="# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + audit,
        report_status="SUCCESS",
    )

    assert audit.count("### ") == len(USER_SOLVE_CONTROL_PLANE_QUESTIONS)
    assert "(to be filled)" not in audit
    assert "project_state/gates/prework_provenance_result.json" in audit
    assert "project_state/gates/user_solve_control_plane_result.json" in audit
    assert "reverse_agent/user_solve_request.py" in audit
    assert "reverse_agent/user_solve_response.py" in audit
    assert "reverse_agent/user_solve_handoff.py" in audit
    assert "reverse_agent/user_solve_controller.py" in audit
    assert "reverse_agent/user_solve_cli.py" in audit
    assert "non-invasive" in audit
    assert result["status"] == "PASS"
    assert result["alignment_failures"] == []


def test_user_solve_local_frontend_mvp_required_audit_generator_is_substantive() -> None:
    questions = [
        "Was the current decision treated as execution authority and task_packet as background only?",
        "Did decision metadata remain valid and aligned with active reverse-agent-iteration@v2?",
        "Did this decision supersede the smaller frontend-bridge plan without mixing scopes?",
        "Were startup and prework provenance commands recorded and accepted before implementation validation?",
        "Was a frontend bridge facade implemented?",
        "Does the bridge delegate to the accepted offline controller instead of duplicating control-plane logic?",
        "Was a local fixture API adapter implemented?",
        "Does the local adapter provide route-like request/response handling without production service behavior?",
        "Was a static demo frontend added under frontend/user_solve_demo/?",
        "Does the demo cover candidate, missing-evidence, blocked, failed, and verified states?",
        "Was a deterministic fixture catalog implemented and shared by CLI/API/demo/schema where appropriate?",
        "Was a schema snapshot implemented for request, response, error payload, UI state, route contract, fixtures, and demo payloads?",
        "Was a UI state mapper implemented and tested?",
        "Does UI state mapping cover candidate pending validation, missing evidence, verified, failed, blocked, and review states?",
        "Was an error taxonomy implemented and tested?",
        "Do error payloads have stable codes, safe public messages, retryability, and developer diagnostics?",
        "Does default user/demo/API serialization hide internal paths and developer trace refs?",
        "Does developer serialization retain audit diagnostics explicitly?",
        "Does the local MVP avoid production service behavior, persistence, real-file processing, remote dispatch, and external process invocation?",
        "Does the local MVP preserve candidate_found pending-validation behavior?",
        "Does the local MVP preserve verified requires passed validation behavior?",
        "Does the local MVP preserve missing-evidence to fallback/deep-analysis behavior?",
        "Was a current user_solve_local_frontend_mvp_result.json or equivalent gate artifact generated?",
        "Was a current user_solve_frontend_mvp_snapshot.json or equivalent schema/demo snapshot artifact generated?",
        "Do gate artifacts carry current decision/report/round IDs?",
        "Do gate artifacts prove fixture-only, local-only, safe serialization behavior?",
        "Did tests cover static demo file presence and fixture linkage?",
        "Did tests cover local API adapter behavior?",
        "Did tests cover schema snapshot stability?",
        "Did tests cover fixture catalog coverage and redaction?",
        "Did tests cover UI state mapping?",
        "Did tests cover error taxonomy?",
        "Did tests cover frontend bridge facade behavior?",
        "Did existing offline control-plane tests continue passing?",
        "Did pytest_result record real commands and exit codes?",
        "Did command-plan authorize all executed commands and omit no executed commands?",
        "Did final-check pass with current IDs?",
        "Did run-closeout pass and archive corrected reports if authorized?",
        "Were forbidden files untouched?",
        "Did the final report avoid any solved/static/runtime/audit verification claim for concrete samples?",
    ]
    decision_text = (
        "# Decision\n\nUser Solve Local Frontend MVP accepted_requires_frontend_mvp_gate "
        "user_solve_local_frontend_mvp_result.json\n\n## Required Audit\n\n"
        + "\n".join(f"{index}. {question}" for index, question in enumerate(questions, start=1))
    )

    audit = _generate_user_solve_local_frontend_mvp_required_audit(decision_text)
    result = _required_audit_coverage_check(
        decision_text=decision_text,
        report_text="# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + audit,
        report_status="SUCCESS",
    )

    assert audit.count("### ") == 40
    assert "(to be filled)" not in audit
    assert "project_state/gates/user_solve_local_frontend_mvp_result.json" in audit
    assert "project_state/gates/user_solve_frontend_mvp_snapshot.json" in audit
    assert "frontend/user_solve_demo/index.html" in audit
    assert result["status"] == "PASS"
    assert result["alignment_failures"] == []


def test_user_solve_workbench_required_audit_generator_is_substantive() -> None:
    questions = [
        "Was the current decision treated as execution authority and task_packet as background only?",
        "Did decision metadata remain valid and aligned with active reverse-agent-iteration@v2?",
        "Did this decision supersede the smaller tool-profile-only plan without mixing scopes?",
        "Was the last accepted local frontend MVP treated as baseline?",
        "Were startup and prework provenance commands recorded before implementation validation?",
        "Was existing related functionality inspected before adding new modules?",
        "Was reverse_agent/tool_profiles.py implemented or compatibly extended?",
        "Does ToolProfile support stable identity, category, path source, availability metadata, capability flags, risk level, disabled/unavailable states, and safe serialization?",
        "Does tool profile loading use deterministic precedence without external process execution?",
        "Was reverse_agent/tool_capabilities.py implemented or compatibly extended?",
        "Does RunnerCapability represent runner id, platform metadata, available/missing/disabled tools, permission flags, and supported analysis features without dispatching work?",
        "Was reverse_agent/user_solve_route_plan.py implemented or compatibly extended?",
        "Does route planning map request state, missing evidence, capability availability, risk level, and permissions into safe planned next actions without executing them?",
        "Was reverse_agent/user_solve_task_trace.py implemented or compatibly extended?",
        "Does synthetic task trace capture request metadata, fixture/demo source, candidate state, missing evidence, route plan, validation state, and artifact placeholders without persistent task files?",
        "Was reverse_agent/user_solve_workbench.py implemented or compatibly extended?",
        "Does the workbench facade compose existing controller/session/result/UI/error/fixture behavior instead of duplicating it?",
        "Was reverse_agent/user_solve_workbench_api.py implemented or compatibly extended?",
        "Does the workbench API provide route-shaped pure-function handling without production service behavior?",
        "Were fixture catalog and frontend/demo fixtures expanded consistently if touched?",
        "Were schema snapshots expanded for tool profiles, runner capabilities, route plans, workbench API routes, task traces, fixtures, UI states, and public/developer payloads?",
        "Were example configs added with portable placeholders and no secrets?",
        "Were CLI previews added for candidate, missing-evidence, blocked, verified, route-plan, capability, and workbench states?",
        "Was documentation added or updated for the workbench foundation and future execution boundary?",
        "Was a current user_solve_workbench_result.json or equivalent gate artifact generated?",
        "Was a current user_solve_workbench_snapshot.json or equivalent snapshot generated?",
        "Do gate artifacts carry current decision/report/round IDs?",
        "Do gate artifacts prove no external tool invocation, no real sample analysis, no dispatch, no persistence, and no production service behavior?",
        "Do tests cover profile normalization, invalid profile rejection, capability serialization, route planner behavior, task trace serialization/redaction, workbench facade/API behavior, example config validity, schema stability, gates, reports, and CLI previews?",
        "Do existing user-solve/frontend/control-plane tests continue passing under command-plan coverage?",
        "Did pytest_result record real commands and exit codes?",
        "Did command-plan authorize all executed commands and omit no executed commands?",
        "Did final-check pass with current IDs?",
        "Did run-closeout pass and archive current reports if authorized?",
        "Were forbidden files untouched?",
        "Did the final report avoid any solved/static/runtime/audit verification claim for concrete samples?",
    ]
    decision_text = (
        "# Decision\n\nUser Solve Workbench Foundation accepted_requires_workbench_gate_artifact "
        "user_solve_workbench_result.json\n\n## Required Audit\n\n"
        + "\n".join(f"{index}. {question}" for index, question in enumerate(questions, start=1))
    )

    audit = _generate_user_solve_workbench_required_audit(decision_text)
    result = _required_audit_coverage_check(
        decision_text=decision_text,
        report_text="# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + audit,
        report_status="SUCCESS",
    )

    assert audit.count("### ") == 36
    assert "(to be filled)" not in audit
    assert "project_state/gates/user_solve_workbench_result.json" in audit
    assert "project_state/gates/user_solve_workbench_snapshot.json" in audit
    assert "reverse_agent/tool_profiles.py" in audit
    assert result["status"] == "PASS"
    assert result["alignment_failures"] == []


def test_ci_observation_bridge_required_audit_generator_is_substantive() -> None:
    questions = [
        "Does `ci_observation_schema_result.json` define commit SHA, workflow name, run ID, job summaries, step summaries, conclusion/status, observed command summaries, artifact metadata, and provenance?",
        "Does `ci_observation_handoff_packet.json` validate a supplied snapshot or record `AWAITING_EXTERNAL_OBSERVATION` when none is supplied?",
        "Does `ci_observation_reconcile_result.json` reconcile observation state with CI run evidence, local CI parity, workflow coverage, workflow readiness, command-plan, pytest_result, execution-log, and report-summary evidence?",
        "Does `ci_artifact_manifest_result.json` validate read-only artifact export expectations without repository write permissions?",
        "Does `ci_audit_handoff_bundle.json` summarize CI observation, manifest, parity, workflow coverage/readiness, report status, pytest status, final-check, and closeout status?",
    ] + [f"CI observation bridge audit item {index}?" for index in range(6, 33)]
    decision_text = (
        "# Decision\n\n"
        "ci-observation-schema ci-observation-handoff ci-observation-reconcile "
        "ci-artifact-manifest ci-audit-handoff-bundle "
        "ci_observation_schema_result.json ci_observation_handoff_packet.json "
        "ci_observation_reconcile_result.json ci_artifact_manifest_result.json "
        "ci_audit_handoff_bundle.json\n\n"
        "## Required Audit\n\n"
        + "\n".join(f"{index}. {question}" for index, question in enumerate(questions, start=1))
    )

    audit = _generate_ci_observation_bridge_required_audit(decision_text)
    result = _required_audit_coverage_check(
        decision_text=decision_text,
        report_text="# CODEX_EXECUTION_REPORT\n\n## Status\n\nSUCCESS\n\n" + audit,
        report_status="SUCCESS",
    )

    assert audit.count("### ") == 32
    assert "(to be filled)" not in audit
    assert "project_state/gates/ci_observation_schema_result.json" in audit
    assert "project_state/gates/ci_observation_handoff_packet.json" in audit
    assert "project_state/gates/ci_observation_reconcile_result.json" in audit
    assert "project_state/gates/ci_artifact_manifest_result.json" in audit
    assert "project_state/gates/ci_audit_handoff_bundle.json" in audit
    assert result["status"] == "PASS"
