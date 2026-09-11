from __future__ import annotations

import hashlib
import json

import pytest

from reverse_agent.platform_v1.environment_discovery import (
    MAX_PARSED_SOURCE_BYTES,
    EnvironmentDiscoveryError,
    discover_environment_requirements,
)


def _write(root, relative: str, content: str | bytes) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def _runtime(result, runtime: str):
    return [item for item in result.runtimes if item.runtime == runtime]


def test_empty_repository_returns_stable_non_blocked_contract(tmp_path) -> None:
    first = discover_environment_requirements(tmp_path)
    second = discover_environment_requirements(tmp_path)

    assert first == second
    assert first.runtimes == ()
    assert first.tools == ()
    assert first.locks == ()
    assert first.setup_sources == ()
    assert first.conflicts == ()
    assert first.blocked is False
    assert len(first.digest) == 64


def test_python_range_and_exact_pin_preserve_exact_source_provenance(tmp_path) -> None:
    pyproject = b'[project]\nname = "fixture"\nrequires-python = ">=3.13"\n'
    _write(tmp_path, "pyproject.toml", pyproject)
    _write(tmp_path, ".python-version", "3.13.2\n")

    result = discover_environment_requirements(tmp_path)
    python = _runtime(result, "python")

    assert [(item.constraint_kind, item.constraint) for item in python] == [
        ("exact", "3.13.2"),
        ("range", ">=3.13"),
    ]
    by_path = {item.source.path: item for item in python}
    assert by_path["pyproject.toml"].source.sha256 == hashlib.sha256(pyproject).hexdigest()
    assert by_path[".python-version"].source.kind == "version:python"
    assert result.conflicts == ()


def test_package_json_node_package_manager_and_lock_are_deterministic(tmp_path) -> None:
    _write(
        tmp_path,
        "package.json",
        json.dumps(
            {
                "engines": {"node": ">=20 <23"},
                "packageManager": "pnpm@9.15.0+sha512.abcdef",
            }
        ),
    )
    lock = b"lockfileVersion: '9.0'\n"
    _write(tmp_path, "pnpm-lock.yaml", lock)

    first = discover_environment_requirements(tmp_path)
    second = discover_environment_requirements(tmp_path)

    assert first == second
    assert [(item.constraint_kind, item.constraint) for item in _runtime(first, "node")] == [
        ("range", ">=20 <23")
    ]
    assert [(item.tool, item.constraint) for item in first.tools] == [
        ("pnpm", "9.15.0")
    ]
    assert [(item.path, item.kind) for item in first.locks] == [
        ("pnpm-lock.yaml", "lock:node:pnpm")
    ]
    assert first.locks[0].sha256 == hashlib.sha256(lock).hexdigest()


def test_cargo_go_and_tool_versions_are_discovered_without_execution(tmp_path) -> None:
    _write(tmp_path, "Cargo.toml", '[package]\nname = "demo"\nrust-version = "1.85"\n')
    _write(tmp_path, "go.mod", "module example.test/demo\n\ngo 1.24.0\ngodebug default=go1.21\n")
    _write(
        tmp_path,
        ".tool-versions",
        "python 3.13.2\nnodejs 22.14.0\nrust 1.85.1\ngolang 1.24.1\nruby 3.4.1\n",
    )

    result = discover_environment_requirements(tmp_path)

    assert ("rust", "minimum", "1.85") in {
        (item.runtime, item.constraint_kind, item.constraint)
        for item in result.runtimes
    }
    assert ("go", "minimum", "1.24.0") in {
        (item.runtime, item.constraint_kind, item.constraint)
        for item in result.runtimes
    }
    assert {
        (item.runtime, item.constraint)
        for item in result.runtimes
        if item.constraint_kind == "exact"
    } == {
        ("python", "3.13.2"),
        ("node", "22.14.0"),
        ("rust", "1.85.1"),
        ("go", "1.24.1"),
    }
    assert all(item.runtime != "ruby" for item in result.runtimes)


def test_identical_duplicate_exact_pins_are_deduplicated(tmp_path) -> None:
    _write(tmp_path, ".tool-versions", "python 3.13.2\npython 3.13.2\n")

    result = discover_environment_requirements(tmp_path)

    assert [(item.runtime, item.constraint) for item in result.runtimes] == [
        ("python", "3.13.2")
    ]
    assert result.conflicts == ()
    assert result.blocked is False


@pytest.mark.parametrize(
    ("version_file", "tool_line", "runtime"),
    [
        (".python-version", "python 3.12.9\n", "python"),
        (".node-version", "nodejs 20.19.0\n", "node"),
    ],
)
def test_contradictory_exact_pins_produce_typed_conflict(
    tmp_path, version_file: str, tool_line: str, runtime: str
) -> None:
    version = "3.13.2\n" if runtime == "python" else "22.14.0\n"
    _write(tmp_path, version_file, version)
    _write(tmp_path, ".tool-versions", tool_line)

    result = discover_environment_requirements(tmp_path)

    assert result.blocked is True
    assert len(result.conflicts) == 1
    conflict = result.conflicts[0]
    assert conflict.code == "ENV_VERSION_CONFLICT"
    assert conflict.subject == runtime
    assert len(conflict.values) == 2


@pytest.mark.parametrize(
    ("relative", "content"),
    [
        ("pyproject.toml", "[project\nname = 'broken'"),
        ("package.json", "{not-json"),
    ],
)
def test_malformed_supported_manifests_fail_with_sanitized_code(
    tmp_path, relative: str, content: str
) -> None:
    _write(tmp_path, relative, content)

    with pytest.raises(EnvironmentDiscoveryError) as caught:
        discover_environment_requirements(tmp_path)

    assert caught.value.code == "ENV_DISCOVERY_SOURCE_INVALID"
    assert caught.value.source == relative
    assert "broken" not in str(caught.value)
    assert "not-json" not in str(caught.value)


def test_oversized_parsed_source_fails_before_parser(tmp_path) -> None:
    _write(
        tmp_path,
        "package.json",
        b"{" + (b" " * MAX_PARSED_SOURCE_BYTES) + b"}",
    )

    with pytest.raises(EnvironmentDiscoveryError) as caught:
        discover_environment_requirements(tmp_path)

    assert caught.value.code == "ENV_DISCOVERY_SOURCE_TOO_LARGE"
    assert caught.value.source == "package.json"


def test_changed_lock_bytes_change_result_identity(tmp_path) -> None:
    _write(tmp_path, "uv.lock", "version = 1\n")
    first = discover_environment_requirements(tmp_path)

    _write(tmp_path, "uv.lock", "version = 2\n")
    second = discover_environment_requirements(tmp_path)

    assert first.locks[0].sha256 != second.locks[0].sha256
    assert first.digest != second.digest


def test_setup_metadata_is_opaque_and_scripts_env_secrets_are_not_admitted(
    tmp_path,
) -> None:
    marker = tmp_path / "should-not-exist"
    _write(
        tmp_path,
        "setup.sh",
        f"#!/bin/sh\nprintf touched > {marker}\n",
    )
    _write(tmp_path, ".env", "PRIVATE_TOKEN=SECRET_SENTINEL_ENV_797\n")
    _write(
        tmp_path,
        ".devcontainer/devcontainer.json",
        "{ definitely-not-json SECRET_SENTINEL_DEVCONTAINER_797",
    )
    _write(tmp_path, "Dockerfile", "RUN echo SECRET_SENTINEL_DOCKER_797\n")
    _write(
        tmp_path,
        ".github/workflows/copilot-setup-steps.yml",
        "steps:\n  - run: echo SECRET_SENTINEL_COPILOT_797\n",
    )

    result = discover_environment_requirements(tmp_path)
    serialized = json.dumps(result.to_dict(), sort_keys=True)

    assert not marker.exists()
    assert [source.path for source in result.setup_sources] == [
        ".devcontainer/devcontainer.json",
        ".github/workflows/copilot-setup-steps.yml",
        "Dockerfile",
    ]
    assert ".env" not in serialized
    assert "setup.sh" not in serialized
    assert "SECRET_SENTINEL" not in serialized


def test_repository_escaping_supported_symlink_fails_closed(tmp_path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside-package.json"
    outside.write_text('{"engines":{"node":">=22"}}', encoding="utf-8")
    link = tmp_path / "package.json"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable on this host")

    try:
        with pytest.raises(EnvironmentDiscoveryError) as caught:
            discover_environment_requirements(tmp_path)
        assert caught.value.code == "ENV_SOURCE_OUTSIDE_REPOSITORY"
        assert caught.value.source == "package.json"
    finally:
        outside.unlink(missing_ok=True)


def test_unsupported_runtime_value_is_sanitized(tmp_path) -> None:
    secret = "SECRET_SENTINEL_RANGE_797"
    _write(
        tmp_path,
        "pyproject.toml",
        f'[project]\nname = "fixture"\nrequires-python = ">=3.13;{secret}"\n',
    )

    with pytest.raises(EnvironmentDiscoveryError) as caught:
        discover_environment_requirements(tmp_path)

    assert caught.value.code == "ENV_DISCOVERY_UNSUPPORTED_VALUE"
    assert secret not in str(caught.value)
