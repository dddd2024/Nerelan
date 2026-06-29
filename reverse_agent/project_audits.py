"""Read-only audit record validation for project_state/audits/*.md."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping


AUDIT_SCHEMA_VERSION = 1
AUDIT_OUTCOMES = {
    "ACCEPTED",
    "ACCEPTED_WITH_LIMITATIONS",
    "REWORK_REQUIRED",
    "BLOCKED",
}
REQUIRED_FIELDS = {
    "schema_version",
    "audit_id",
    "audited_decision_id",
    "audited_round_id",
    "outcome",
    "mainline",
}
OPTIONAL_FIELDS = {
    "audited_report_id",
    "created_by",
    "created_at_local",
    "remote_mutation_scope",
}
_AUDIT_SUMMARY_RE = re.compile(
    r"```json\s+audit_summary\s*\n(?P<body>.*?)\n```",
    re.DOTALL,
)


def _string_value(payload: Mapping[str, Any], field: str, errors: list[str]) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty string")
        return ""
    return value.strip()


def _project_relative(path: Path, state_dir: Path) -> str:
    try:
        return path.resolve().relative_to(state_dir.parent.resolve()).as_posix()
    except (OSError, ValueError):
        return path.as_posix()


def load_audit_summary(path: str | Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    match = _AUDIT_SUMMARY_RE.search(text)
    if not match:
        raise ValueError("missing fenced json audit_summary block")
    payload = json.loads(match.group("body"))
    if not isinstance(payload, dict):
        raise ValueError("audit_summary must be a JSON object")
    return payload


def validate_audit_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    missing = sorted(field for field in REQUIRED_FIELDS if field not in payload)
    if missing:
        errors.append(f"missing required fields: {missing}")

    schema_version = payload.get("schema_version")
    if schema_version != AUDIT_SCHEMA_VERSION:
        errors.append(f"schema_version must be {AUDIT_SCHEMA_VERSION}")

    audit_id = _string_value(payload, "audit_id", errors)
    audited_decision_id = _string_value(payload, "audited_decision_id", errors)
    audited_round_id = _string_value(payload, "audited_round_id", errors)
    mainline = _string_value(payload, "mainline", errors)
    outcome = _string_value(payload, "outcome", errors).upper()
    if outcome and outcome not in AUDIT_OUTCOMES:
        errors.append(f"outcome must be one of {sorted(AUDIT_OUTCOMES)}")

    optional: dict[str, str] = {}
    for field in sorted(OPTIONAL_FIELDS):
        value = payload.get(field)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be a non-empty string when present")
            continue
        optional[field] = value.strip()

    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "validation_status": "FAILED" if errors else "PASSED",
        "errors": errors,
        "warnings": warnings,
        "audit_id": audit_id,
        "audited_decision_id": audited_decision_id,
        "audited_round_id": audited_round_id,
        "outcome": outcome,
        "mainline": mainline,
        "recognized_optional_fields": optional,
    }


def validate_audit_file(path: str | Path) -> dict[str, Any]:
    return validate_audit_payload(load_audit_summary(path))


def validate_audits_dir(state_dir: str | Path) -> dict[str, Any]:
    root = Path(state_dir)
    audits_dir = root / "audits"
    errors: list[str] = []
    warnings: list[str] = []
    validated_paths: list[str] = []
    outcome_counts = {outcome: 0 for outcome in sorted(AUDIT_OUTCOMES)}
    seen_audit_ids: dict[str, str] = {}

    if not audits_dir.exists():
        return {
            "schema_version": AUDIT_SCHEMA_VERSION,
            "validation_status": "PASSED",
            "errors": errors,
            "warnings": warnings,
            "audits_dir": _project_relative(audits_dir, root),
            "audit_count": 0,
            "validated_paths": validated_paths,
            "outcome_counts": outcome_counts,
            "audits": [],
        }
    if not audits_dir.is_dir():
        errors.append(f"audits path is not a directory: {_project_relative(audits_dir, root)}")
        return {
            "schema_version": AUDIT_SCHEMA_VERSION,
            "validation_status": "FAILED",
            "errors": errors,
            "warnings": warnings,
            "audits_dir": _project_relative(audits_dir, root),
            "audit_count": 0,
            "validated_paths": validated_paths,
            "outcome_counts": outcome_counts,
            "audits": [],
        }

    audits: list[dict[str, Any]] = []
    for audit_path in sorted(audits_dir.glob("*.md")):
        rel_path = _project_relative(audit_path, root)
        try:
            result = validate_audit_file(audit_path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{rel_path}: {exc}")
            continue

        errors.extend(f"{rel_path}: {error}" for error in result["errors"])
        audit_id = str(result.get("audit_id") or "")
        if audit_id:
            if audit_id in seen_audit_ids:
                errors.append(
                    f"duplicate audit_id {audit_id!r}: {seen_audit_ids[audit_id]} and {rel_path}"
                )
            else:
                seen_audit_ids[audit_id] = rel_path
        outcome = str(result.get("outcome") or "")
        if outcome in outcome_counts:
            outcome_counts[outcome] += 1
        if result["validation_status"] == "PASSED":
            validated_paths.append(rel_path)
        audits.append({
            "path": rel_path,
            "audit_id": audit_id,
            "audited_decision_id": result.get("audited_decision_id", ""),
            "audited_round_id": result.get("audited_round_id", ""),
            "outcome": outcome,
            "mainline": result.get("mainline", ""),
            "validation_status": result["validation_status"],
            "errors": result["errors"],
        })

    return {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "validation_status": "FAILED" if errors else "PASSED",
        "errors": errors,
        "warnings": warnings,
        "audits_dir": _project_relative(audits_dir, root),
        "audit_count": len(audits),
        "validated_paths": validated_paths,
        "outcome_counts": outcome_counts,
        "audits": audits,
    }
