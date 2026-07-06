"""Schema-only readiness artifacts for a future SQLite read index."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .project_state import read_decision_meta


STATE_INDEX_READINESS_SCHEMA_VERSION = 1
STATE_INDEX_SCHEMA_PATH = "project_state/gates/state_index_readiness_schema.json"
STATE_INDEX_PLAN_PATH = "project_state/gates/state_index_readiness_plan.json"
STATE_INDEX_RESULT_PATH = "project_state/gates/state_index_readiness_result.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _identity(state_dir: Path, artifact_name: str, artifact_path: str) -> dict[str, Any]:
    decision = read_decision_meta(state_dir)
    round_id = str(decision.get("round_id") or "")
    return {
        "schema_version": STATE_INDEX_READINESS_SCHEMA_VERSION,
        "artifact_name": artifact_name,
        "artifact_path": artifact_path,
        "decision_id": str(decision.get("decision_id") or ""),
        "round_id": round_id,
        "report_id": f"codex_report_{round_id.removeprefix('round_')}" if round_id else "",
        "mainline": str(decision.get("mainline") or ""),
        "generated_at": _now_iso(),
    }


def _db_files(state_dir: Path) -> list[str]:
    names: list[str] = []
    for pattern in ("*.sqlite", "*.sqlite3", "*.db"):
        for path in sorted(state_dir.glob(pattern)):
            if path.is_file():
                names.append(f"project_state/{path.name}")
    return names


def build_state_index_readiness_schema(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    tables = {
        "decisions": ["decision_id", "round_id", "status", "mainline", "state_digest"],
        "rounds": ["round_id", "decision_id", "report_id", "closeout_status", "archive_manifest_path"],
        "artifacts": ["artifact_path", "artifact_name", "round_id", "role", "sha256", "freshness"],
        "executions": ["command", "kind", "round_id", "exit_code", "expected_exit_codes"],
        "audits": ["audit_item", "status", "evidence_path", "round_id"],
        "workstreams": ["workstream_id", "family", "status", "active_round_id"],
        "backlog_notices": ["notice_id", "classification", "blocking_current_round", "source_path"],
    }
    payload = {
        **_identity(state_dir_path, "state_index_readiness_schema.json", STATE_INDEX_SCHEMA_PATH),
        "gate_name": "state-index-readiness-schema",
        "schema_status": "SCHEMA_ONLY",
        "sqlite_read_index_only": True,
        "project_state_remains_audit_fact_source": True,
        "database_file_created": False,
        "migration_created": False,
        "tables": tables,
        "generated_artifacts": [STATE_INDEX_SCHEMA_PATH],
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "state_index_readiness_schema.json", payload)
    return payload


def build_state_index_readiness_plan(
    *,
    state_dir: str | Path = "project_state",
    schema: Mapping[str, Any] | None = None,
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    schema_payload = schema or build_state_index_readiness_schema(state_dir=state_dir_path, write_result=write_result)
    payload = {
        **_identity(state_dir_path, "state_index_readiness_plan.json", STATE_INDEX_PLAN_PATH),
        "gate_name": "state-index-readiness-plan",
        "plan_status": "READY_FOR_FUTURE_DECISION",
        "sqlite_read_index_only": True,
        "project_state_remains_audit_fact_source": True,
        "database_creation_allowed_this_round": False,
        "migration_allowed_this_round": False,
        "future_required_steps": [
            "separate APPROVED database/read-index decision",
            "command-plan explicitly authorizes schema migration",
            "project_state remains source of audit truth",
            "final-check proves generated DB is derived and disposable",
        ],
        "schema_table_count": len(schema_payload.get("tables") or {}),
        "generated_artifacts": [STATE_INDEX_PLAN_PATH, STATE_INDEX_SCHEMA_PATH],
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "state_index_readiness_plan.json", payload)
    return payload


def build_state_index_readiness_result(
    *,
    state_dir: str | Path = "project_state",
    write_result: bool = True,
) -> dict[str, Any]:
    state_dir_path = Path(state_dir)
    schema = build_state_index_readiness_schema(state_dir=state_dir_path, write_result=write_result)
    plan = build_state_index_readiness_plan(state_dir=state_dir_path, schema=schema, write_result=write_result)
    db_files = _db_files(state_dir_path)
    errors: list[str] = []
    if db_files:
        errors.append("database files already exist in project_state root")
    if schema.get("project_state_remains_audit_fact_source") is not True:
        errors.append("schema does not preserve project_state as fact source")
    if plan.get("database_creation_allowed_this_round") is not False:
        errors.append("plan allows database creation this round")
    payload = {
        **_identity(state_dir_path, "state_index_readiness_result.json", STATE_INDEX_RESULT_PATH),
        "gate_name": "state-index-readiness",
        "gate_status": "PASSED" if not errors else "FAILED",
        "readiness_status": "SCHEMA_READY_NO_DATABASE" if not errors else "FAILED",
        "sqlite_read_index_only": True,
        "project_state_remains_audit_fact_source": True,
        "database_file_created": False,
        "database_files_present": db_files,
        "migration_created": False,
        "checks": [
            {
                "name": "schema_defines_required_tables",
                "status": "PASS" if len(schema.get("tables") or {}) >= 7 else "FAIL",
                "table_names": sorted((schema.get("tables") or {}).keys()),
            },
            {
                "name": "no_database_file_created",
                "status": "PASS" if not db_files else "FAIL",
                "database_files_present": db_files,
            },
            {
                "name": "project_state_fact_source_preserved",
                "status": "PASS",
                "detail": "SQLite is a future query/read index only",
            },
        ],
        "errors": errors,
        "generated_artifacts": [STATE_INDEX_SCHEMA_PATH, STATE_INDEX_PLAN_PATH, STATE_INDEX_RESULT_PATH],
    }
    if write_result:
        _write_json(state_dir_path / "gates" / "state_index_readiness_result.json", payload)
    return payload


def validate_state_index_readiness_result(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("gate_status") != "PASSED":
        errors.append("state index readiness gate did not pass")
    if payload.get("sqlite_read_index_only") is not True:
        errors.append("sqlite_read_index_only must be true")
    if payload.get("project_state_remains_audit_fact_source") is not True:
        errors.append("project_state fact source must be preserved")
    if payload.get("database_file_created") is not False:
        errors.append("database_file_created must be false")
    if payload.get("database_files_present") != []:
        errors.append("database_files_present must be empty")
    return errors
