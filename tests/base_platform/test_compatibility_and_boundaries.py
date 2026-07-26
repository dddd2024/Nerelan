from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from reverse_agent.base_platform import (
    BasePlatformError,
    CompatibilitySnapshot,
    ReadOnlyCompatibilityAdapter,
)


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "reverse_agent" / "base_platform"
FORBIDDEN_IMPORT_ROOTS = {
    "github",
    "httpx",
    "langgraph",
    "openai",
    "requests",
    "reverse_agent.local_reverse_runtime",
    "selenium",
}


def test_compatibility_adapter_is_read_only_versioned_and_non_authoritative() -> None:
    source = {
        "schema_version": 1,
        "repository": "owner/repo",
        "nested": {"operations": ["read"]},
    }
    original = json.loads(json.dumps(source))
    snapshot = ReadOnlyCompatibilityAdapter().adapt(
        source,
        source_type="legacy-work-item",
        source_identity="owner/repo#1",
    )

    assert source == original
    assert snapshot.adapter_version == "0.1"
    assert snapshot.authoritative is False
    source["nested"]["operations"].append("mutated")
    assert snapshot.payload["nested"]["operations"] == ("read",)
    with pytest.raises(TypeError):
        snapshot.payload["new"] = "forbidden"


def test_compatibility_snapshot_round_trip_remains_non_authoritative() -> None:
    snapshot = ReadOnlyCompatibilityAdapter().adapt(
        {"schema_version": 1, "value": "read-only"},
        source_type="legacy",
        source_identity="legacy:1",
    )

    decoded = CompatibilitySnapshot.from_mapping(json.loads(snapshot.canonical_bytes()))
    assert decoded == snapshot
    assert decoded.authoritative is False


def test_compatibility_adapter_fails_closed_on_unknown_version() -> None:
    with pytest.raises(BasePlatformError) as captured:
        ReadOnlyCompatibilityAdapter().adapt(
            {"schema_version": 999},
            source_type="legacy",
            source_identity="legacy:999",
        )

    assert captured.value.code == "UNSUPPORTED_COMPATIBILITY_VERSION"


def test_compatibility_snapshot_cannot_claim_authority() -> None:
    with pytest.raises(BasePlatformError) as captured:
        CompatibilitySnapshot(
            identity="compat:bad",
            adapter_version="0.1",
            source_type="legacy",
            source_identity="legacy:1",
            payload={},
            authoritative=True,
        )

    assert captured.value.code == "COMPATIBILITY_CANNOT_AUTHORIZE"


def test_base_platform_has_no_forbidden_integration_imports() -> None:
    observed: set[str] = set()
    for path in PACKAGE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                observed.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                observed.add(node.module)

    forbidden = {
        imported
        for imported in observed
        if any(
            imported == root or imported.startswith(f"{root}.")
            for root in FORBIDDEN_IMPORT_ROOTS
        )
    }
    assert forbidden == set()


def test_base_platform_tests_do_not_write_project_state_or_runtime_evidence() -> None:
    write_methods = {"mkdir", "open", "rename", "replace", "touch", "unlink", "write_bytes", "write_text"}
    for path in Path(__file__).parent.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            function_name = (
                node.func.attr
                if isinstance(node.func, ast.Attribute)
                else node.func.id
                if isinstance(node.func, ast.Name)
                else ""
            )
            if function_name not in write_methods:
                continue
            literal_arguments = " ".join(
                argument.value
                for argument in node.args
                if isinstance(argument, ast.Constant) and isinstance(argument.value, str)
            )
            assert "project_state" not in literal_arguments
            assert "runtime_evidence" not in literal_arguments
