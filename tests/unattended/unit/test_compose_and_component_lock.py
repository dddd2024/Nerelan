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
    executor_key_secret_preflight,
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
    ordinary = compose.split("\n  reverse-agent-worker:\n", 1)[1].split(
        "\n  sandbox-controller-worker:\n", 1
    )[0]
    controller = compose.split(
        "\n  sandbox-controller-worker:\n", 1
    )[1].split("\n  litellm-database:\n", 1)[0]
    assert "/var/run/docker.sock" not in ordinary
    assert "/var/run/docker.sock" in controller
    assert "profiles: [runtime-proof]" in ordinary
    assert "profiles: [runtime-proof]" in controller
    assert "source: litellm_executor_key" not in ordinary
    assert "source: litellm_executor_key" in controller
    assert "\n  model-executor:\n" in compose
    assert "    internal: true" in compose
    assert "aliases: [litellm-executor]" in compose
    for service in ("temporal", "postgresql", "temporal-ui"):
        block = compose.split(f"\n  {service}:\n", 1)[1].split("\n  ", 1)[0]
        assert "model-executor" not in block


def test_runtime_profile_resolves_two_socket_separated_workers(
    tmp_path: Path,
) -> None:
    provider_file = tmp_path / "provider"
    provider_file.write_text("non-provider-placeholder", encoding="utf-8")
    executor_file = tmp_path / "executor"
    executor_file.write_text("sk-non-provider-placeholder", encoding="utf-8")
    workspace_root = tmp_path / "attempts"
    workspace_root.mkdir()
    environment = os.environ.copy()
    environment.update(
        {
            "POSTGRES_PASSWORD": "synthetic-postgres",
            "LITELLM_DATABASE_PASSWORD": "synthetic-database",
            "LITELLM_MASTER_KEY": "synthetic-master",
            "LITELLM_SALT_KEY": "synthetic-salt",
            "UNATTENDED_OPENAI_API_KEY_FILE": str(provider_file),
            "UNATTENDED_LITELLM_EXECUTOR_KEY_FILE": str(executor_file),
            "UNATTENDED_HOST_WORKSPACE_ROOT": str(workspace_root),
            "COMPOSE_PROJECT_NAME": "issue82-runtime-proof",
        }
    )
    completed = subprocess.run(
        (
            "docker",
            "compose",
            "--profile",
            "runtime-proof",
            "-f",
            str(DEPLOY / "compose.yaml"),
            "config",
            "--format",
            "json",
        ),
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    services = json.loads(completed.stdout)["services"]
    ordinary = services["reverse-agent-worker"]
    controller = services["sandbox-controller-worker"]
    assert ordinary.get("volumes", []) == []
    assert ordinary.get("secrets", []) == []
    assert any(
        mount["source"] == "/var/run/docker.sock"
        and mount["target"] == "/var/run/docker.sock"
        for mount in controller["volumes"]
    )
    assert controller["secrets"] == [
        {
            "source": "litellm_executor_key",
            "target": "litellm_executor_key",
            "mode": "0400",
        }
    ]
    assert ordinary["networks"] == {"control": None}
    assert controller["networks"] == {"control": None}


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
    assert compose.count("tr -d '\\\\r'") == 4


def test_resolved_compose_mounts_provider_secret_only_into_litellm(
    tmp_path: Path,
) -> None:
    provider_value = secrets.token_urlsafe(32)
    secret_file = tmp_path / "provider-material"
    secret_file.write_text(provider_value, encoding="utf-8")
    secret_file.chmod(0o600)
    executor_key_file = tmp_path / "executor-material"
    executor_key_file.write_text(
        f"sk-{secrets.token_urlsafe(32)}",
        encoding="utf-8",
    )
    executor_key_file.chmod(0o600)
    environment = os.environ.copy()
    environment.update(
        {
            "POSTGRES_PASSWORD": "synthetic-postgres",
            "LITELLM_DATABASE_PASSWORD": "synthetic_database_password",
            "LITELLM_MASTER_KEY": "synthetic-litellm",
            "LITELLM_SALT_KEY": "synthetic-salt",
            "UNATTENDED_OPENAI_API_KEY_FILE": str(secret_file),
            "UNATTENDED_LITELLM_EXECUTOR_KEY_FILE": str(executor_key_file),
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
    provider_mounted = {
        name
        for name, service in services.items()
        if any(
            secret.get("source") == "openai_api_key"
            for secret in service.get("secrets", [])
        )
    }
    executor_key_mounted = {
        name
        for name, service in services.items()
        if any(
            secret.get("source") == "litellm_executor_key"
            for secret in service.get("secrets", [])
        )
    }
    assert provider_mounted == {"litellm"}
    assert executor_key_mounted == {"litellm-key-bootstrap"}
    assert services["litellm"]["secrets"] == [
        {
            "source": "openai_api_key",
            "target": "openai_api_key",
            "mode": "0400",
        }
    ]
    assert resolved["secrets"]["openai_api_key"]["file"] == str(secret_file)
    assert resolved["secrets"]["litellm_executor_key"]["file"] == str(
        executor_key_file
    )
    for service in services.values():
        environment_values = service.get("environment", {})
        assert "OPENAI_API_KEY" not in environment_values
        assert provider_value not in json.dumps(environment_values, sort_keys=True)
    assert set(services["litellm"]["networks"]) == {"control", "model-executor"}
    assert resolved["networks"]["model-executor"]["internal"] is True
    assert "LITELLM_MASTER_KEY" not in services["agent-canvas"].get(
        "environment", {}
    )
    assert services["litellm"]["environment"]["DATABASE_URL"].startswith(
        "postgresql://litellm:"
    )
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


def test_executor_key_preflight_is_presence_only(tmp_path: Path) -> None:
    key_file = tmp_path / "executor-key"
    key_file.write_text(f"sk-{secrets.token_urlsafe(32)}", encoding="utf-8")
    key_file.chmod(0o600)

    report = executor_key_secret_preflight(key_file, repository_root=ROOT)
    rendered = json.dumps(report, sort_keys=True)

    assert report["executor_key"] == "PRESENT"
    assert report["checks"]["regular_file"] == "PASS"
    assert str(key_file) not in rendered


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


def test_litellm_virtual_key_boundary_is_fixed_and_database_is_separate() -> None:
    compose = (DEPLOY / "compose.yaml").read_text(encoding="utf-8")
    config = (DEPLOY / "litellm.config.example.yaml").read_text(encoding="utf-8")
    bootstrap = (DEPLOY / "litellm-key-bootstrap.py").read_text(encoding="utf-8")
    database = (
        DEPLOY / "postgres" / "ensure-litellm-database.sh"
    ).read_text(encoding="utf-8")

    assert 'database_url: os.environ/DATABASE_URL' in config
    assert "disable_spend_logs: false" in config
    assert "CREATE DATABASE litellm OWNER litellm" in database
    assert "NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION" in database
    assert "REVOKE ALL ON DATABASE temporal FROM litellm" in database
    assert "REVOKE CONNECT ON DATABASE temporal FROM PUBLIC" in database
    assert '"models": ["unattended-v0"]' in bootstrap
    assert '"max_budget": 1.0' in bootstrap
    assert '"rpm_limit": 10' in bootstrap
    assert '"tpm_limit": 50000' in bootstrap
    assert '"key_type": "llm_api"' in bootstrap
    assert '"/v1/models"' in bootstrap
    assert "/key/generate" in bootstrap
    assert "/key/update" in bootstrap
    assert "litellm_executor_key" in compose
