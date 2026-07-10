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


def test_state_manifest_includes_phase_a_scoped_metadata_section(tmp_path: Path) -> None:
    """Phase A: state_manifest must emit a scoped_metadata section classifying
    current state files with scope/domain/mainline/role/freshness metadata,
    treating legacy gaps as non-blocking warnings."""
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    manifest = build_state_manifest(state_dir=state_dir)

    assert "scoped_metadata" in manifest
    scoped = manifest["scoped_metadata"]
    assert scoped["phase"] == "A"
    # Policy flags preserve Phase A non-blocking behavior
    assert scoped["policy"]["missing_scope_metadata_is_non_blocking"] is True
    assert scoped["policy"]["legacy_entries_preserved"] is True
    assert scoped["policy"]["no_files_moved_or_deleted"] is True
    assert scoped["policy"]["domain_migration_not_complete"] is True
    # State file scope classifications are present
    assert "state_file_scope" in scoped
    file_scope = scoped["state_file_scope"]
    assert "project_state/decision_packet.md" in file_scope
    assert file_scope["project_state/decision_packet.md"]["scope"] == "global"
    assert file_scope["project_state/decision_packet.md"]["domain"] == "project_governance"
    # Coverage summary is present and non-blocking
    state_cov = scoped["state_file_scope_coverage"]
    assert state_cov["phase"] == "A"
    assert state_cov["hard_failure"] is False
    assert state_cov["legacy_compatible"] is True
    assert state_cov["total_state_files"] >= 1
    assert state_cov["scoped_state_files"] >= 1
    # negative_results scope coverage is surfaced (file exists with [])
    neg_cov = scoped["negative_results_scope_coverage"]
    assert neg_cov.get("phase") == "A"
    assert neg_cov.get("hard_failure") is False


def test_state_manifest_scoped_metadata_classifies_sample_and_global_files(tmp_path: Path) -> None:
    """state_manifest scoped_metadata must distinguish global governance files
    from sample-scoped reverse_solving files."""
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    manifest = build_state_manifest(state_dir=state_dir)
    file_scope = manifest["scoped_metadata"]["state_file_scope"]

    # Global governance file
    assert file_scope["project_state/decision_packet.md"]["scope"] == "global"
    assert file_scope["project_state/decision_packet.md"]["mainline"] == "project_governance"
    # Sample-scoped reverse_solving file
    assert file_scope["project_state/artifact_index.json"]["scope"] == "sample"
    assert file_scope["project_state/artifact_index.json"]["domain"] == "reverse_solving"
    assert file_scope["project_state/artifact_index.json"]["role"] == "historical_nonblocking"


def test_state_manifest_scoped_metadata_legacy_gaps_do_not_hard_fail(tmp_path: Path) -> None:
    """When some state files lack scope metadata (legacy), the scoped_metadata
    coverage must remain non-blocking in Phase A."""
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    manifest = build_state_manifest(state_dir=state_dir)
    state_cov = manifest["scoped_metadata"]["state_file_scope_coverage"]
    # hard_failure must always be False in Phase A
    assert state_cov["hard_failure"] is False
    assert state_cov["legacy_compatible"] is True
    # Legacy count may be > 0 but must not block
    assert state_cov["legacy_state_files_without_scope"] >= 0


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


def test_expected_exit_codes_from_plan_extracts_mapping() -> None:
    """_expected_exit_codes_from_plan extracts command->exit codes mapping."""
    from reverse_agent.project_state import _expected_exit_codes_from_plan
    plan = {
        "commands": [
            {"command": "pytest", "expected_exit_codes": [0]},
            {"command": "final-check", "expected_exit_codes": [0, 1]},
            {"command": "no-codes"},
            {"not_a_command": True, "expected_exit_codes": [0]},
        ]
    }
    mapping = _expected_exit_codes_from_plan(plan)
    assert mapping == {"pytest": [0], "final-check": [0, 1]}


def test_expected_exit_codes_from_plan_empty_plan() -> None:
    """_expected_exit_codes_from_plan returns empty dict for missing/invalid commands."""
    from reverse_agent.project_state import _expected_exit_codes_from_plan
    assert _expected_exit_codes_from_plan({}) == {}
    assert _expected_exit_codes_from_plan({"commands": "not_a_list"}) == {}
    assert _expected_exit_codes_from_plan({"commands": []}) == {}


def test_has_failed_command_block_with_plan_allows_expected_nonzero() -> None:
    """When command_plan allows exit 1, exit 1 should NOT count as failure."""
    from reverse_agent.project_state import _has_failed_command_block_with_plan
    body = (
        "===== COMMAND: final-check =====\n"
        "1 FAIL\n"
        "===== EXIT: 1 =====\n"
    )
    expected_by_command = {"final-check": [0, 1]}
    assert _has_failed_command_block_with_plan(body, expected_by_command) is False


def test_has_failed_command_block_with_plan_fails_unexpected_nonzero() -> None:
    """When command_plan only allows exit 0, exit 1 should count as failure."""
    from reverse_agent.project_state import _has_failed_command_block_with_plan
    body = (
        "===== COMMAND: pytest =====\n"
        "1 failed\n"
        "===== EXIT: 1 =====\n"
    )
    expected_by_command = {"pytest": [0]}
    assert _has_failed_command_block_with_plan(body, expected_by_command) is True


def test_has_failed_command_block_with_plan_falls_back_when_no_plan() -> None:
    """When expected_by_command is None/empty, fall back to simple non-zero check."""
    from reverse_agent.project_state import _has_failed_command_block_with_plan
    body = (
        "===== COMMAND: final-check =====\n"
        "1 FAIL\n"
        "===== EXIT: 1 =====\n"
    )
    assert _has_failed_command_block_with_plan(body, None) is True
    assert _has_failed_command_block_with_plan(body, {}) is True


def test_has_failed_command_block_with_plan_prefix_match() -> None:
    """Prefix matching should find expected exit codes for wrapped commands."""
    from reverse_agent.project_state import _has_failed_command_block_with_plan
    body = (
        "===== COMMAND: python -m reverse_agent.project_gate final-check --state-dir project_state =====\n"
        "1 FAIL\n"
        "===== EXIT: 1 =====\n"
    )
    expected_by_command = {"final-check": [0, 1]}
    assert _has_failed_command_block_with_plan(body, expected_by_command) is False


def test_write_pytest_result_with_command_plan_keeps_passed_for_expected_exit(tmp_path: Path) -> None:
    """When command_plan allows exit 1 for final-check, PASSED status stays PASSED."""
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
    command_plan = {
        "commands": [
            {"command": "pytest", "expected_exit_codes": [0]},
            {"command": "final-check", "expected_exit_codes": [0, 1]},
        ]
    }
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
        command_plan=command_plan,
    )
    text = result_path.read_text(encoding="utf-8")
    header = parse_pytest_result_header(text)
    assert header["status"] == "PASSED"


def test_write_pytest_result_with_command_plan_downgrades_for_unexpected_exit(tmp_path: Path) -> None:
    """When command_plan only allows exit 0 but body has exit 1, downgrade PASSED->FAILED."""
    from reverse_agent.project_state import write_pytest_result, parse_pytest_result_header
    state_dir = tmp_path / "project_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    body = (
        "===== COMMAND: pytest =====\n"
        "1 failed\n"
        "===== EXIT: 1 =====\n"
    )
    command_plan = {
        "commands": [
            {"command": "pytest", "expected_exit_codes": [0]},
        ]
    }
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
        command_plan=command_plan,
    )
    text = result_path.read_text(encoding="utf-8")
    header = parse_pytest_result_header(text)
    assert header["status"] == "FAILED"


def test_write_pytest_result_without_command_plan_still_downgrades(tmp_path: Path) -> None:
    """Without command_plan, PASSED with non-zero exit still downgrades to FAILED (backwards compat)."""
    from reverse_agent.project_state import write_pytest_result, parse_pytest_result_header
    state_dir = tmp_path / "project_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    body = (
        "===== COMMAND: pytest =====\n"
        "1 failed\n"
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
            "tests_ran": ["pytest"],
        },
        body=body,
    )
    text = result_path.read_text(encoding="utf-8")
    header = parse_pytest_result_header(text)
    assert header["status"] == "FAILED"


# ---------------------------------------------------------------------------
# State manifest freshness validation tests
# ---------------------------------------------------------------------------

REPORT_ID = "codex_report_20260705_project_governance_context_registry_v1"


def _build_fresh_manifest(tmp_path: Path) -> tuple[Path, dict]:
    """Build a state_manifest from a valid fixture and return (state_dir, manifest)."""
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)
    manifest = build_state_manifest(state_dir=state_dir)
    return state_dir, manifest


def test_validate_state_manifest_current_artifacts_pass_when_fresh(tmp_path: Path) -> None:
    """A manifest regenerated from live files must pass freshness validation."""
    state_dir, manifest = _build_fresh_manifest(tmp_path)
    errors = validate_state_manifest(
        manifest,
        decision_id=DECISION_ID,
        round_id=ROUND_ID,
        report_id=REPORT_ID,
        state_dir=state_dir,
    )
    assert errors == []


def test_validate_state_manifest_rejects_stale_decision_id(tmp_path: Path) -> None:
    """A manifest with a stale decision_id must fail validation."""
    state_dir, manifest = _build_fresh_manifest(tmp_path)
    manifest["decision_id"] = "decision_stale_v0"
    errors = validate_state_manifest(
        manifest,
        decision_id=DECISION_ID,
        round_id=ROUND_ID,
        report_id=REPORT_ID,
        state_dir=state_dir,
    )
    assert any("decision_id mismatch" in e for e in errors)


def test_validate_state_manifest_rejects_stale_round_id(tmp_path: Path) -> None:
    """A manifest with a stale round_id must fail validation."""
    state_dir, manifest = _build_fresh_manifest(tmp_path)
    manifest["round_id"] = "round_stale_v0"
    errors = validate_state_manifest(
        manifest,
        decision_id=DECISION_ID,
        round_id=ROUND_ID,
        report_id=REPORT_ID,
        state_dir=state_dir,
    )
    assert any("round_id mismatch" in e for e in errors)


def test_validate_state_manifest_rejects_stale_current_artifact_sha256(tmp_path: Path) -> None:
    """A manifest with a stale SHA-256 for a current artifact must fail."""
    state_dir, manifest = _build_fresh_manifest(tmp_path)
    current = manifest["artifact_roles"]["current"]
    # Tamper with the decision_packet SHA-256 (it is a required current ref)
    current["decision_packet"]["sha256"] = "0" * 64
    errors = validate_state_manifest(
        manifest,
        decision_id=DECISION_ID,
        round_id=ROUND_ID,
        report_id=REPORT_ID,
        state_dir=state_dir,
    )
    assert any("sha256 mismatch" in e and "decision_packet" in e for e in errors)


def test_validate_state_manifest_rejects_stale_current_artifact_size(tmp_path: Path) -> None:
    """A manifest with a stale size for a current artifact must fail."""
    state_dir, manifest = _build_fresh_manifest(tmp_path)
    current = manifest["artifact_roles"]["current"]
    # Tamper with the decision_packet size (it is a required current ref)
    current["decision_packet"]["size_bytes"] = current["decision_packet"]["size_bytes"] + 999
    errors = validate_state_manifest(
        manifest,
        decision_id=DECISION_ID,
        round_id=ROUND_ID,
        report_id=REPORT_ID,
        state_dir=state_dir,
    )
    assert any("size mismatch" in e and "decision_packet" in e for e in errors)


def test_validate_state_manifest_rejects_missing_required_current_file(tmp_path: Path) -> None:
    """A manifest marking a required current file as exists=true when it is
    missing on disk must fail."""
    state_dir, manifest = _build_fresh_manifest(tmp_path)
    # Delete a required current file from disk
    (state_dir / "decision_packet.md").unlink()
    errors = validate_state_manifest(
        manifest,
        decision_id=DECISION_ID,
        round_id=ROUND_ID,
        report_id=REPORT_ID,
        state_dir=state_dir,
    )
    assert any("decision_packet" in e and "missing" in e for e in errors)


def test_validate_state_manifest_rejects_stale_report_id(tmp_path: Path) -> None:
    """A manifest with a stale report_id must fail when report_id is provided."""
    state_dir, manifest = _build_fresh_manifest(tmp_path)
    manifest["report_id"] = "codex_report_stale_v0"
    errors = validate_state_manifest(
        manifest,
        decision_id=DECISION_ID,
        round_id=ROUND_ID,
        report_id=REPORT_ID,
        state_dir=state_dir,
    )
    assert any("report_id mismatch" in e for e in errors)


def test_validate_state_manifest_without_state_dir_skips_freshness(tmp_path: Path) -> None:
    """When state_dir is not provided, freshness validation is skipped
    (backward compatible with existing callers)."""
    state_dir, manifest = _build_fresh_manifest(tmp_path)
    # Tamper with SHA-256 but don't pass state_dir — should NOT report sha256 error
    manifest["artifact_roles"]["current"]["decision_packet"]["sha256"] = "0" * 64
    errors = validate_state_manifest(
        manifest,
        decision_id=DECISION_ID,
        round_id=ROUND_ID,
    )
    assert not any("sha256 mismatch" in e for e in errors)
