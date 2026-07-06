import json
from pathlib import Path

from reverse_agent.project_state_manifest import build_state_manifest, validate_state_manifest


DECISION_ID = "decision_20260705_project_governance_context_registry_v1"
ROUND_ID = "round_20260705_project_governance_context_registry_v1"


def _write_state(state_dir: Path) -> None:
    state_dir.mkdir()
    (state_dir / "gates").mkdir()
    (state_dir / "rounds" / "round_20260704_manual_mode_web_orchestrator_mvp_big_step_v1").mkdir(parents=True)
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{{
  "schema_version": 1,
  "decision_id": "{DECISION_ID}",
  "round_id": "{ROUND_ID}",
  "based_on_state_build_id": "state_test",
  "based_on_state_digest": "digest_test",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}}
```

```json decision_contract
{{
  "follows_last_accepted_decision_id": "decision_20260704_manual_mode_web_orchestrator_mvp_big_step_v1",
  "follows_last_accepted_round_id": "round_20260704_manual_mode_web_orchestrator_mvp_big_step_v1"
}}
```
""",
        encoding="utf-8",
    )
    (state_dir / "codex_execution_report.md").write_text(
        f"""```json codex_report_summary
{{
  "schema_version": 1,
  "report_id": "codex_report_20260705_project_governance_context_registry_v1",
  "round_id": "{ROUND_ID}",
  "based_on_decision_id": "{DECISION_ID}",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [],
  "tests_ran": [],
  "generated_artifacts": []
}}
```
""",
        encoding="utf-8",
    )
    (state_dir / "pytest_result.txt").write_text(
        f"""```json pytest_result_summary
{{
  "schema_version": 1,
  "decision_id": "{DECISION_ID}",
  "report_id": "codex_report_20260705_project_governance_context_registry_v1",
  "round_id": "{ROUND_ID}",
  "status": "PASSED",
  "tests_ran": []
}}
```
""",
        encoding="utf-8",
    )
    for name, payload in {
        "command_plan.json": {"plan_status": "PASSED"},
        "execution_log.json": {"gate_status": "PASSED"},
        "final_gate_result.json": {"gate_status": "PASSED"},
        "report_summary_synthesis.json": {"synthesis_status": "PASSED"},
        "run_closeout_result.json": {"closeout_status": "PASSED"},
    }.items():
        (state_dir / "gates" / name).write_text(json.dumps(payload), encoding="utf-8")
    (state_dir / "task_packet.json").write_text("{}", encoding="utf-8")
    (state_dir / "current_state.json").write_text("{}", encoding="utf-8")
    (state_dir / "negative_results.json").write_text("[]", encoding="utf-8")
    (state_dir / "artifact_index.json").write_text(
        json.dumps({"missing": ["summary"], "latest_artifacts_v2": {"summary": {"freshness": "missing"}}}),
        encoding="utf-8",
    )
    (state_dir / "rounds" / "round_20260704_manual_mode_web_orchestrator_mvp_big_step_v1" / "round_manifest.json").write_text(
        json.dumps({"round_id": "round_20260704_manual_mode_web_orchestrator_mvp_big_step_v1"}),
        encoding="utf-8",
    )


def test_state_manifest_indexes_current_state_without_promoting_sample_gaps(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    manifest = build_state_manifest(state_dir=state_dir)

    assert manifest["decision_id"] == DECISION_ID
    assert manifest["round_id"] == ROUND_ID
    assert manifest["artifact_kind"] == "governance_index"
    assert manifest["authority"]["governance_artifacts_are_fact_source_replacements"] is False
    assert manifest["artifact_roles"]["historical_nonblocking"]["task_packet"]["role"] == "historical_nonblocking"
    assert manifest["artifact_roles"]["generated_or_updated"]["post_final_evidence_sync"]["path"] == (
        "project_state/gates/post_final_evidence_sync_result.json"
    )
    assert manifest["artifact_roles"]["generated_or_updated"]["job_lifecycle_validation"]["path"] == (
        "project_state/gates/job_lifecycle_validation_result.json"
    )
    assert manifest["artifact_roles"]["generated_or_updated"]["decision_preflight"]["path"] == (
        "project_state/gates/decision_preflight_result.json"
    )
    assert manifest["artifact_roles"]["generated_or_updated"]["current_planned_job"]["path"].endswith(
        "jobs/job_20260705_project_governance_context_registry_v1.json"
    )
    assert manifest["artifact_freshness"]["missing_sample_artifacts_blocking_for_current_round"] is False
    assert validate_state_manifest(manifest, decision_id=DECISION_ID, round_id=ROUND_ID) == []
    assert (state_dir / "state_manifest.json").exists()


def test_has_failed_command_block_detects_nonzero_exit() -> None:
    from reverse_agent.project_state import _has_failed_command_block
    body_with_failure = (
        "===== COMMAND: some-cmd =====\n"
        "output\n"
        "===== EXIT: 1 =====\n"
    )
    assert _has_failed_command_block(body_with_failure) is True


def test_has_failed_command_block_all_zero_exit() -> None:
    from reverse_agent.project_state import _has_failed_command_block
    body_all_pass = (
        "===== COMMAND: some-cmd =====\n"
        "output\n"
        "===== EXIT: 0 =====\n"
    )
    assert _has_failed_command_block(body_all_pass) is False


def test_has_failed_command_block_empty_body() -> None:
    from reverse_agent.project_state import _has_failed_command_block
    assert _has_failed_command_block("") is False


def test_write_pytest_result_downgrades_passed_to_failed_when_body_has_nonzero_exit(tmp_path: Path) -> None:
    """When status is PASSED but body contains non-zero exit codes,
    write_pytest_result should auto-downgrade the status to FAILED."""
    from reverse_agent.project_state import write_pytest_result, parse_pytest_result_header
    state_dir = tmp_path / "project_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    body = (
        "===== COMMAND: pytest =====\n"
        "10 passed\n"
        "===== EXIT: 0 =====\n"
        "\n"
        "===== COMMAND: final-check =====\n"
        "1 FAIL\n"
        "===== EXIT: 1 =====\n"
    )
    result_path = write_pytest_result(
        state_dir=state_dir,
        summary={
            "schema_version": 1,
            "decision_id": "decision_test",
            "report_id": "report_test",
            "round_id": "round_test",
            "generated_at": "2026-07-06T00:00:00Z",
            "status": "PASSED",
            "tests_ran": ["pytest", "final-check"],
        },
        body=body,
    )
    text = result_path.read_text(encoding="utf-8")
    header = parse_pytest_result_header(text)
    assert header["status"] == "FAILED"


def test_write_pytest_result_keeps_passed_when_all_exits_zero(tmp_path: Path) -> None:
    """When status is PASSED and all command exits are 0, status stays PASSED."""
    from reverse_agent.project_state import write_pytest_result, parse_pytest_result_header
    state_dir = tmp_path / "project_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    body = (
        "===== COMMAND: pytest =====\n"
        "10 passed\n"
        "===== EXIT: 0 =====\n"
    )
    result_path = write_pytest_result(
        state_dir=state_dir,
        summary={
            "schema_version": 1,
            "decision_id": "decision_test",
            "report_id": "report_test",
            "round_id": "round_test",
            "generated_at": "2026-07-06T00:00:00Z",
            "status": "PASSED",
            "tests_ran": ["pytest"],
        },
        body=body,
    )
    text = result_path.read_text(encoding="utf-8")
    header = parse_pytest_result_header(text)
    assert header["status"] == "PASSED"


def test_write_pytest_result_preserves_explicit_failed_status(tmp_path: Path) -> None:
    """When status is already FAILED, it should remain FAILED regardless of exit codes."""
    from reverse_agent.project_state import write_pytest_result, parse_pytest_result_header
    state_dir = tmp_path / "project_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    body = "===== COMMAND: pytest =====\n5 failed\n===== EXIT: 1 =====\n"
    result_path = write_pytest_result(
        state_dir=state_dir,
        summary={
            "schema_version": 1,
            "decision_id": "decision_test",
            "report_id": "report_test",
            "round_id": "round_test",
            "generated_at": "2026-07-06T00:00:00Z",
            "status": "FAILED",
            "tests_ran": ["pytest"],
        },
        body=body,
    )
    text = result_path.read_text(encoding="utf-8")
    header = parse_pytest_result_header(text)
    assert header["status"] == "FAILED"
