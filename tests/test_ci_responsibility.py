import fnmatch
import re
from pathlib import Path
import tomllib
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
STATE_GATE_PATH = WORKFLOWS_DIR / "state-gate.yml"
CI_PATH = WORKFLOWS_DIR / "ci.yml"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"

STATE_GATE_GATEWAYS = [
    "project_state/**",
    ".github/workflows/**",
    ".codex-skills/**",
    "docs/prompts/**",
    "reverse_agent/control_plane/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_state.py",
    "reverse_agent/decision_preflight.py",
    "reverse_agent/post_final_evidence_sync.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/project_ci.py",
    "reverse_agent/project_jobs.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/architecture/report_truth.py",
]

PRODUCT_SOURCE_SAMPLES = [
    "reverse_agent/platform_v1/task_service.py",
]

PRODUCT_TEST_SAMPLES = [
    "tests/platform_v1/test_task_service.py",
]

GOVERNANCE_SAMPLES = [
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/project_gate.py",
    "project_state/decision_packet.md",
    ".github/workflows/ci.yml",
]


def _read_state_gate() -> str:
    return STATE_GATE_PATH.read_text(encoding="utf-8")


def _read_ci() -> str:
    return CI_PATH.read_text(encoding="utf-8")


def _read_pyproject() -> dict:
    with PYPROJECT_PATH.open("rb") as handle:
        return tomllib.load(handle)


def _extract_event_block(content: str, event_name: str) -> str | None:
    lines = content.splitlines()
    start = None
    start_indent = None
    for i, line in enumerate(lines):
        if line.startswith(f"  {event_name}:"):
            start = i
            start_indent = len(line) - len(line.lstrip(" "))
            break
    if start is None:
        return None
    block_lines = [lines[start]]
    for j in range(start + 1, len(lines)):
        line = lines[j]
        if not line.strip():
            block_lines.append(line)
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent <= start_indent and line.strip() and not line.strip().startswith("#"):
            break
        block_lines.append(line)
    return "\n".join(block_lines)


def _extract_paths_from_block(block: str) -> list[str]:
    paths = []
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            match = re.match(r'^-\s*["\']?(.*?)["\']?\s*$', stripped)
            if match:
                paths.append(match.group(1))
    return paths


def _path_matches(patterns: list[str], path: str) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


def test_state_gate_push_event_has_paths_filter() -> None:
    content = _read_state_gate()
    push_block = _extract_event_block(content, "push")
    assert push_block is not None
    paths = _extract_paths_from_block(push_block)
    assert paths, "push event block must contain paths filter"
    for required in STATE_GATE_GATEWAYS:
        assert required in paths, f"push.paths missing: {required}"


def test_state_gate_pull_request_event_has_no_paths_filter() -> None:
    content = _read_state_gate()
    pr_block = _extract_event_block(content, "pull_request")
    assert pr_block is not None
    for line in pr_block.splitlines():
        stripped = line.strip()
        if stripped.startswith("paths:"):
            pytest.fail(
                "pull_request event block must NOT contain paths filter; "
                "State Gate must run on all PRs to maintain Path-A reachability"
            )


def test_state_gate_push_no_broad_product_paths() -> None:
    content = _read_state_gate()
    assert "reverse_agent/**" not in content
    assert "tests/**" not in content


def test_state_gate_pull_request_target_bootstrap_job_present() -> None:
    content = _read_state_gate()
    assert "pull_request_target:" in content
    assert "bootstrap-authority:" in content


def test_state_gate_product_source_path_does_not_match() -> None:
    content = _read_state_gate()
    push_block = _extract_event_block(content, "push")
    pr_block = _extract_event_block(content, "pull_request")
    push_paths = _extract_paths_from_block(push_block)
    pr_paths = _extract_paths_from_block(pr_block)
    for sample in PRODUCT_SOURCE_SAMPLES:
        assert not _path_matches(push_paths, sample), (
            f"product source {sample} must NOT trigger push State Gate"
        )
        assert not _path_matches(pr_paths, sample), (
            f"product source {sample} must NOT trigger pull_request State Gate"
        )


def test_state_gate_product_test_path_does_not_match() -> None:
    content = _read_state_gate()
    push_block = _extract_event_block(content, "push")
    pr_block = _extract_event_block(content, "pull_request")
    push_paths = _extract_paths_from_block(push_block)
    pr_paths = _extract_paths_from_block(pr_block)
    for sample in PRODUCT_TEST_SAMPLES:
        assert not _path_matches(push_paths, sample), (
            f"product test {sample} must NOT trigger push State Gate"
        )
        assert not _path_matches(pr_paths, sample), (
            f"product test {sample} must NOT trigger pull_request State Gate"
        )


def test_state_gate_governance_paths_do_match() -> None:
    content = _read_state_gate()
    push_block = _extract_event_block(content, "push")
    push_paths = _extract_paths_from_block(push_block)
    for sample in GOVERNANCE_SAMPLES:
        assert _path_matches(push_paths, sample), (
            f"governance path {sample} must trigger push State Gate"
        )


def test_ci_platform_v1_blocking_gate_present() -> None:
    content = _read_ci()
    assert "Platform V1 blocking gate" in content
    assert "python -m pytest tests/platform_v1" in content


_EXACT_DESELECTED_NODE_IDS: list[str] = [
    (
        "tests/platform_v1/test_merge_intent.py"
        "::TestDecisionImmutability"
        "::test_decision_bytes_unchanged_since_commit"
    ),
    (
        "tests/platform_v1/test_merge_intent.py"
        "::TestDecisionImmutability"
        "::test_decision_commit_precedes_implementation"
    ),
    (
        "tests/platform_v1/test_merge_intent.py"
        "::TestDecisionImmutability"
        "::test_single_decision_commit_in_range"
    ),
    (
        "tests/platform_v1/test_task3c_v6_production_relay.py"
        "::TestCombinedTrustedHostInstalledOpenCodeE2E"
        "::test_real_task_api_opencode_relay_fake_provider_end_to_end"
    ),
    (
        "tests/platform_v1/test_task3c_v4_repairs.py"
        "::TestInstalledOpenCodeFakeProviderSmoke"
        "::test_installed_opencode_fake_provider_end_to_end"
    ),
    (
        "tests/platform_v1/test_task3c_v5_opencode_probe.py"
        "::TestDirectFakeProviderControl"
        "::test_opencode_direct_fake_provider"
    ),
    (
        "tests/platform_v1/test_task3c_v5_opencode_probe.py"
        "::TestRelayFakeProviderRun"
        "::test_opencode_relay_fake_provider"
    ),
]


def _extract_platform_v1_blocking_command(content: str) -> str | None:
    marker = "Platform V1 blocking gate"
    idx = content.find(marker)
    assert idx != -1, "Platform V1 blocking gate section missing"
    section = content[idx:]
    for line in section.splitlines()[1:]:
        if line.strip().startswith("run:"):
            return line.split("run:", 1)[1].strip()
    return None


def _extract_deselected_nodes(cmd: str) -> set[str]:
    nodes: set[str] = set()
    for part in cmd.split():
        if part.startswith("--deselect="):
            nodes.add(part.split("=", 1)[1])
    return nodes


def test_ci_platform_v1_blocking_gate_deselects_exact_seven_nodes() -> None:
    content = _read_ci()
    cmd = _extract_platform_v1_blocking_command(content)
    assert cmd is not None
    deselected = _extract_deselected_nodes(cmd)
    assert deselected == set(_EXACT_DESELECTED_NODE_IDS), (
        f"Platform V1 blocking gate deselected set must exactly match the 7 "
        f"reclassified node IDs; got {sorted(deselected)}"
    )


def test_ci_platform_v1_blocking_gate_exactly_seven_deselects() -> None:
    content = _read_ci()
    cmd = _extract_platform_v1_blocking_command(content)
    assert cmd is not None
    deselected = _extract_deselected_nodes(cmd)
    assert len(deselected) == 7, (
        f"Platform V1 blocking gate must contain exactly 7 --deselect node IDs, "
        f"got {len(deselected)}"
    )


def test_ci_platform_v1_blocking_gate_does_not_broad_ignore_relay_file() -> None:
    content = _read_ci()
    cmd = _extract_platform_v1_blocking_command(content)
    assert cmd is not None
    deselected = _extract_deselected_nodes(cmd)
    relay_node = (
        "tests/platform_v1/test_task3c_v6_production_relay.py"
        "::TestCombinedTrustedHostInstalledOpenCodeE2E"
        "::test_real_task_api_opencode_relay_fake_provider_end_to_end"
    )
    assert relay_node in deselected
    assert deselected != {"tests/platform_v1/test_task3c_v6_production_relay.py"}, (
        "must not broad-ignore test_task3c_v6_production_relay.py"
    )
    assert all(
        ":" in n.split("/")[-1] or "::" in n
        for n in deselected
        if n.endswith("test_task3c_v6_production_relay.py")
    ), "relay-file deselections must be exact node IDs, not whole-file"


def test_ci_platform_v1_blocking_gate_does_not_broad_ignore_merge_intent_file() -> None:
    content = _read_ci()
    cmd = _extract_platform_v1_blocking_command(content)
    assert cmd is not None
    deselected = _extract_deselected_nodes(cmd)
    merge_intent_file_deselects = [
        n for n in deselected
        if n.startswith("tests/platform_v1/test_merge_intent.py")
    ]
    assert len(merge_intent_file_deselects) == 3
    assert "tests/platform_v1/test_merge_intent.py" not in deselected, (
        "must not broad-ignore test_merge_intent.py"
    )
    for node in merge_intent_file_deselects:
        assert "::" in node, (
            f"merge-intent deselection must be an exact node ID, got {node!r}"
        )


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


def _normalize_package_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _find_dependency_entries(
    dependencies: list[str], normalized_name: str
) -> list[str]:
    entries = []
    for dep in dependencies:
        match = re.match(r"^([A-Za-z0-9_.-]+)", dep)
        if match and _normalize_package_name(match.group(1)) == normalized_name:
            entries.append(dep)
    return entries


def _assert_exact_pin_policy(
    dependencies: list[str], package_name: str
) -> None:
    entries = _find_dependency_entries(dependencies, package_name)
    assert entries, f"{package_name} dependency entry missing"
    assert len(entries) == 1, f"{package_name} must appear exactly once"
    entry = entries[0]
    name_match = re.match(r"^([A-Za-z0-9_.-]+)", entry)
    assert name_match is not None
    pkg_name = name_match.group(1)
    remainder = entry[name_match.end():]
    if not remainder.startswith("=="):
        raise AssertionError(
            f"{package_name} must use exact == pin, got: {entry}"
        )
    version_part = remainder[2:].strip()
    version_part = re.split(r"[,;@\s]", version_part, maxsplit=1)[0].strip()
    assert version_part, f"{package_name} has empty version after =="


def test_langgraph_exact_pin_policy() -> None:
    pyproject = _read_pyproject()
    dependencies = pyproject["project"]["dependencies"]
    _assert_exact_pin_policy(dependencies, "langgraph")


def test_langgraph_checkpoint_sqlite_exact_pin_policy() -> None:
    pyproject = _read_pyproject()
    dependencies = pyproject["project"]["dependencies"]
    _assert_exact_pin_policy(dependencies, "langgraph-checkpoint-sqlite")


def _assert_exact_pin_rejects(dependencies: list[str], package_name: str) -> None:
    with pytest.raises(AssertionError):
        _assert_exact_pin_policy(dependencies, package_name)


def _assert_exact_pin_accepts(dependencies: list[str], package_name: str) -> None:
    _assert_exact_pin_policy(dependencies, package_name)


def test_exact_pin_policy_rejects_duplicate_dependency_entry() -> None:
    _assert_exact_pin_rejects(
        [
            "langgraph==SENTINEL",
            "langgraph>=OTHER_SENTINEL",
        ],
        "langgraph",
    )


def test_exact_pin_policy_rejects_range_only_dependency() -> None:
    _assert_exact_pin_rejects(
        ["langgraph>=SENTINEL"],
        "langgraph",
    )


def test_exact_pin_policy_rejects_unpinned_dependency() -> None:
    _assert_exact_pin_rejects(
        ["langgraph"],
        "langgraph",
    )


def test_exact_pin_policy_accepts_unique_exact_pin() -> None:
    _assert_exact_pin_accepts(
        ["langgraph==SENTINEL"],
        "langgraph",
    )


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
