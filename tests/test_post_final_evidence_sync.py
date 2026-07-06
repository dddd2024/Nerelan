import json
from pathlib import Path

from reverse_agent.post_final_evidence_sync import (
    build_post_final_evidence_sync_result,
    validate_post_final_evidence_sync_result,
)


DECISION_ID = "decision_20260706_post_final_sync_job_preflight_big_step_v1"
ROUND_ID = "round_20260706_post_final_sync_job_preflight_big_step_v1"


def _write_state(state_dir: Path, *, final_gate: dict[str, object] | None = None) -> None:
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
  "forbidden_capabilities_this_round": [
    "automatic_runner_dispatch",
    "manual_runner_dispatch",
    "model_api_invocation",
    "workflow_dispatch_trigger",
    "real_sample_analysis_execution",
    "sqlite_database_creation"
  ],
  "allowed_source_files": ["reverse_agent/post_final_evidence_sync.py"]
}}
```
""",
        encoding="utf-8",
    )
    for name, payload in {
        "command_plan.json": {
            "decision_id": DECISION_ID,
            "round_id": ROUND_ID,
            "plan_status": "PASSED",
        },
        "report_summary_synthesis.json": {"synthesis_status": "PASSED"},
    }.items():
        (state_dir / "gates" / name).write_text(json.dumps(payload), encoding="utf-8")
    if final_gate is not None:
        (state_dir / "gates" / "final_gate_result.json").write_text(json.dumps(final_gate), encoding="utf-8")
    (state_dir / "codex_execution_report.md").write_text("", encoding="utf-8")
    (state_dir / "pytest_result.txt").write_text("", encoding="utf-8")
    (state_dir / "artifact_index.json").write_text("{}", encoding="utf-8")
    (state_dir / "negative_results.json").write_text("[]", encoding="utf-8")
    (state_dir / "task_packet.json").write_text("{}", encoding="utf-8")
    (state_dir / "current_state.json").write_text("{}", encoding="utf-8")


def test_post_final_evidence_sync_passes_pre_final_with_warning(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)

    result = build_post_final_evidence_sync_result(state_dir=state_dir)
    context = json.loads((state_dir / "context" / "current_context_packet.json").read_text(encoding="utf-8"))

    assert result["gate_status"] == "PASSED"
    assert result["final_gate_current"] is False
    assert result["context_final_gate_status"] == ""
    assert result["post_final_sync_status"] == "PRE_FINAL_CONTEXT"
    assert result["warnings"]
    assert context["auditor_context"]["final_gate_status_source"] == "missing_final_gate_result"
    assert validate_post_final_evidence_sync_result(result, decision_id=DECISION_ID, round_id=ROUND_ID) == []


def test_post_final_evidence_sync_refreshes_context_after_current_final_gate(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    _write_state(
        state_dir,
        final_gate={
            "decision_id": DECISION_ID,
            "round_id": ROUND_ID,
            "gate_status": "PASSED",
            "generated_at": "2026-07-06T00:00:00Z",
        },
    )

    result = build_post_final_evidence_sync_result(state_dir=state_dir)
    context = json.loads((state_dir / "context" / "current_context_packet.json").read_text(encoding="utf-8"))

    assert result["gate_status"] == "PASSED"
    assert result["final_gate_current"] is True
    assert result["context_final_gate_status"] == "PASSED"
    assert result["context_final_gate_status_source"] == "current_final_gate_result"
    assert result["post_final_sync_status"] == "CURRENT_POST_FINAL_SYNCED"
    assert context["auditor_context"]["stale_context_detected"] is False
    assert (state_dir / "gates" / "post_final_evidence_sync_snapshot.json").exists()
    assert validate_post_final_evidence_sync_result(result, decision_id=DECISION_ID, round_id=ROUND_ID) == []
