from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from reverse_agent.unattended.component_lock import (
    COMPONENTS,
    PROJECTION_SHA256,
    load_component_lock,
)

ROOT = Path(__file__).resolve().parents[3]
DEPLOY = ROOT / "deploy" / "unattended"


def test_component_lock_exact_inventory_projection_and_independent_fields() -> None:
    lock_path = DEPLOY / "component-lock.yaml"
    lock = load_component_lock(lock_path)
    assert lock["projection_sha256"] == PROJECTION_SHA256
    assert {entry["component"] for entry in lock["components"]} == COMPONENTS
    assert len(lock["components"]) == 8
    assert hashlib.sha256(lock_path.read_bytes()).hexdigest()


def test_component_lock_rejects_floating_or_projection_drift(
    tmp_path: Path,
) -> None:
    lock = json.loads((DEPLOY / "component-lock.yaml").read_text(encoding="utf-8"))
    lock["components"][0]["container_image"] = "docker.io/temporalio/server:latest"
    drifted = tmp_path / "component-lock.yaml"
    drifted.write_text(json.dumps(lock), encoding="utf-8")
    with pytest.raises(ValueError, match="floating_component"):
        load_component_lock(drifted)


def test_all_published_ports_default_to_loopback() -> None:
    compose = (DEPLOY / "compose.yaml").read_text(encoding="utf-8")
    for port in (7233, 8080, 4000, 8000, 3000):
        assert (
            f'"${{UNATTENDED_BIND_ADDRESS:-127.0.0.1}}:{port}:{port}"'
            in compose
        )
    assert '"7233:7233"' not in compose
    assert '"8080:8080"' not in compose
    assert '"4000:4000"' not in compose
    assert '"8000:8000"' not in compose
    assert '"3000:3000"' not in compose


def test_temporal_bootstrap_is_automatic_and_idempotent() -> None:
    compose = (DEPLOY / "compose.yaml").read_text(encoding="utf-8")
    schema = (
        DEPLOY / "temporal" / "scripts" / "setup-postgres.sh"
    ).read_text(encoding="utf-8")
    namespace = (
        DEPLOY / "temporal" / "scripts" / "ensure-default-namespace.sh"
    ).read_text(encoding="utf-8")
    assert "temporal-namespace:" in compose
    assert "condition: service_completed_successfully" in compose
    assert "--quiet create" in schema
    assert "--quiet setup-schema" in schema
    assert "update-schema" in schema
    assert "namespace describe --namespace default" in namespace
    assert "namespace create --namespace default" in namespace
    assert not compose.startswith("name:")
    assert compose.count("tr -d '\\\\r'") == 2
