import json
from pathlib import Path

from reverse_agent.project_context_builder import (
    build_current_context_packet,
    validate_current_context_packet,
)


DECISION_ID = "decision_20260706_post_final_timestamp_precision_hardening_v1"
ROUND_ID = "round_20260706_post_final_timestamp_precision_hardening_v1"


def _write_state(state_dir: Path) -> None:
    state_dir.mkdir()
    (state_dir / "gates").mkdir()
    (state_dir / "decision_packet.md").write_text(
        f"""```json decision_meta
{{
  "schema_version": 1,
  "decision_id": "{DECISION_ID}",
  "round_id": "{ROUND_ID}",
  "based_on_state_build_id": "state_test",
  "based_on_state_digest": "digest_test",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}}
```

```json decision_contract
{{
  "forbidden_capabilities_this_round": ["model_api_invocation", "runner_dispatch"],
  "forbidden_mutated_paths": [".codex-skills/*", "solve_reports/*"],
  "allowed_source_files": ["reverse_agent/project_context_builder.py"]
}}
```
""",
        encoding="utf-8",
    )
    (state_dir / "codex_execution_report.md").write_text("", encoding="utf-8")
    (state_dir / "pytest_result.txt").write_text("", encoding="utf-8")
    (state_dir / "artifact_index.json").write_text(json.dumps({"missing": ["summary"]}), encoding="utf-8")
    (state_dir / "negative_results.json").write_text(
        json.dumps([{"direction": "old sample_solver blind search", "severity": "soft_block", "do_not_repeat": True}]),
        encoding="utf-8",
    )
    (state_dir / "task_packet.json").write_text("{}", encoding="utf-8")
    (state_dir / "current_state.json").write_text("{}", encoding="utf-8")
    (state_dir / "gates" / "command_plan.json").write_text(json.dumps({"plan_status": "PASSED"}), encoding="utf-8")
    (state_dir / "gates" / "final_gate_result.json").write_text(json.dumps({"gate_status": "PASSED"}), encoding="utf-8")
    (state_dir / "gates" / "report_summary_synthesis.json").write_text(json.dumps({"synthesis_status": "PASSED"}), encoding="utf-8")


def test_current_context_packet_is_bounded_and_non_dispatching(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    packet = build_current_context_packet(state_dir=state_dir)

    assert packet["decision_id"] == DECISION_ID
    assert packet["round_id"] == ROUND_ID
    assert packet["planner_context"]["task_authority"] == "project_state/decision_packet.md"
    assert packet["planner_context"]["task_packet_role"] == "background_only"
    assert packet["auditor_context"]["governance_artifacts_are_fact_source_replacements"] is False
    assert packet["auditor_context"]["final_gate_status"] == ""
    assert packet["auditor_context"]["final_gate_status_source"] == "stale_final_gate_result"
    assert packet["auditor_context"]["final_gate_current"] is False
    assert packet["auditor_context"]["post_final_sync_status"] == "STALE_PRE_FINAL_CONTEXT"
    assert packet["auditor_context"]["stale_context_detected"] is True
    assert packet["model_api_invocation"] is False
    assert packet["runner_dispatch"] is False
    assert packet["external_analysis_tool_invocation"] is False
    assert packet["negative_results_constraints"][0]["do_not_repeat"] is True
    assert validate_current_context_packet(packet, decision_id=DECISION_ID, round_id=ROUND_ID) == []
    assert packet["auditor_context"]["timestamp_precision_policy"] == "precise_parsed_with_digest_fallback"
    assert "final_gate_source_path" in packet["auditor_context"]
    assert "final_gate_source_sha256" in packet["auditor_context"]
    assert "context_sync_basis" in packet["auditor_context"]
    assert "post_final_sync_evaluated_at" in packet["auditor_context"]
    assert (state_dir / "context" / "current_context_packet.json").exists()


def test_context_packet_generated_at_has_microsecond_precision(tmp_path: Path) -> None:
    """context packet generated_at should preserve microsecond precision
    so that timestamp comparisons with fractional-second final gate timestamps
    are accurate."""
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    packet = build_current_context_packet(state_dir=state_dir)
    generated_at = packet["generated_at"]
    # Should contain fractional seconds (at least 6 digits after decimal point)
    assert "." in generated_at
    # Should end with Z
    assert generated_at.endswith("Z")


def test_validate_rejects_missing_timestamp_precision_policy(tmp_path: Path) -> None:
    """validate_current_context_packet rejects missing timestamp_precision_policy."""
    bad_packet = {
        "schema_version": 1,
        "decision_id": DECISION_ID,
        "round_id": ROUND_ID,
        "artifact_kind": "governance_index",
        "auditor_context": {
            "governance_artifacts_are_fact_source_replacements": False,
        },
        "model_api_invocation": False,
        "runner_dispatch": False,
        "external_analysis_tool_invocation": False,
    }
    errors = validate_current_context_packet(bad_packet, decision_id=DECISION_ID, round_id=ROUND_ID)
    assert any("timestamp_precision_policy" in e for e in errors)


def test_context_packet_backward_compatible_fields(tmp_path: Path) -> None:
    """Existing fields in context packet should still be present after
    adding new timestamp precision fields."""
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    packet = build_current_context_packet(state_dir=state_dir)
    # Old fields should still be present
    assert "schema_version" in packet
    assert "artifact_name" in packet
    assert "artifact_kind" in packet
    assert "generated_at" in packet
    assert "decision_id" in packet
    assert "round_id" in packet
    assert "planner_context" in packet
    assert "auditor_context" in packet
    assert "existing_capabilities" in packet
    assert "forbidden_capabilities" in packet
    assert "negative_results_constraints" in packet
    # Old auditor_context fields should still be present
    ac = packet["auditor_context"]
    assert "final_gate_status" in ac
    assert "final_gate_status_source" in ac
    assert "final_gate_current" in ac
    assert "post_final_sync_status" in ac
    assert "stale_context_detected" in ac
