from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
from pathlib import Path

import pytest

from reverse_agent.unattended.component_lock import (
    COMPONENTS,
    PROJECTION_SHA256,
    load_component_lock,
)
from reverse_agent.unattended.secrets import (
    _strict_posix_permissions,
    provider_secret_preflight,
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
    for port in (7233, 8080, 4000, 3000):
        assert (
            f'"${{UNATTENDED_BIND_ADDRESS:-127.0.0.1}}:{port}:{port}"'
            in compose
        )
    assert '"7233:7233"' not in compose
    assert '"8080:8080"' not in compose
    assert '"4000:4000"' not in compose
    assert '"3000:3000"' not in compose


def test_compose_separates_control_from_internal_model_executor_network() -> None:
    compose = (DEPLOY / "compose.yaml").read_text(encoding="utf-8")

    assert "\n  agent-server:\n" not in compose
    assert "/var/run/docker.sock" not in compose
    assert "\n  model-executor:\n" in compose
    assert "    internal: true" in compose
    assert "aliases: [litellm-executor]" in compose
    for service in ("temporal", "postgresql", "temporal-ui"):
        block = compose.split(f"\n  {service}:\n", 1)[1].split("\n  ", 1)[0]
        assert "model-executor" not in block


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


def test_resolved_compose_mounts_provider_secret_only_into_litellm(
    tmp_path: Path,
) -> None:
    provider_value = secrets.token_urlsafe(32)
    secret_file = tmp_path / "provider-material"
    secret_file.write_text(provider_value, encoding="utf-8")
    secret_file.chmod(0o600)
    environment = os.environ.copy()
    environment.update(
        {
            "POSTGRES_PASSWORD": "synthetic-postgres",
            "LITELLM_MASTER_KEY": "synthetic-litellm",
            "LITELLM_SALT_KEY": "synthetic-salt",
            "UNATTENDED_OPENAI_API_KEY_FILE": str(secret_file),
        }
    )
    completed = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(DEPLOY / "compose.yaml"),
            "config",
            "--format",
            "json",
        ],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    resolved = json.loads(completed.stdout)
    services = resolved["services"]
    mounted = {
        name
        for name, service in services.items()
        if service.get("secrets")
    }
    assert mounted == {"litellm"}
    assert services["litellm"]["secrets"] == [
        {
            "source": "openai_api_key",
            "target": "openai_api_key",
            "mode": "0400",
        }
    ]
    assert resolved["secrets"]["openai_api_key"]["file"] == str(secret_file)
    for service in services.values():
        environment_values = service.get("environment", {})
        assert "OPENAI_API_KEY" not in environment_values
        assert provider_value not in json.dumps(environment_values, sort_keys=True)
    assert set(services["litellm"]["networks"]) == {"control", "model-executor"}
    assert resolved["networks"]["model-executor"]["internal"] is True
    assert provider_value not in completed.stdout


def test_provider_secret_preflight_is_value_and_path_safe(
    tmp_path: Path,
) -> None:
    provider_value = secrets.token_urlsafe(32)
    secret_file = tmp_path / "provider-material"
    secret_file.write_text(provider_value, encoding="utf-8")
    secret_file.chmod(0o600)
    report = provider_secret_preflight(secret_file, repository_root=ROOT)
    rendered = json.dumps(report, sort_keys=True)
    assert report["provider_secret"] == "PRESENT"
    assert report["checks"]["regular_file"] == "PASS"
    assert report["checks"]["outside_repository"] == "PASS"
    assert report["checks"]["permissions_0600"] == (
        "PASS" if os.name == "posix" else "FAIL"
    )
    assert provider_value not in rendered
    assert str(secret_file) not in rendered


def test_provider_secret_preflight_rejects_missing_repo_file_and_bad_mode(
    tmp_path: Path,
) -> None:
    missing = provider_secret_preflight(None, repository_root=ROOT)
    assert missing["provider_secret"] == "MISSING"
    assert missing["status"] == "FAIL"

    repo_file = DEPLOY / ".env.example"
    inside = provider_secret_preflight(repo_file, repository_root=ROOT)
    assert inside["provider_secret"] == "PRESENT"
    assert inside["checks"]["outside_repository"] == "FAIL"

    bad_mode = tmp_path / "bad-mode"
    bad_mode.write_text(secrets.token_urlsafe(32), encoding="utf-8")
    bad_mode.chmod(0o644)
    permissive = provider_secret_preflight(bad_mode, repository_root=ROOT)
    assert permissive["provider_secret"] == "PRESENT"
    assert permissive["checks"]["permissions_0600"] == "FAIL"
    assert _strict_posix_permissions("posix", 0o600) is True
    assert _strict_posix_permissions("posix", 0o644) is False
    assert _strict_posix_permissions("nt", 0o600) is False


def test_provider_configuration_has_no_env_value_slot_and_fixed_launcher() -> None:
    env_example = (DEPLOY / ".env.example").read_text(encoding="utf-8")
    compose = (DEPLOY / "compose.yaml").read_text(encoding="utf-8")
    launcher = (DEPLOY / "litellm-entrypoint.sh").read_text(encoding="utf-8")
    assert "\nOPENAI_API_KEY=" not in env_example
    assert "UNATTENDED_OPENAI_API_KEY_FILE=" in env_example
    assert "OPENAI_API_KEY:" not in compose
    assert "/run/secrets/openai_api_key" in launcher
    assert "exec litellm --config /app/config.yaml --port 4000" in launcher
    assert "echo" not in launcher
    assert "print" not in launcher
