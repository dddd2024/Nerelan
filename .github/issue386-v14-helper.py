from pathlib import Path
import subprocess

BASE = "0da78df5d2c5337ffeab17e3a00651df507637f0"
BRANCH = "owner/issue386-executor-router-collision-r1-v14-helper"
WORKFLOW = ".github/workflows/issue386-v14-helper.yml"
HELPER = ".github/issue386-v14-helper.py"

PRODUCT_PATHS = {
    "reverse_agent/platform_v1/task_runtime.py",
    "tests/platform_v1/test_task_runtime.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_unattended_coordinator.py",
}

FOCUSED_TESTS = 'def test_registration_rejects_duplicate_normalized_kind_and_preserves_factory() -> None:\n    router = ExecutorRouter()\n    first_factory = lambda: object()\n    router.register(" Custom ", first_factory)\n    with pytest.raises(ExecutorRuntimeError, match=r"^duplicate_executor_kind:custom$"):\n        router.register("CUSTOM", lambda: object())\n    assert router._registry["custom"] is first_factory\n\n\ndef test_registration_cannot_shadow_builtin_executor_aliases() -> None:\n    router = ExecutorRouter()\n    fixture_factory = router._registry["deterministic_fixture"]\n    opencode_factory = router._registry["opencode"]\n    with pytest.raises(ExecutorRuntimeError, match=r"^duplicate_executor_kind:deterministic_fixture$"):\n        router.register(" DETERMINISTIC_FIXTURE ", lambda: object())\n    with pytest.raises(ExecutorRuntimeError, match=r"^duplicate_executor_kind:opencode$"):\n        router.register(" OpenCode ", lambda: object())\n    assert router._registry["deterministic_fixture"] is fixture_factory\n    assert router._registry["opencode"] is opencode_factory\n\n\ndef test_explicit_replace_normalizes_existing_kind() -> None:\n    router = ExecutorRouter()\n    replacement = lambda: object()\n    router.replace(" DETERMINISTIC_FIXTURE ", replacement)\n    assert router._registry["deterministic_fixture"] is replacement\n\n\ndef test_explicit_replace_rejects_unknown_kind() -> None:\n    router = ExecutorRouter()\n    with pytest.raises(ExecutorRuntimeError, match=r"^unknown_executor_kind:missing$"):\n        router.replace(" Missing ", lambda: object())\n\n\ndef test_normalized_dispatch_lookup_preserves_builtin_fixture() -> None:\n    with tempfile.TemporaryDirectory() as td:\n        router = ExecutorRouter()\n        result = router.dispatch_execute(\n            task_id="task-normalized-fixture",\n            store=TaskStore(":memory:"),\n            executor_kind=" DETERMINISTIC_FIXTURE ",\n            workspace_root=td,\n        )\n    assert result.success is True\n\n\ndef test_normalized_create_executor_lookup_preserves_opencode() -> None:\n    from reverse_agent.platform_v1.opencode_executor import OpenCodeExecutor\n    router = ExecutorRouter()\n    executor = router.create_executor(\n        executor_kind=" OpenCode ",\n        model_id="sensetime/sensenova-6.7-flash-lite",\n        opencode_exe="/fake/opencode",\n    )\n    assert isinstance(executor, OpenCodeExecutor)\n\n\ndef test_registration_and_replace_reject_empty_kind() -> None:\n    router = ExecutorRouter()\n    with pytest.raises(ExecutorRuntimeError, match=r"^executor_kind_must_be_non_empty$"):\n        router.register("   ", lambda: object())\n    with pytest.raises(ExecutorRuntimeError, match=r"^executor_kind_must_be_non_empty$"):\n        router.replace("   ", lambda: object())'


def run(*args: str) -> None:
    subprocess.run(list(args), check=True)


def output(*args: str) -> str:
    return subprocess.check_output(list(args), text=True)


def newline_for(data: bytes) -> bytes:
    return b"\r\n" if b"\r\n" in data else b"\n"


def encode_template(text: str, newline: bytes) -> bytes:
    return text.replace("\n", newline.decode("ascii")).encode("utf-8")


def replace_exact_bytes(path: str, old: str, new: str, expected: int) -> None:
    p = Path(path)
    data = p.read_bytes()
    nl = newline_for(data)
    old_b = encode_template(old, nl)
    new_b = encode_template(new, nl)
    actual = data.count(old_b)
    if actual != expected:
        raise SystemExit(f"{path}: expected {expected} matches, found {actual}")
    p.write_bytes(data.replace(old_b, new_b))


runtime_path = "reverse_agent/platform_v1/task_runtime.py"
marker_old = (
    "# ---------------------------------------------------------------------------\n"
    "# ExecutorRouter\n"
    "# ---------------------------------------------------------------------------\n\n"
    "class ExecutorRouter:"
)
marker_new = (
    "# ---------------------------------------------------------------------------\n"
    "# ExecutorRouter\n"
    "# ---------------------------------------------------------------------------\n\n"
    "def _normalize_executor_kind(kind: str) -> str:\n"
    "    if not isinstance(kind, str) or not kind.strip():\n"
    '        raise ExecutorRuntimeError("executor_kind_must_be_non_empty")\n'
    "    return kind.strip().casefold()\n\n\n"
    "class ExecutorRouter:"
)
replace_exact_bytes(runtime_path, marker_old, marker_new, 1)

register_old = (
    "    def register(self, kind: str, factory: Callable[..., Executor]) -> None:\n"
    "        if not isinstance(kind, str) or not kind.strip():\n"
    '            raise ExecutorRuntimeError("executor_kind_must_be_non_empty")\n'
    "        self._registry[kind] = factory\n"
)
register_new = (
    "    def register(self, kind: str, factory: Callable[..., Executor]) -> None:\n"
    "        normalized_kind = _normalize_executor_kind(kind)\n"
    "        if normalized_kind in self._registry:\n"
    '            raise ExecutorRuntimeError(f"duplicate_executor_kind:{normalized_kind}")\n'
    "        self._registry[normalized_kind] = factory\n\n"
    "    def replace(self, kind: str, factory: Callable[..., Executor]) -> None:\n"
    "        normalized_kind = _normalize_executor_kind(kind)\n"
    "        if normalized_kind not in self._registry:\n"
    '            raise ExecutorRuntimeError(f"unknown_executor_kind:{normalized_kind}")\n'
    "        self._registry[normalized_kind] = factory\n"
)
replace_exact_bytes(runtime_path, register_old, register_new, 1)

lookup_old = (
    "        factory = self._registry.get(executor_kind)\n"
    "        if factory is None:\n"
    '            raise ExecutorRuntimeError(f"unknown_executor_kind:{executor_kind}")'
)
lookup_new = (
    "        normalized_kind = _normalize_executor_kind(executor_kind)\n"
    "        factory = self._registry.get(normalized_kind)\n"
    "        if factory is None:\n"
    '            raise ExecutorRuntimeError(f"unknown_executor_kind:{normalized_kind}")'
)
replace_exact_bytes(runtime_path, lookup_old, lookup_new, 2)

test_path = Path("tests/platform_v1/test_task_runtime.py")
test_data = test_path.read_bytes()
test_nl = newline_for(test_data)
sentinel = b"def test_registration_rejects_duplicate_normalized_kind_and_preserves_factory()"
if sentinel in test_data:
    raise SystemExit("focused tests already patched unexpectedly")

focused_b = encode_template(FOCUSED_TESTS, test_nl)
if focused_b.endswith(b"\n") or focused_b.endswith(b"\r"):
    raise SystemExit("focused test payload unexpectedly ends with newline")
if test_data.endswith(test_nl):
    patched_tests = test_data + test_nl + focused_b + test_nl
else:
    patched_tests = test_data + test_nl + test_nl + focused_b + test_nl
if not patched_tests.endswith(test_nl):
    raise SystemExit("patched tests missing EOF newline")
if patched_tests.endswith(test_nl + test_nl):
    raise SystemExit("patched tests contain blank line at EOF")
test_path.write_bytes(patched_tests)

caller_counts = {
    "tests/platform_v1/test_durable_execution.py": 3,
    "tests/platform_v1/test_task_service.py": 4,
    "tests/platform_v1/test_unattended_coordinator.py": 1,
}
old_call = 'router.register("deterministic_fixture",'
new_call = 'router.replace("deterministic_fixture",'
for path, expected in caller_counts.items():
    replace_exact_bytes(path, old_call, new_call, expected)

changed = set(output("git", "diff", "--name-only", BASE, "--").splitlines())
expected_pre_delete = PRODUCT_PATHS | {WORKFLOW, HELPER}
if changed != expected_pre_delete:
    raise SystemExit(f"unexpected changed paths after patch: {sorted(changed)}")

run("python", "-m", "pytest", "tests/platform_v1/test_task_runtime.py", "-q")
run(
    "python", "-m", "pytest",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_unattended_coordinator.py",
    "-q",
)
run("git", "diff", "--check")

run("git", "rm", WORKFLOW, HELPER)
changed = set(output("git", "diff", "--name-only", BASE, "--").splitlines())
if changed != PRODUCT_PATHS:
    raise SystemExit(f"net candidate paths mismatch: {sorted(changed)}")

run("git", "config", "user.name", "github-actions[bot]")
run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
run("git", "add", "-A")
run("git", "commit", "-m", "chore: prepare Issue 386 V14 product tree")

if output("git", "status", "--porcelain").strip():
    raise SystemExit("candidate working tree is not clean")
changed = set(output("git", "diff", "--name-only", BASE, "HEAD").splitlines())
if changed != PRODUCT_PATHS:
    raise SystemExit(f"candidate commit paths mismatch: {sorted(changed)}")
if output("git", "diff", "--name-only", BASE, "HEAD", "--", ".github").strip():
    raise SystemExit("temporary helper files remain in candidate tree")

run(
    "python", "-m", "pytest", "tests/platform_v1", "-q",
    "--deselect=tests/platform_v1/test_task3c_v6_production_relay.py::TestCombinedTrustedHostInstalledOpenCodeE2E::test_real_task_api_opencode_relay_fake_provider_end_to_end",
    "--deselect=tests/platform_v1/test_task3c_v4_repairs.py::TestInstalledOpenCodeFakeProviderSmoke::test_installed_opencode_fake_provider_end_to_end",
    "--deselect=tests/platform_v1/test_task3c_v5_opencode_probe.py::TestDirectFakeProviderControl::test_opencode_direct_fake_provider",
    "--deselect=tests/platform_v1/test_task3c_v5_opencode_probe.py::TestRelayFakeProviderRun::test_opencode_relay_fake_provider",
)

run("git", "push", "origin", f"HEAD:{BRANCH}")
