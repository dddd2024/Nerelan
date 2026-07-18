"""Tests for pyproject.toml packaging metadata.

Validates that the packaging metadata is minimal, justified, and avoids
speculative dependencies, as required by the v6 Decision's Required Audit
item #13.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_pyproject() -> dict:
    pyproject_path = _repo_root() / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml must exist at repository root"
    with pyproject_path.open("rb") as fh:
        return tomllib.load(fh)


def test_pyproject_has_build_system():
    data = _load_pyproject()
    assert "build-system" in data, "pyproject.toml must declare [build-system]"
    build = data["build-system"]
    assert "requires" in build, "[build-system] must declare requires"
    assert "setuptools" in " ".join(build["requires"]), (
        "build-system should use setuptools for minimal packaging"
    )
    assert "build-backend" in build, "[build-system] must declare build-backend"


def test_pyproject_project_name_is_valid():
    data = _load_pyproject()
    assert "project" in data, "pyproject.toml must declare [project]"
    project = data["project"]
    name = project.get("name", "")
    assert name, "[project] name must be non-empty"
    # PEP 508 normalized name: letters, digits, - and .
    normalized = name.lower().replace("_", "-")
    assert normalized == "reverse-agent", f"expected reverse-agent, got {name}"


def test_pyproject_version_is_pep440():
    data = _load_pyproject()
    version = data.get("project", {}).get("version", "")
    assert version, "[project] version must be non-empty"
    # Minimal PEP 440 check: contains at least one digit and a dot
    assert any(ch.isdigit() for ch in version), (
        f"version must contain digits, got {version}"
    )
    assert "." in version, f"version must contain a dot, got {version}"


def test_pyproject_requires_python_is_313_plus():
    data = _load_pyproject()
    requires_python = data.get("project", {}).get("requires-python", "")
    assert requires_python, "[project] requires-python must be declared"
    assert "3.13" in requires_python, (
        f"requires-python should target >=3.13, got {requires_python}"
    )


def test_pyproject_dependencies_are_minimal():
    data = _load_pyproject()
    dependencies = data.get("project", {}).get("dependencies", [])
    # Only pytest is a justified runtime dependency for this governance package
    assert isinstance(dependencies, list), "dependencies must be a list"
    dep_names = [d.split(">")[0].split("<")[0].split("=")[0].split("!")[0].strip()
                 for d in dependencies]
    assert "pytest" in dep_names, "pytest should be a declared dependency"
    # Avoid speculative heavy dependencies
    forbidden = {"numpy", "scipy", "pandas", "torch", "tensorflow", "flask", "django"}
    found_forbidden = set(dep_names) & forbidden
    assert not found_forbidden, (
        f"speculative dependencies not allowed: {found_forbidden}"
    )


def test_pyproject_optional_dependencies_are_bounded():
    data = _load_pyproject()
    optional = data.get("project", {}).get("optional-dependencies", {})
    if not optional:
        pytest.skip("no optional dependencies declared")
    for group, deps in optional.items():
        assert isinstance(deps, list), f"optional group {group} must be a list"
        for dep in deps:
            assert isinstance(dep, str), f"optional dep in {group} must be a string"


def test_pyproject_package_discovery_includes_reverse_agent():
    data = _load_pyproject()
    tool_setuptools = data.get("tool", {}).get("setuptools", {})
    packages_find = tool_setuptools.get("packages", {}).get("find", {})
    include = packages_find.get("include", [])
    assert any("reverse_agent" in pkg for pkg in include), (
        "package discovery must include reverse_agent*"
    )
    exclude = packages_find.get("exclude", [])
    # Tests and project_state should not be packaged
    assert any("tests" in exc for exc in exclude), (
        "package discovery should exclude tests*"
    )


def test_pyproject_no_heavy_packaging_frameworks():
    data = _load_pyproject()
    build_requires = data.get("build-system", {}).get("requires", [])
    joined = " ".join(build_requires).lower()
    heavy = {"poetry", "flit", "hatchling", "pdm"}
    found = [h for h in heavy if h in joined]
    assert not found, (
        f"heavy packaging frameworks not allowed: {found}; use setuptools"
    )


def test_module_imports_under_python_313():
    """Verify the package imports cleanly under the current Python."""
    if sys.version_info < (3, 13):
        pytest.skip("test requires Python 3.13+")
    import importlib
    for module_name in (
        "reverse_agent.project_gate",
        "reverse_agent.project_state",
        "reverse_agent.post_final_evidence_sync",
        "reverse_agent.decision_preflight",
    ):
        mod = importlib.import_module(module_name)
        assert mod is not None, f"failed to import {module_name}"
