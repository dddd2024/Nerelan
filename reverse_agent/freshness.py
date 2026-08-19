"""Deterministic maturity-component freshness registry validation."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


class FreshnessError(ValueError):
    pass


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise FreshnessError(f"invalid_checked_at:{value}") from exc


def validate_registry(
    registry_path: str | Path,
    *,
    repository_root: str | Path | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    path = Path(registry_path).resolve()
    root = Path(repository_root).resolve() if repository_root else path.parent.parent.resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FreshnessError("freshness_registry_unreadable") from exc
    if not isinstance(payload, Mapping) or payload.get("schema_version") != 1:
        raise FreshnessError("freshness_registry_schema_invalid")
    entries = payload.get("components")
    if not isinstance(entries, list) or not entries:
        raise FreshnessError("freshness_registry_components_required")
    current = today or datetime.now(timezone.utc).date()
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    failures: list[str] = []
    for raw in entries:
        if not isinstance(raw, Mapping):
            raise FreshnessError("freshness_component_invalid")
        identifier = str(raw.get("id", "")).strip()
        version = str(raw.get("current_version", "")).strip()
        source_url = str(raw.get("source_url", "")).strip()
        owner = str(raw.get("owner", "")).strip()
        evidence_paths = raw.get("evidence_paths", [])
        if (
            not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}", identifier)
            or identifier in seen
            or not version
            or not source_url.startswith("https://")
            or not owner
            or not isinstance(evidence_paths, list)
            or not evidence_paths
        ):
            raise FreshnessError(f"freshness_component_contract_invalid:{identifier or 'unknown'}")
        seen.add(identifier)
        max_age = int(raw.get("max_age_days", 0))
        if max_age < 1 or max_age > 365:
            raise FreshnessError(f"freshness_max_age_invalid:{identifier}")
        checked = _parse_date(str(raw.get("checked_at", "")))
        age_days = (current - checked).days
        if age_days < 0:
            raise FreshnessError(f"freshness_checked_at_in_future:{identifier}")
        stale = age_days > max_age
        evidence_missing: list[str] = []
        version_missing: list[str] = []
        for relative in evidence_paths:
            rel = Path(str(relative))
            if rel.is_absolute() or ".." in rel.parts:
                raise FreshnessError(f"freshness_evidence_path_unsafe:{identifier}")
            evidence = (root / rel).resolve()
            if root not in evidence.parents and evidence != root:
                raise FreshnessError(f"freshness_evidence_path_unsafe:{identifier}")
            if not evidence.exists():
                evidence_missing.append(str(relative))
                continue
            if bool(raw.get("require_version_in_evidence", True)):
                try:
                    text = evidence.read_text(encoding="utf-8") if evidence.is_file() else evidence.name
                except OSError:
                    text = ""
                if version not in text:
                    version_missing.append(str(relative))
        status = "PASS"
        if stale or evidence_missing or version_missing:
            status = "FAIL"
            failures.append(identifier)
        results.append({
            "id": identifier,
            "current_version": version,
            "age_days": age_days,
            "max_age_days": max_age,
            "stale": stale,
            "evidence_missing": evidence_missing,
            "version_missing": version_missing,
            "status": status,
        })
    return {
        "status": "PASS" if not failures else "FAIL",
        "registry": str(path),
        "checked_on": current.isoformat(),
        "components": results,
        "failures": failures,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", default="governance/freshness-registry.json")
    parser.add_argument("--repository-root", default=".")
    args = parser.parse_args(argv)
    try:
        result = validate_registry(args.registry, repository_root=args.repository_root)
    except FreshnessError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
