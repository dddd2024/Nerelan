import json
from pathlib import Path

from reverse_agent.project_audits import (
    AUDIT_OUTCOMES,
    validate_audit_file,
    validate_audit_payload,
    validate_audits_dir,
)


def _valid_audit(*, audit_id: str = "audit_valid", outcome: str = "ACCEPTED") -> dict:
    return {
        "schema_version": 1,
        "audit_id": audit_id,
        "audited_decision_id": "decision_valid",
        "audited_round_id": "round_valid",
        "audited_report_id": "codex_report_valid",
        "outcome": outcome,
        "mainline": "engineering_branch",
        "created_by": "test",
        "created_at_local": "2026-06-29",
        "remote_mutation_scope": "none",
    }


def _write_audit(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# AUDIT_RESULT\n\n"
        "```json audit_summary\n"
        f"{json.dumps(payload, indent=2)}\n"
        "```\n",
        encoding="utf-8",
    )


def test_validate_audit_payload_accepts_valid_summary() -> None:
    result = validate_audit_payload(_valid_audit(outcome="REWORK_REQUIRED"))

    assert result["validation_status"] == "PASSED"
    assert result["outcome"] == "REWORK_REQUIRED"
    assert "BLOCKED" in AUDIT_OUTCOMES


def test_validate_audit_payload_rejects_missing_required_field() -> None:
    payload = _valid_audit()
    del payload["audited_round_id"]

    result = validate_audit_payload(payload)

    assert result["validation_status"] == "FAILED"
    assert any("missing required fields" in error for error in result["errors"])


def test_validate_audit_payload_rejects_unknown_outcome() -> None:
    payload = _valid_audit(outcome="MAYBE")

    result = validate_audit_payload(payload)

    assert result["validation_status"] == "FAILED"
    assert any("outcome must be one of" in error for error in result["errors"])


def test_validate_audit_file_reads_markdown_summary(tmp_path: Path) -> None:
    audit_path = tmp_path / "project_state" / "audits" / "audit_valid.md"
    _write_audit(audit_path, _valid_audit())

    result = validate_audit_file(audit_path)

    assert result["validation_status"] == "PASSED"
    assert result["audit_id"] == "audit_valid"


def test_validate_audits_dir_accepts_missing_directory(tmp_path: Path) -> None:
    state_dir = tmp_path / "project_state"
    state_dir.mkdir()

    result = validate_audits_dir(state_dir)

    assert result["validation_status"] == "PASSED"
    assert result["audit_count"] == 0
    assert result["validated_paths"] == []
    assert result["outcome_counts"]["ACCEPTED"] == 0


def test_validate_audits_dir_reports_invalid_markdown_without_mutating(tmp_path: Path) -> None:
    audits_dir = tmp_path / "project_state" / "audits"
    audits_dir.mkdir(parents=True)
    bad_path = audits_dir / "bad.md"
    original = "# AUDIT_RESULT\n\nmissing summary\n"
    bad_path.write_text(original, encoding="utf-8")

    result = validate_audits_dir(tmp_path / "project_state")

    assert result["validation_status"] == "FAILED"
    assert result["audit_count"] == 0
    assert result["validated_paths"] == []
    assert any("bad.md" in error for error in result["errors"])
    assert bad_path.read_text(encoding="utf-8") == original


def test_validate_audits_dir_rejects_duplicate_audit_ids(tmp_path: Path) -> None:
    audits_dir = tmp_path / "project_state" / "audits"
    _write_audit(audits_dir / "first.md", _valid_audit(audit_id="audit_duplicate"))
    _write_audit(audits_dir / "second.md", _valid_audit(audit_id="audit_duplicate"))

    result = validate_audits_dir(tmp_path / "project_state")

    assert result["validation_status"] == "FAILED"
    assert result["audit_count"] == 2
    assert len(result["validated_paths"]) == 2
    assert any("duplicate audit_id 'audit_duplicate'" in error for error in result["errors"])


def test_validate_audits_dir_returns_outcome_counts_and_paths(tmp_path: Path) -> None:
    audits_dir = tmp_path / "project_state" / "audits"
    _write_audit(audits_dir / "accepted.md", _valid_audit(audit_id="audit_a", outcome="ACCEPTED"))
    _write_audit(audits_dir / "blocked.md", _valid_audit(audit_id="audit_b", outcome="BLOCKED"))

    result = validate_audits_dir(tmp_path / "project_state")

    assert result["validation_status"] == "PASSED"
    assert result["audit_count"] == 2
    assert result["validated_paths"] == [
        "project_state/audits/accepted.md",
        "project_state/audits/blocked.md",
    ]
    assert result["outcome_counts"]["ACCEPTED"] == 1
    assert result["outcome_counts"]["BLOCKED"] == 1


def test_validate_audits_dir_accepts_current_audit_record() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    audit_path = (
        repo_root
        / "project_state"
        / "audits"
        / "audit_20260629_rework_required_clean_baseline_jobs_inventory_gate.md"
    )
    result = validate_audit_file(audit_path)

    assert result["validation_status"] == "PASSED"
    assert (
        result["audit_id"]
        == "audit_20260629_rework_required_clean_baseline_jobs_inventory_gate"
    )
    assert result["outcome"] == "REWORK_REQUIRED"
    assert result["mainline"] == "engineering_branch"
