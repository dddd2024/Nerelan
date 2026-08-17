import re
from pathlib import Path
import tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
STATE_GATE_PATH = WORKFLOWS_DIR / "state-gate.yml"
CI_PATH = WORKFLOWS_DIR / "ci.yml"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


def _read_state_gate() -> str:
    return STATE_GATE_PATH.read_text(encoding="utf-8")


def _read_ci() -> str:
    return CI_PATH.read_text(encoding="utf-8")


def _read_pyproject() -> dict:
    with PYPROJECT_PATH.open("rb") as handle:
        return tomllib.load(handle)


def test_state_gate_push_no_broad_product_paths() -> None:
    content = _read_state_gate()
    assert "reverse_agent/**" not in content
    assert "tests/**" not in content


def test_state_gate_still_has_governance_paths() -> None:
    content = _read_state_gate()
    assert "project_state/**" in content
    assert ".github/workflows/**" in content
    assert ".codex-skills/**" in content
    assert "docs/prompts/**" in content


def test_state_gate_pull_request_target_bootstrap_job_present() -> None:
    content = _read_state_gate()
    assert "pull_request_target:" in content
    assert "bootstrap-authority:" in content


def test_ci_platform_v1_blocking_gate_present() -> None:
    content = _read_ci()
    assert "Platform V1 blocking gate" in content
    assert "python -m pytest tests/platform_v1 -q" in content


def test_ci_repository_wide_diagnostic_nonblocking() -> None:
    content = _read_ci()
    diagnostic_section = content.split("Repository-wide diagnostic")
    assert len(diagnostic_section) >= 2
    diagnostic_body = diagnostic_section[1]
    assert "continue-on-error: true" in diagnostic_body


def test_pyproject_packaging_semantic_properties() -> None:
    pyproject = _read_pyproject()
    assert pyproject["project"]["name"] == "reverse-agent"
    assert pyproject["project"]["requires-python"] == ">=3.13"
    assert pyproject["build-system"]["build-backend"] == "setuptools.build_meta"


def test_pyproject_required_dependency_packages() -> None:
    pyproject = _read_pyproject()
    dependencies = pyproject["project"]["dependencies"]
    names = _extract_package_names(dependencies)
    assert "langgraph" in names
    assert "langgraph-checkpoint-sqlite" in names


def test_pyproject_dependencies_are_explicitly_pinned() -> None:
    pyproject = _read_pyproject()
    dependencies = pyproject["project"]["dependencies"]
    for dep in dependencies:
        assert any(
            operator in dep for operator in ("==", ">=", "<=", ">", "<", "!=", "~=")
        ), f"dependency not pinned: {dep}"
    names = _extract_package_names(dependencies)
    assert "langgraph" in names
    assert "langgraph-checkpoint-sqlite" in names


def test_pyproject_test_extra_pytest_range() -> None:
    pyproject = _read_pyproject()
    test_deps = pyproject["project"]["optional-dependencies"]["test"]
    assert any(dep.startswith("pytest") for dep in test_deps)
    pytest_deps = [dep for dep in test_deps if dep.startswith("pytest")]
    assert len(pytest_deps) == 1
    assert ">=8" in pytest_deps[0]
    assert "<9" in pytest_deps[0]


def _extract_package_names(dependencies: list[str]) -> set[str]:
    names = set()
    for dep in dependencies:
        match = re.match(r"^([A-Za-z0-9_.-]+)", dep)
        if match:
            names.add(match.group(1).lower().replace("_", "-"))
    return names
