from datetime import date
import json

import pytest

from reverse_agent.freshness import FreshnessError, validate_registry


def test_repository_freshness_registry_is_current_and_evidenced():
    result = validate_registry(
        "governance/freshness-registry.json", repository_root=".", today=date(2026, 8, 19)
    )
    assert result["status"] == "PASS"
    assert len(result["components"]) == 4


def test_stale_or_unsafe_registry_fails_closed(tmp_path):
    evidence = tmp_path / "component.txt"
    evidence.write_text("1.0.0", encoding="utf-8")
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({
        "schema_version": 1,
        "components": [{
            "id": "sample-component", "current_version": "1.0.0",
            "source_url": "https://example.invalid/releases", "owner": "owner",
            "checked_at": "2026-01-01", "max_age_days": 30,
            "evidence_paths": ["component.txt"],
        }],
    }), encoding="utf-8")
    result = validate_registry(registry, repository_root=tmp_path, today=date(2026, 8, 19))
    assert result["status"] == "FAIL"
    assert result["components"][0]["stale"] is True

    payload = json.loads(registry.read_text(encoding="utf-8"))
    payload["components"][0]["evidence_paths"] = ["../outside.txt"]
    registry.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(FreshnessError, match="unsafe"):
        validate_registry(registry, repository_root=tmp_path, today=date(2026, 1, 2))
