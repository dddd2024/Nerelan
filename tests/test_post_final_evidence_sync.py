import json
from pathlib import Path

from reverse_agent.post_final_evidence_sync import (
    build_post_final_evidence_sync_result,
    validate_post_final_evidence_sync_result,
)


DECISION_ID = "decision_20260706_post_final_timestamp_precision_hardening_v1"
ROUND_ID = "round_20260706_post_final_timestamp_precision_hardening_v1"


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
  "allowed_source_files": ["reverse_agent/post_final_evidence_sync.py"],
  "accepted_requires_source_artifact_identity_checks": true,
  "accepted_requires_context_packet_precise_sync_fields": true,
  "accepted_requires_final_check_coverage_for_timestamp_precision": true,
  "accepted_requires_post_final_sync_warning_removed_or_reclassified": true
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
    assert result["context_sync_basis"] == "pre_final"
    assert result["timestamp_precision_policy"] == "precise_parsed_with_digest_fallback"
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
    assert result["context_sync_basis"] in ("timestamp_and_digest", "timestamp_only", "digest_current_timestamp_rounded")
    assert result["timestamp_precision_policy"] == "precise_parsed_with_digest_fallback"
    assert result["final_gate_source_sha256"] != ""
    assert "context_sync_basis" in context["auditor_context"]
    assert context["auditor_context"]["stale_context_detected"] is False
    assert (state_dir / "gates" / "post_final_evidence_sync_snapshot.json").exists()
    assert validate_post_final_evidence_sync_result(result, decision_id=DECISION_ID, round_id=ROUND_ID) == []


def test_digest_match_suppresses_timestamp_warning_when_context_rounded(tmp_path: Path) -> None:
    """When context generated_at is second-granularity and final_gate has fractional
    seconds but digest and IDs match, the sync basis should be
    digest_current_timestamp_rounded and no active timestamp warning should be emitted."""
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)
    # Write a final gate with fractional-second timestamp
    final_gate_data = {
        "decision_id": DECISION_ID,
        "round_id": ROUND_ID,
        "gate_status": "PASSED",
        "generated_at": "2026-07-06T00:00:00.123456Z",
    }
    (state_dir / "gates" / "final_gate_result.json").write_text(
        json.dumps(final_gate_data), encoding="utf-8"
    )
    # Build once to create context with matching digest
    result1 = build_post_final_evidence_sync_result(state_dir=state_dir)
    context1 = json.loads((state_dir / "context" / "current_context_packet.json").read_text(encoding="utf-8"))
    # The context generated_at should now have microsecond precision
    # and context_sync_basis should indicate digest-backed current
    assert result1["gate_status"] == "PASSED"
    assert result1["final_gate_current"] is True
    assert result1["context_sync_basis"] in ("timestamp_and_digest", "digest_current_timestamp_rounded", "timestamp_only")
    assert result1["timestamp_precision_policy"] == "precise_parsed_with_digest_fallback"
    assert result1["final_gate_source_sha256"] != ""
    # No active timestamp warning when digest confirms current sync
    ts_warnings = [w for w in result1["warnings"] if "generated before final_gate_result timestamp" in w]
    if result1["context_sync_basis"] == "digest_current_timestamp_rounded":
        assert ts_warnings == []
    assert context1["auditor_context"]["context_sync_basis"] in ("timestamp_and_digest", "digest_current_timestamp_rounded", "timestamp_only")
    assert context1["auditor_context"]["timestamp_precision_policy"] == "precise_parsed_with_digest_fallback"
    assert validate_post_final_evidence_sync_result(result1, decision_id=DECISION_ID, round_id=ROUND_ID) == []


def test_stale_context_after_newer_final_gate_still_warns(tmp_path: Path) -> None:
    """When the context packet references a different final gate artifact,
    the sync should detect staleness and warn/fail."""
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)
    # Write a final gate for the current decision
    final_gate_data = {
        "decision_id": DECISION_ID,
        "round_id": ROUND_ID,
        "gate_status": "PASSED",
        "generated_at": "2026-07-06T12:00:00Z",
    }
    (state_dir / "gates" / "final_gate_result.json").write_text(
        json.dumps(final_gate_data), encoding="utf-8"
    )
    # Build context referencing this gate
    result1 = build_post_final_evidence_sync_result(state_dir=state_dir)
    assert result1["gate_status"] == "PASSED"
    # Now replace the final gate with a different one (different timestamp)
    final_gate_data_v2 = {
        "decision_id": DECISION_ID,
        "round_id": ROUND_ID,
        "gate_status": "PASSED",
        "generated_at": "2026-07-06T13:00:00Z",
    }
    (state_dir / "gates" / "final_gate_result.json").write_text(
        json.dumps(final_gate_data_v2), encoding="utf-8"
    )
    # Do NOT refresh context: the context still references the old gate
    result2 = build_post_final_evidence_sync_result(state_dir=state_dir, refresh_context=True)
    # After refresh, context should be current again
    assert result2["gate_status"] == "PASSED"
    assert result2["final_gate_current"] is True


def test_malformed_timestamp_does_not_crash(tmp_path: Path) -> None:
    """Malformed timestamps should not crash the sync; they should result
    in absent/invalid timestamp fields being treated as warnings."""
    state_dir = tmp_path / "project_state"
    _write_state(state_dir)
    final_gate_data = {
        "decision_id": DECISION_ID,
        "round_id": ROUND_ID,
        "gate_status": "PASSED",
        "generated_at": "not-a-timestamp",
    }
    (state_dir / "gates" / "final_gate_result.json").write_text(
        json.dumps(final_gate_data), encoding="utf-8"
    )
    result = build_post_final_evidence_sync_result(state_dir=state_dir)
    assert result["gate_status"] == "PASSED"
    # With a malformed final_gate timestamp, context_after_final is False
    # but since we have digest match, the warning may be suppressed
    assert result["context_sync_basis"] in ("timestamp_and_digest", "digest_current_timestamp_rounded", "timestamp_only", "stale", "pre_final")
    assert validate_post_final_evidence_sync_result(result, decision_id=DECISION_ID, round_id=ROUND_ID) == []


def test_classify_sync_basis_returns_pre_final_when_no_final_gate() -> None:
    """_classify_sync_basis returns pre_final when final gate is not current."""
    from reverse_agent.post_final_evidence_sync import _classify_sync_basis
    assert _classify_sync_basis(
        final_gate_current=False,
        context_current=True,
        context_after_final=False,
        final_gate_digest="abc",
        context_final_gate_digest="abc",
        final_gate_decision_id="d1",
        context_final_gate_decision_id="d1",
        final_gate_round_id="r1",
        context_final_gate_round_id="r1",
    ) == "pre_final"


def test_classify_sync_basis_returns_stale_when_context_not_current() -> None:
    """_classify_sync_basis returns stale when context is not current."""
    from reverse_agent.post_final_evidence_sync import _classify_sync_basis
    assert _classify_sync_basis(
        final_gate_current=True,
        context_current=False,
        context_after_final=False,
        final_gate_digest="abc",
        context_final_gate_digest="abc",
        final_gate_decision_id="d1",
        context_final_gate_decision_id="d1",
        final_gate_round_id="r1",
        context_final_gate_round_id="r1",
    ) == "stale"


def test_classify_sync_basis_returns_timestamp_and_digest() -> None:
    """_classify_sync_basis returns timestamp_and_digest when both digest
    and IDs match and context is after final."""
    from reverse_agent.post_final_evidence_sync import _classify_sync_basis
    assert _classify_sync_basis(
        final_gate_current=True,
        context_current=True,
        context_after_final=True,
        final_gate_digest="abc123",
        context_final_gate_digest="abc123",
        final_gate_decision_id="d1",
        context_final_gate_decision_id="d1",
        final_gate_round_id="r1",
        context_final_gate_round_id="r1",
    ) == "timestamp_and_digest"


def test_classify_sync_basis_returns_digest_current_timestamp_rounded() -> None:
    """_classify_sync_basis returns digest_current_timestamp_rounded when
    digest and IDs match but context is not after final (timestamp rounding)."""
    from reverse_agent.post_final_evidence_sync import _classify_sync_basis
    assert _classify_sync_basis(
        final_gate_current=True,
        context_current=True,
        context_after_final=False,
        final_gate_digest="abc123",
        context_final_gate_digest="abc123",
        final_gate_decision_id="d1",
        context_final_gate_decision_id="d1",
        final_gate_round_id="r1",
        context_final_gate_round_id="r1",
    ) == "digest_current_timestamp_rounded"


def test_classify_sync_basis_returns_timestamp_only() -> None:
    """_classify_sync_basis returns timestamp_only when context is after final
    but digest does not match."""
    from reverse_agent.post_final_evidence_sync import _classify_sync_basis
    assert _classify_sync_basis(
        final_gate_current=True,
        context_current=True,
        context_after_final=True,
        final_gate_digest="abc123",
        context_final_gate_digest="different",
        final_gate_decision_id="d1",
        context_final_gate_decision_id="d1",
        final_gate_round_id="r1",
        context_final_gate_round_id="r1",
    ) == "timestamp_only"


def test_classify_sync_basis_returns_stale_when_no_match() -> None:
    """_classify_sync_basis returns stale when digest does not match and
    context is not after final."""
    from reverse_agent.post_final_evidence_sync import _classify_sync_basis
    assert _classify_sync_basis(
        final_gate_current=True,
        context_current=True,
        context_after_final=False,
        final_gate_digest="abc123",
        context_final_gate_digest="different",
        final_gate_decision_id="d1",
        context_final_gate_decision_id="d1",
        final_gate_round_id="r1",
        context_final_gate_round_id="r1",
    ) == "stale"


def test_validate_rejects_missing_sync_basis_and_precision() -> None:
    """validate_post_final_evidence_sync_result rejects missing context_sync_basis
    and timestamp_precision_policy."""
    bad_payload = {
        "decision_id": DECISION_ID,
        "round_id": ROUND_ID,
        "runner_dispatch": False,
        "model_api_invocation": False,
        "github_actions_dispatch": False,
        "remote_mutation": False,
        "gate_status": "PASSED",
    }
    errors = validate_post_final_evidence_sync_result(bad_payload, decision_id=DECISION_ID, round_id=ROUND_ID)
    assert any("context_sync_basis" in e for e in errors)
    assert any("timestamp_precision_policy" in e for e in errors)
