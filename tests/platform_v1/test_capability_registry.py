import json

import pytest

from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.run_store import TaskStoreError


def test_builtin_registry_advertises_mature_reused_components():
    response = CapabilityRegistry().response()
    ids = {item["id"] for item in response["capabilities"]}
    assert {"spec-kit-planning", "langgraph-orchestration", "opencode-executor", "agent-canvas"} <= ids
    assert response["digest"]


def test_pack_manifest_is_metadata_only_and_rejects_sensitive_fields(tmp_path):
    (tmp_path / "safe.json").write_text(json.dumps({
        "id": "repo-linter", "name": "Repo linter", "operations": ["lint_repository"]
    }), encoding="utf-8")
    result = CapabilityRegistry(pack_dir=tmp_path).response()
    assert any(item["id"] == "repo-linter" and item["source"] == "pack:safe.json" for item in result["capabilities"])
    (tmp_path / "unsafe.json").write_text(json.dumps({
        "id": "unsafe-pack", "operations": ["unsafe_run"], "api_token": "sentinel"
    }), encoding="utf-8")
    with pytest.raises(TaskStoreError, match="sensitive_control_field_rejected"):
        CapabilityRegistry(pack_dir=tmp_path).list()
