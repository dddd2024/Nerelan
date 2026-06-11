import json
from pathlib import Path

import pytest

from reverse_agent.project_gate import final_check, main, preflight
from reverse_agent.project_state import archive_round, write_pytest_result


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_skill_registry(tmp_path: Path) -> None:
    _write_json(
        tmp_path / ".codex-skills" / "registry.json",
        {
            "schema_version": 1,
            "skills": {
                "reverse-agent-iteration": {
                    "path": ".codex-skills/reverse-agent-iteration/SKILL.md",
                    "status": "active",
                    "scope": "generic_workflow",
                    "version": 2,
                },
                "samplereverse-frontier": {
                    "path": ".codex-skills/samplereverse-frontier/SKILL.md",
                    "status": "active",
                    "scope": "sample_profile",
                    "version": 2,
                },
            },
        },
    )


def _archive_paths(round_id: str) -> list[str]:
    return [
        f"project_state/rounds/{round_id}/codex_execution_report.md",
        f"project_state/rounds/{round_id}/decision_packet.md",
        f"project_state/rounds/{round_id}/pytest_result.txt",
        f"project_state/rounds/{round_id}/round_manifest.json",
    ]


def _write_decision(state_dir: Path, *, decision_id: str, round_id: str) -> None:
    payload = {
        "schema_version": 1,
        "decision_id": decision_id,
        "round_id": round_id,
        "based_on_state_build_id": "state_test",
        "based_on_state_digest": "digest_test",
        "status": "APPROVED",
        "mainline": "engineering_branch",
        "skill_profiles": ["reverse-agent-iteration@v2", "samplereverse-frontier@v2"],
    }
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{json.dumps(payload, indent=2)}
```

# DECISION_PACKET
""",
        encoding="utf-8",
    )


def _write_preflight_decision(
    state_dir: Path,
    *,
    decision_id: str = "decision_preflight",
    round_id: str = "round_preflight",
    status: str = "APPROVED",
    mainline: str = "engineering_branch",
    skill_profiles: list[str] | None = None,
    goal: str = "Build a read-only project gate.",
    current_evidence: str = "Historical stale artifacts are not current evidence.",
    implementation_scope: str | None = None,
) -> None:
    profiles = skill_profiles if skill_profiles is not None else ["reverse-agent-iteration@v2", "samplereverse-frontier@v2"]
    payload = {
        "schema_version": 1,
        "decision_id": decision_id,
        "round_id": round_id,
        "based_on_state_build_id": "state_test",
        "based_on_state_digest": "digest_test",
        "status": status,
        "mainline": mainline,
        "skill_profiles": profiles,
    }
    scope = implementation_scope or """Allowed source files:

- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`

Allowed generated files:

- `project_state/gates/preflight_result.json`

Disallowed:

- `.codex-skills/`
- `solve_reports/`
"""
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{json.dumps(payload, indent=2)}
```

# DECISION_PACKET

## 1. Goal

{goal}

## 2. Current Evidence

{current_evidence}

## 6. Implementation Scope

{scope}
""",
        encoding="utf-8",
    )


def _make_preflight_state(tmp_path: Path, **decision_kwargs: object) -> Path:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_skill_registry(tmp_path)
    _write_json(
        state_dir / "current_state.json",
        {
            "round_id": "round_sample",
            "state_build_id": "state_test",
            "state_digest": "digest_test",
            "state_scope": "sample_state",
        },
    )
    _write_json(
        state_dir / "task_packet.json",
        {
            "task": "old_sample_task",
            "derived_task": "old_sample_task",
            "state_scope": "sample_state",
            "task_source": "derived_from_sample_artifacts",
            "execution_scope": "decision_packet_controls_current_round",
            "active_decision_packet": "project_state/decision_packet.md",
        },
    )
    _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
    _write_json(state_dir / "model_gate.json", {"should_call_model": False})
    _write_json(state_dir / "negative_results.json", {})
    _write_preflight_decision(state_dir, **decision_kwargs)
    return state_dir


def _write_report(
    state_dir: Path,
    *,
    decision_id: str,
    report_id: str,
    round_id: str,
    status: str = "SUCCESS",
    acceptance: str = "ACCEPTED",
    files_changed: list[str] | None = None,
    tests_ran: list[str] | None = None,
    generated_artifacts: list[str] | None = None,
) -> None:
    payload = {
        "schema_version": 1,
        "report_id": report_id,
        "round_id": round_id,
        "based_on_decision_id": decision_id,
        "status": status,
        "acceptance_recommendation": acceptance,
        "files_changed": files_changed if files_changed is not None else [],
        "tests_ran": tests_ran if tests_ran is not None else ["python -m pytest -q"],
        "generated_artifacts": generated_artifacts if generated_artifacts is not None else [],
        "verified_artifacts": [],
    }
    (state_dir / "codex_execution_report.md").write_text(
        f"""```json codex_report_summary
{json.dumps(payload, indent=2)}
```

# CODEX_EXECUTION_REPORT
""",
        encoding="utf-8",
    )


def _write_pytest(
    state_dir: Path,
    *,
    decision_id: str,
    report_id: str,
    round_id: str,
    tests_ran: list[str] | None = None,
    status: str = "PASSED",
    body: str = "1 passed\n",
) -> None:
    write_pytest_result(
        state_dir=state_dir,
        summary={
            "schema_version": 1,
            "decision_id": decision_id,
            "report_id": report_id,
            "round_id": round_id,
            "generated_at": "2026-06-11T00:00:00Z",
            "status": status,
            "tests_ran": tests_ran if tests_ran is not None else ["python -m pytest -q"],
        },
        body=body,
    )


def _make_gate_state(
    tmp_path: Path,
    *,
    status: str = "SUCCESS",
    acceptance: str = "ACCEPTED",
    files_changed: list[str] | None = None,
    tests_ran: list[str] | None = None,
    pytest_tests_ran: list[str] | None = None,
    generated_artifacts: list[str] | None = None,
) -> Path:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_skill_registry(tmp_path)
    _write_json(
        state_dir / "current_state.json",
        {
            "round_id": "round_sample",
            "state_build_id": "state_test",
            "state_digest": "digest_test",
            "state_scope": "sample_state",
            "source_harness_run": "run_test",
        },
    )
    _write_json(
        state_dir / "task_packet.json",
        {
            "state_scope": "sample_state",
            "task_source": "derived_from_sample_artifacts",
            "execution_scope": "decision_packet_controls_current_round",
            "active_decision_packet": "project_state/decision_packet.md",
        },
    )
    _write_json(state_dir / "artifact_index.json", {"missing": [], "latest_artifacts": {}})
    _write_json(state_dir / "model_gate.json", {"should_call_model": False})
    _write_json(state_dir / "negative_results.json", {})

    decision_id = "decision_gate"
    report_id = "report_gate"
    round_id = "round_gate"
    archive_paths = _archive_paths(round_id)
    base_changed = [
        "reverse_agent/project_gate.py",
        "tests/test_project_gate.py",
        "project_state/codex_execution_report.md",
        "project_state/pytest_result.txt",
        "project_state/gates/final_gate_result.json",
        *archive_paths,
    ]
    report_tests = tests_ran if tests_ran is not None else ["python -m pytest -q"]
    _write_decision(state_dir, decision_id=decision_id, round_id=round_id)
    _write_report(
        state_dir,
        decision_id=decision_id,
        report_id=report_id,
        round_id=round_id,
        status=status,
        acceptance=acceptance,
        files_changed=files_changed if files_changed is not None else base_changed,
        tests_ran=report_tests,
        generated_artifacts=generated_artifacts
        if generated_artifacts is not None
        else ["project_state/gates/final_gate_result.json", *archive_paths],
    )
    _write_pytest(
        state_dir,
        decision_id=decision_id,
        report_id=report_id,
        round_id=round_id,
        tests_ran=pytest_tests_ran if pytest_tests_ran is not None else report_tests,
    )
    archive_round(state_dir=state_dir, round_id=round_id)
    return state_dir


@pytest.fixture(autouse=True)
def _clean_git_diff(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "reverse_agent.project_gate._git_changed_files",
        lambda _repo_root: [
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
            "project_state/rounds/round_gate/codex_execution_report.md",
            "project_state/rounds/round_gate/decision_packet.md",
            "project_state/rounds/round_gate/pytest_result.txt",
            "project_state/rounds/round_gate/round_manifest.json",
        ],
    )


def _check(result: dict[str, object], name: str) -> dict[str, object]:
    return next(check for check in result["checks"] if check["name"] == name)


def test_final_check_passes_successful_consistent_round(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path)

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "PASSED"
    assert result["blocking_reasons"] == []
    assert (state_dir / "gates" / "final_gate_result.json").exists()


def test_final_check_fails_when_codex_report_summary_missing(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path)
    (state_dir / "codex_execution_report.md").write_text("# CODEX_EXECUTION_REPORT\n", encoding="utf-8")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "decision_report_match")["status"] == "FAIL"
    assert _check(result, "status_policy_valid")["status"] == "FAIL"


def test_final_check_warns_when_pytest_result_lacks_required_commands(tmp_path: Path) -> None:
    state_dir = _make_gate_state(
        tmp_path,
        tests_ran=["python -m pytest -q", "python -m reverse_agent.project_gate final-check --state-dir project_state"],
        pytest_tests_ran=["python -m pytest -q"],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "WARN"
    coverage = _check(result, "pytest_result_covers_report_tests")
    assert coverage["status"] == "WARN"
    assert "python -m reverse_agent.project_gate final-check --state-dir project_state" in coverage["missing_report_tests"]


def test_final_check_fails_when_files_changed_omits_archive_files(tmp_path: Path) -> None:
    state_dir = _make_gate_state(
        tmp_path,
        files_changed=[
            "reverse_agent/project_gate.py",
            "tests/test_project_gate.py",
            "project_state/codex_execution_report.md",
            "project_state/pytest_result.txt",
        ],
    )

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    diff_check = _check(result, "files_changed_covers_git_diff")
    assert diff_check["status"] == "FAIL"
    assert "project_state/rounds/round_gate/round_manifest.json" in diff_check["missing_files"]


def test_final_check_fails_when_generated_artifacts_omit_archive_files(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path, generated_artifacts=["project_state/gates/final_gate_result.json"])

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    artifact_check = _check(result, "generated_artifacts_cover_round_archive")
    assert artifact_check["status"] == "FAIL"
    assert "project_state/rounds/round_gate/codex_execution_report.md" in artifact_check["missing_artifacts"]


def test_final_check_fails_when_archived_report_differs_from_live_report(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path)
    with (state_dir / "codex_execution_report.md").open("a", encoding="utf-8") as handle:
        handle.write("\nLive report drift after archive.\n")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "archived_report_matches_live_report")["status"] == "FAIL"


def test_final_check_rejects_success_with_lint_failure(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path)
    text = (state_dir / "pytest_result.txt").read_text(encoding="utf-8")
    (state_dir / "pytest_result.txt").write_text(text + "\nFAILED tests/test_project_gate.py::test_x\n", encoding="utf-8")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "pytest_result_match")["status"] == "FAIL"
    assert _check(result, "status_policy_valid")["status"] == "FAIL"


def test_final_check_accepts_consistent_blocked_report_as_blocked(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path, status="BLOCKED", acceptance="BLOCKED")

    result = final_check(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "BLOCKED"
    assert result["blocking_reasons"] == []
    assert _check(result, "status_policy_valid")["status"] == "PASS"


def test_project_gate_cli_json_writes_result(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    state_dir = _make_gate_state(tmp_path)

    assert main(["final-check", "--state-dir", str(state_dir), "--json"]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["gate_status"] == "PASSED"
    assert (state_dir / "gates" / "final_gate_result.json").exists()


def test_preflight_passes_current_engineering_decision(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path)

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "PASSED"
    assert result["blocking_reasons"] == []
    assert (state_dir / "gates" / "preflight_result.json").exists()


def test_preflight_fails_when_decision_meta_missing(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path)
    (state_dir / "decision_packet.md").write_text("# DECISION_PACKET\n", encoding="utf-8")

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "decision_meta_parse")["status"] == "FAIL"


def test_preflight_fails_when_status_not_approved(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path, status="DRAFT")

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "decision_approved")["status"] == "FAIL"


def test_preflight_fails_on_invalid_mainline(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path, mainline="sample_solving")

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "mainline_valid")["status"] == "FAIL"


def test_preflight_fails_on_unknown_skill_profile(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path, skill_profiles=["unknown-skill@v1"])

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "skill_profiles_active")["status"] == "FAIL"


def test_preflight_blocks_consumed_decision(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path)
    _write_report(
        state_dir,
        decision_id="decision_preflight",
        report_id="report_preflight",
        round_id="round_preflight",
        generated_artifacts=["project_state/gates/preflight_result.json"],
    )
    _write_pytest(state_dir, decision_id="decision_preflight", report_id="report_preflight", round_id="round_preflight")

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "BLOCKED"
    assert _check(result, "decision_not_consumed_by_report")["status"] == "FAIL"


def test_preflight_fails_when_allowed_scope_includes_forbidden_path(tmp_path: Path) -> None:
    scope = """Allowed source files:

- `.codex-skills/registry.json`
- `reverse_agent/project_gate.py`

Allowed tests:

- `tests/test_project_gate.py`
"""
    state_dir = _make_preflight_state(tmp_path, implementation_scope=scope)

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    forbidden = _check(result, "forbidden_paths_not_allowed")
    assert forbidden["status"] == "FAIL"
    assert ".codex-skills/registry.json" in forbidden["forbidden_paths"]


def test_preflight_fails_engineering_branch_sample_solver_scope(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path, goal="Run sample solver and runtime probe for this round.")

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "mainline_scope_policy")["status"] == "FAIL"


def test_preflight_fails_reverse_mainline_without_tool_capability_audit(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(
        tmp_path,
        mainline="reverse_solving",
        goal="Continue reverse solving from current state.",
    )

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "tool_capability_audit_required_when_applicable")["status"] == "FAIL"


def test_preflight_fails_when_stale_artifact_claimed_as_current_evidence(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path, current_evidence="The stale artifact is current evidence.")

    result = preflight(state_dir=state_dir, repo_root=tmp_path)

    assert result["gate_status"] == "FAILED"
    assert _check(result, "artifact_freshness_policy")["status"] == "FAIL"


def test_project_gate_preflight_cli_json_writes_result(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    state_dir = _make_preflight_state(tmp_path)

    assert main(["preflight", "--state-dir", str(state_dir), "--json"]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["gate_status"] == "PASSED"
    assert (state_dir / "gates" / "preflight_result.json").exists()


def test_project_gate_preflight_cli_blocks_consumed_decision(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path)
    _write_report(
        state_dir,
        decision_id="decision_preflight",
        report_id="report_preflight",
        round_id="round_preflight",
        generated_artifacts=["project_state/gates/preflight_result.json"],
    )
    _write_pytest(state_dir, decision_id="decision_preflight", report_id="report_preflight", round_id="round_preflight")

    assert main(["preflight", "--state-dir", str(state_dir)]) != 0


def test_project_gate_preflight_cli_fails_invalid_decision(tmp_path: Path) -> None:
    state_dir = _make_preflight_state(tmp_path)
    (state_dir / "decision_packet.md").write_text("# DECISION_PACKET\n", encoding="utf-8")

    assert main(["preflight", "--state-dir", str(state_dir)]) != 0


def test_project_gate_final_check_cli_keeps_consistent_blocked_report_zero_exit(tmp_path: Path) -> None:
    state_dir = _make_gate_state(tmp_path, status="BLOCKED", acceptance="BLOCKED")

    assert main(["final-check", "--state-dir", str(state_dir)]) == 0
