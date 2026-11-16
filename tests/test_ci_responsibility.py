import ast
import os
import re
import runpy
import subprocess
import sys
from pathlib import Path
import tomllib
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
CI_PATH = WORKFLOWS_DIR / "ci.yml"
FRONTEND_PLAYWRIGHT_PATH = WORKFLOWS_DIR / "frontend-playwright.yml"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


def test_installed_opencode_markers_match_exact_existing_exclusions() -> None:
    marked = set()
    attribute_count = 0
    for path in (REPO_ROOT / "tests").rglob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        attribute_count += sum(
            isinstance(node, ast.Attribute) and ast.unparse(node) == "pytest.mark.installed_opencode"
            for node in ast.walk(tree)
        )
        for cls in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
            for method in cls.body:
                if isinstance(method, ast.FunctionDef) and any(
                    ast.unparse(decorator) == "pytest.mark.installed_opencode"
                    for decorator in method.decorator_list
                ):
                    marked.add(f"{path.relative_to(REPO_ROOT).as_posix()}::{cls.name}::{method.name}")
    assert marked == set(_EXACT_DESELECTED_NODE_IDS)
    assert attribute_count == 4, "Only the four method markers are permitted; no broad marking"
    assert any(marker.startswith("installed_opencode:") for marker in _read_pyproject()["tool"]["pytest"]["ini_options"]["markers"])


@pytest.mark.parametrize(
    ("options", "expected", "exit_code"),
    [
        ([], ["test_selection.py::test_default"], 0),
        (["-m", "installed_opencode"], [], 5),
        (["--run-installed-opencode"], ["test_selection.py::test_default", "test_selection.py::test_installed"], 0),
        (["--run-installed-opencode", "-m", "installed_opencode"], ["test_selection.py::test_installed"], 0),
    ],
)
def test_installed_tool_collection_requires_explicit_opt_in(tmp_path, options, expected, exit_code) -> None:
    (tmp_path / "conftest.py").write_text((REPO_ROOT / "tests/conftest.py").read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "pytest.ini").write_text("[pytest]\nmarkers =\n    installed_opencode: synthetic collection test\n", encoding="utf-8")
    (tmp_path / "test_selection.py").write_text(
        "import pytest\ndef test_default():\n    pass\n"
        "@pytest.mark.installed_opencode\ndef test_installed():\n    pytest.fail('must never execute')\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_PLUGINS", None)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    result = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", *options],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == exit_code, result.stdout + result.stderr
    assert [line for line in result.stdout.splitlines() if line.startswith("test_selection.py::")] == expected


@pytest.mark.parametrize(
    ("exit_code", "tests", "failures", "errors", "skipped", "passed"),
    [("0", 2, 0, 0, 1, True), ("0", 2, 0, 0, 2, False), ("1", 1, 1, 1, 0, False), ("2", 1, 0, 1, 0, False),
     ("5", 0, 0, 0, 0, False), ("", 2, 0, 0, 0, False), ("0", 1, 1, 0, 0, False)],
)
def test_diagnostic_summary_reports_raw_counts_and_actual_exit(tmp_path, exit_code, tests, failures, errors, skipped, passed) -> None:
    render = runpy.run_path(str(REPO_ROOT / "scripts/ci_test_summary.py"))["render_summary"]
    report = tmp_path / "junit.xml"
    report.write_text(f'<testsuites><testsuite tests="{tests}" failures="{failures}" errors="{errors}" skipped="{skipped}"/></testsuites>', encoding="utf-8")
    summary = render(report, exit_code)
    for name, count in [("tests", tests), ("failures", failures), ("errors", errors), ("skipped", skipped)]:
        assert f"| {name} | {count} |" in summary
    assert ("**Selected tests passed.**" in summary) == passed
    assert "| passed |" not in summary, "JUnit double failures must not produce inferred passed counts"
    assert f"<code>{exit_code or 'unavailable'}</code>" in summary
    assert "excluded and were not executed" in summary


@pytest.mark.parametrize("content", [None, "broken XML", "<testsuites/>", '<testsuite tests="-1" failures="0" errors="0" skipped="0"/>'])
def test_diagnostic_summary_missing_or_invalid_report_is_unknown(tmp_path, content) -> None:
    render = runpy.run_path(str(REPO_ROOT / "scripts/ci_test_summary.py"))["render_summary"]
    report = tmp_path / "junit.xml"
    if content is not None:
        report.write_text(content, encoding="utf-8")
    summary = render(report, "0")
    assert "statistics unavailable" in summary
    assert "success is unproven" in summary
    assert "**Selected tests passed.**" not in summary


def test_diagnostic_workflow_preserves_exit_and_publishes_evidence() -> None:
    content = _read_ci()
    assert 'pytest_exit=$?' in content
    assert 'exit "$pytest_exit"' in content
    assert '--junitxml=ci-diagnostic.xml' in content
    assert '-m "not installed_opencode"' in content
    assert 'steps.repository_diagnostic.outputs.exit_code' in content
    assert '"$GITHUB_STEP_SUMMARY"' in content
    assert 'path: ci-diagnostic.xml' in content
    assert "if: always() && steps.repository_diagnostic.outcome != 'skipped'" in content

def _read_ci() -> str:
    return CI_PATH.read_text(encoding="utf-8")


def _read_pyproject() -> dict:
    with PYPROJECT_PATH.open("rb") as handle:
        return tomllib.load(handle)


def test_ci_platform_v1_blocking_gate_present() -> None:
    content = _read_ci()
    assert "Platform V1 blocking gate" in content
    assert "python -m pytest tests/platform_v1" in content


_EXACT_DESELECTED_NODE_IDS: list[str] = [
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


def test_ci_platform_v1_blocking_gate_deselects_exact_four_nodes() -> None:
    content = _read_ci()
    cmd = _extract_platform_v1_blocking_command(content)
    assert cmd is not None
    deselected = _extract_deselected_nodes(cmd)
    assert deselected == set(_EXACT_DESELECTED_NODE_IDS), (
        f"Platform V1 blocking gate deselected set must exactly match the 4 "
        f"reclassified node IDs; got {sorted(deselected)}"
    )


def test_ci_platform_v1_blocking_gate_exactly_four_deselects() -> None:
    content = _read_ci()
    cmd = _extract_platform_v1_blocking_command(content)
    assert cmd is not None
    deselected = _extract_deselected_nodes(cmd)
    assert len(deselected) == 4, (
        f"Platform V1 blocking gate must contain exactly 4 --deselect node IDs, "
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


def test_frontend_playwright_workflow_contract() -> None:
    content = FRONTEND_PLAYWRIGHT_PATH.read_text(encoding="utf-8")
    for required in (
        "runs-on: ubuntu-24.04",
        'node-version: "22.23.1"',
        "run: npm ci",
        "npx playwright install --with-deps --no-shell chromium",
        "run: npm run e2e",
        "if: failure()",
        "contents: read",
    ):
        assert required in content, f"frontend Playwright workflow missing: {required}"
    assert "--update-snapshots" not in content
    assert "workflow_dispatch" not in content
    for provider_url in (
        "api.openai.com",
        "api.anthropic.com",
        "generativelanguage.googleapis.com",
        "openrouter.ai",
    ):
        assert provider_url not in content


# The single exact-product-head resolver shared by every history-sensitive
# workflow.  For pull_request events the checked-out ref is the PR product
# head (github.event.pull_request.head.sha), never the synthetic merge ref
# (refs/pull/<n>/merge); for push/main events it falls back to github.sha.
EXACT_PRODUCT_HEAD_REF = "${{ github.event.pull_request.head.sha || github.sha }}"


def _extract_checkout_ref(content: str) -> str | None:
    """Return the ``ref:`` value of the first actions/checkout step."""
    marker = "uses: actions/checkout@v4"
    idx = content.find(marker)
    if idx == -1:
        return None
    block = content[idx:]
    # The checkout step is: uses + with: (indented). Find the ref: line.
    match = re.search(r"^\s*ref:\s*(.*)$", block, re.MULTILINE)
    return match.group(1).strip() if match else None


def _checkout_has_persist_credentials_false(content: str) -> bool:
    marker = "uses: actions/checkout@v4"
    idx = content.find(marker)
    if idx == -1:
        return False
    block = content[idx:]
    next_step = block.find("uses: actions/setup-python@v5")
    if next_step == -1:
        next_step = len(block)
    checkout_block = block[:next_step]
    return "persist-credentials: false" in checkout_block


@pytest.mark.parametrize(
    "workflow_path",
    [CI_PATH],
    ids=["ci"],
)
def test_history_sensitive_workflow_checkout_uses_exact_product_head(
    workflow_path: Path,
) -> None:
    """F regression 1: every history-sensitive workflow checks out the exact PR
    product head for pull_request events.

    Git history-sensitive validation (decision chronology, immutability,
    expected-head protection) must run on the PR product head
    ``github.event.pull_request.head.sha``, never on GitHub's synthetic merge
    ref ``refs/pull/<n>/merge``.
    """
    content = workflow_path.read_text(encoding="utf-8")
    ref = _extract_checkout_ref(content)
    assert ref is not None, f"{workflow_path.name} must have an actions/checkout step"
    assert ref == EXACT_PRODUCT_HEAD_REF, (
        f"{workflow_path.name} checkout must use the exact-product-head resolver "
        f"{EXACT_PRODUCT_HEAD_REF}; got {ref!r}"
    )


@pytest.mark.parametrize(
    "workflow_path",
    [CI_PATH],
    ids=["ci"],
)
def test_history_sensitive_workflow_checkout_falls_back_to_github_sha(
    workflow_path: Path,
) -> None:
    """F regression 2: on push/main events (no pull_request object) the same
    resolver falls back to ``github.sha``. No second head resolver is created.
    """
    content = workflow_path.read_text(encoding="utf-8")
    ref = _extract_checkout_ref(content)
    assert ref is not None
    assert "github.sha" in ref
    assert "pull_request.head.sha" in ref


@pytest.mark.parametrize(
    "workflow_path",
    [CI_PATH],
    ids=["ci"],
)
def test_history_sensitive_workflow_never_uses_synthetic_merge_ref(
    workflow_path: Path,
) -> None:
    """F regression 3: the synthetic merge ref ``refs/pull/<n>/merge`` must not
    be used as the product HEAD for decision chronology.
    """
    content = workflow_path.read_text(encoding="utf-8")
    ref = _extract_checkout_ref(content)
    assert ref is not None
    assert "refs/pull" not in ref
    assert "/merge" not in ref
    assert "merge_commit_sha" not in ref


@pytest.mark.parametrize(
    "workflow_path",
    [CI_PATH],
    ids=["ci"],
)
def test_history_sensitive_workflow_checkout_disables_persisted_credentials(
    workflow_path: Path,
) -> None:
    """F regression 4: checkout must not persist credentials (read-only work)."""
    content = workflow_path.read_text(encoding="utf-8")
    assert _checkout_has_persist_credentials_false(content), (
        f"{workflow_path.name} checkout must set persist-credentials: false"
    )


FRONTEND_VISUAL_BASELINES_PATH = WORKFLOWS_DIR / "frontend-visual-baselines.yml"


def _workflow_job_block(content: str, job: str) -> str:
    match = re.search(rf"^  {job}:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)", content, re.MULTILINE | re.DOTALL)
    assert match, f"job {job} missing"
    return match.group(1)


def test_frontend_visual_baselines_workflow_only_stages_outside_pr_branch() -> None:
    content = FRONTEND_VISUAL_BASELINES_PATH.read_text(encoding="utf-8")
    assert re.search(r"^permissions:\n  contents: read$", content, re.MULTILINE)
    assert "[update-visual-baselines]" in content
    assert "head.repo.full_name == github.repository" in content
    assert "pull_request_target" not in content

    regenerate = _workflow_job_block(content, "regenerate")
    assert "contents: write" not in regenerate
    assert "persist-credentials: false" in regenerate
    assert "--update-snapshots=changed" in regenerate
    assert "run: npm run e2e:visual\n" in regenerate, "regenerated baselines must be re-checked"

    stage = _workflow_job_block(content, "stage")
    assert "contents: write" in stage
    for forbidden in ("npm ", "npx ", "playwright"):
        assert forbidden not in stage, f"write-capable job must not run PR code: {forbidden}"
    pushes = re.findall(r"git push[^\n]*", content.split("\njobs:\n", 1)[1])
    assert pushes == ['git push origin "HEAD:refs/heads/$staging"'], "staging refs are never force-pushed"
    assert 'staging="ci-visual-baselines/$HEAD_SHA"' in stage
    assert 'git ls-remote origin "refs/heads/$staging"' in stage
    assert "! -name '*.png'" in stage

    # The check itself stays untouched: it never updates snapshots on its own.
    check = FRONTEND_PLAYWRIGHT_PATH.read_text(encoding="utf-8")
    assert "--update-snapshots" not in check
    assert "contents: write" not in check
