"""Tests for context packet domain awareness (Phase A)."""

from __future__ import annotations

import json
from pathlib import Path

from reverse_agent.project_context import (
    DOMAIN_TAXONOMY,
    build_context_domain_awareness,
    classify_context_field_domain,
    detect_stale_domain_facts,
)


DECISION_ID = "decision_test_context_domain_v1"
ROUND_ID = "round_test_context_domain_v1"


def _write_decision_packet(state_dir: Path) -> None:
    (state_dir / "context").mkdir(parents=True, exist_ok=True)
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
  "follows_last_decision_id": "decision_prev",
  "follows_last_round_id": "round_prev"
}}
```
""",
        encoding="utf-8",
    )


def _write_context_packet(state_dir: Path, payload: dict) -> None:
    (state_dir / "context").mkdir(parents=True, exist_ok=True)
    (state_dir / "context" / "current_context_packet.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def test_domain_taxonomy_covers_all_expected_domains() -> None:
    expected = {
        "reverse_solving",
        "project_governance",
        "user_solve_layer",
        "evidence_replay",
        "web_workbench",
        "tool_integration",
        "automation_runner",
        "training_dataset",
        "engineering_branch",
    }
    assert set(DOMAIN_TAXONOMY.keys()) == expected
    for domain, meta in DOMAIN_TAXONOMY.items():
        assert "mainline" in meta
        assert "scope" in meta
        assert "description" in meta


def test_classify_context_field_domain_governance_fields() -> None:
    assert classify_context_field_domain("decision_id") == "project_governance"
    assert classify_context_field_domain("round_id") == "project_governance"
    assert classify_context_field_domain("mainline") == "project_governance"
    assert classify_context_field_domain("report_id") == "project_governance"


def test_classify_context_field_domain_planner_fields() -> None:
    assert (
        classify_context_field_domain("planner_context.current_mainline")
        == "project_governance"
    )
    assert (
        classify_context_field_domain("planner_context.command_authority")
        == "project_governance"
    )


def test_classify_context_field_domain_reverse_solving_fields() -> None:
    assert (
        classify_context_field_domain("planner_context.artifact_freshness")
        == "reverse_solving"
    )
    assert (
        classify_context_field_domain("negative_results_constraints")
        == "reverse_solving"
    )


def test_classify_context_field_domain_unknown_returns_empty() -> None:
    assert classify_context_field_domain("unknown_field") == ""
    assert classify_context_field_domain("") == ""


def test_detect_stale_domain_facts_current_context_no_stale() -> None:
    payload = {
        "decision_id": DECISION_ID,
        "round_id": ROUND_ID,
        "mainline": "project_governance",
    }
    stale = detect_stale_domain_facts(
        payload,
        current_decision_id=DECISION_ID,
        current_round_id=ROUND_ID,
        current_mainline="project_governance",
    )
    assert stale == []


def test_detect_stale_domain_facts_stale_decision_id() -> None:
    payload = {
        "decision_id": "decision_old_v1",
        "round_id": ROUND_ID,
        "mainline": "project_governance",
    }
    stale = detect_stale_domain_facts(
        payload,
        current_decision_id=DECISION_ID,
        current_round_id=ROUND_ID,
        current_mainline="project_governance",
    )
    assert len(stale) == 1
    assert stale[0]["field"] == "decision_id"
    assert stale[0]["observed_value"] == "decision_old_v1"
    assert stale[0]["expected_value"] == DECISION_ID


def test_detect_stale_domain_facts_stale_round_id() -> None:
    payload = {
        "decision_id": DECISION_ID,
        "round_id": "round_old_v1",
        "mainline": "project_governance",
    }
    stale = detect_stale_domain_facts(
        payload,
        current_decision_id=DECISION_ID,
        current_round_id=ROUND_ID,
        current_mainline="project_governance",
    )
    assert len(stale) == 1
    assert stale[0]["field"] == "round_id"


def test_detect_stale_domain_facts_stale_mainline() -> None:
    payload = {
        "decision_id": DECISION_ID,
        "round_id": ROUND_ID,
        "mainline": "engineering_branch",
    }
    stale = detect_stale_domain_facts(
        payload,
        current_decision_id=DECISION_ID,
        current_round_id=ROUND_ID,
        current_mainline="project_governance",
    )
    assert len(stale) == 1
    assert stale[0]["field"] == "mainline"
    assert stale[0]["observed_value"] == "engineering_branch"


def test_detect_stale_domain_facts_auditor_stale_detected() -> None:
    payload = {
        "decision_id": DECISION_ID,
        "round_id": ROUND_ID,
        "mainline": "project_governance",
        "auditor_context": {
            "stale_context_detected": True,
        },
    }
    stale = detect_stale_domain_facts(
        payload,
        current_decision_id=DECISION_ID,
        current_round_id=ROUND_ID,
        current_mainline="project_governance",
    )
    assert len(stale) == 1
    assert stale[0]["field"] == "auditor_context.stale_context_detected"


def test_detect_stale_domain_facts_empty_current_ids_no_stale() -> None:
    """When current IDs are empty, no stale facts are reported (legacy compat)."""
    payload = {
        "decision_id": "decision_old",
        "round_id": "round_old",
        "mainline": "engineering_branch",
    }
    stale = detect_stale_domain_facts(payload)
    assert stale == []


def test_build_context_domain_awareness_current_context(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_decision_packet(state_dir)
    _write_context_packet(
        state_dir,
        {
            "decision_id": DECISION_ID,
            "round_id": ROUND_ID,
            "mainline": "project_governance",
            "auditor_context": {"stale_context_detected": False},
            "planner_context": {"command_authority": "project_state/gates/command_plan.json"},
        },
    )

    awareness = build_context_domain_awareness(state_dir=state_dir)

    assert awareness["context_packet_present"] is True
    assert awareness["current_decision_id"] == DECISION_ID
    assert awareness["current_round_id"] == ROUND_ID
    assert awareness["current_mainline"] == "project_governance"
    assert awareness["context_decision_id"] == DECISION_ID
    assert awareness["context_round_id"] == ROUND_ID
    assert awareness["stale_fact_count"] == 0
    assert awareness["stale_domain_facts"] == []
    assert "project_governance" in awareness["represented_domains"]
    assert awareness["policy"]["stale_domain_facts_are_non_blocking"] is True


def test_build_context_domain_awareness_stale_context(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_decision_packet(state_dir)
    _write_context_packet(
        state_dir,
        {
            "decision_id": "decision_old_v1",
            "round_id": "round_old_v1",
            "mainline": "engineering_branch",
            "auditor_context": {"stale_context_detected": True},
        },
    )

    awareness = build_context_domain_awareness(state_dir=state_dir)

    assert awareness["context_packet_present"] is True
    assert awareness["stale_fact_count"] >= 3
    stale_fields = {f["field"] for f in awareness["stale_domain_facts"]}
    assert "decision_id" in stale_fields
    assert "round_id" in stale_fields
    assert "mainline" in stale_fields


def test_build_context_domain_awareness_missing_context_packet(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_decision_packet(state_dir)
    # No context packet written

    awareness = build_context_domain_awareness(state_dir=state_dir)

    assert awareness["context_packet_present"] is False
    assert awareness["stale_fact_count"] == 0
    assert awareness["policy"]["legacy_context_packets_remain_readable"] is True


def test_build_context_domain_awareness_phase_a_policy(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()
    _write_decision_packet(state_dir)
    _write_context_packet(
        state_dir,
        {
            "decision_id": DECISION_ID,
            "round_id": ROUND_ID,
            "mainline": "project_governance",
        },
    )

    awareness = build_context_domain_awareness(state_dir=state_dir)

    assert awareness["phase"] == "A"
    policy = awareness["policy"]
    assert policy["stale_domain_facts_are_non_blocking"] is True
    assert policy["legacy_context_packets_remain_readable"] is True
    assert policy["no_context_files_moved_or_deleted"] is True
    assert policy["domain_awareness_is_advisory_only"] is True
