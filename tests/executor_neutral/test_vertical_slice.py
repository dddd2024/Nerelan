from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess

import pytest

from reverse_agent.executor_neutral import (
    ExecutionEvidence,
    REQUIRED_CHECK_TIMEOUT_SECONDS,
    TaskContract,
    accept_execution,
    canonical_json,
    collect_execution_evidence,
    export_task_bundle,
    observe_capability,
    sha256_digest,
)
import reverse_agent.executor_neutral.core as core


def _run(repo: Path, *command: str) -> str:
    result = subprocess.run(
        command,
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _repo(tmp_path: Path, name: str = "subject") -> tuple[Path, str]:
    repo = tmp_path / name
    repo.mkdir()
    _run(repo, "git", "init", "-q")
    _run(repo, "git", "config", "user.name", "Executor Neutral Test")
    _run(repo, "git", "config", "user.email", "executor-neutral@example.invalid")
    files = {
        ".gitignore": "__pycache__/\n.pytest_cache/\nignored/\n",
        "calc.py": "def add(left, right):\n    return left - right\n",
        "delete_me.txt": "delete me\n",
        "old_name.txt": "rename me\n",
        "src/existing.py": "VALUE = 1\n",
    }
    for relative, content in files.items():
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _run(repo, "git", "add", "--", ".")
    _run(repo, "git", "commit", "-qm", "base")
    return repo, _run(repo, "git", "rev-parse", "HEAD")


def _contract(base: str, **overrides: object) -> TaskContract:
    payload: dict[str, object] = {
        "schema_version": "1",
        "task_id": "task-add",
        "objective": "Correct the bounded subject.",
        "repository_identity": "temporary/test-subject",
        "base_commit": base,
        "allowed_paths": [
            "calc.py",
            "delete_me.txt",
            "old_name.txt",
            "new_name.txt",
            "new.py",
            "src/**",
        ],
        "required_checks": ['python -c "print(\'ok\')"'],
        "executor_hint": "manual-codex",
    }
    payload.update(overrides)
    return TaskContract.from_mapping(payload)


def _collect(repo: Path, contract: TaskContract):
    return collect_execution_evidence(
        contract,
        repo,
        executor="codex",
        agent_completion_claim=True,
        started_at="2026-07-27T10:00:00+00:00",
        completed_at="2026-07-27T10:00:02+00:00",
    )


def _accepted_fixture(tmp_path: Path):
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    (repo / "calc.py").write_text(
        "def add(left, right):\n    return left + right\n",
        encoding="utf-8",
    )
    evidence = _collect(repo, contract)
    return repo, contract, evidence, accept_execution(contract, evidence)


def _tree_paths(repo: Path, tree: str) -> set[str]:
    output = _run(repo, "git", "ls-tree", "-r", "--name-only", tree)
    return set(output.splitlines())


def test_canonical_serialization_and_digest_are_stable() -> None:
    first = {"z": [2, 1], "a": {"b": True}}
    second = {"a": {"b": True}, "z": [2, 1]}
    assert canonical_json(first) == canonical_json(second)
    assert sha256_digest(first) == sha256_digest(second)


def test_missing_required_contract_field_fails_closed() -> None:
    with pytest.raises(ValueError, match="objective"):
        TaskContract.from_mapping(
            {
                "schema_version": "1",
                "task_id": "task",
                "repository_identity": "tmp/repo",
                "base_commit": "0" * 40,
                "allowed_paths": ["x.py"],
                "required_checks": ["python -V"],
                "executor_hint": "codex",
            }
        )


def test_task_bundle_documents_identity_and_timeout(tmp_path: Path) -> None:
    contract = _contract("a" * 40)
    json_path, markdown_path = export_task_bundle(contract, tmp_path / "bundle")
    assert json.loads(json_path.read_text(encoding="utf-8")) == contract.to_dict()
    markdown = markdown_path.read_text(encoding="utf-8")
    assert contract.digest in markdown
    assert "routing identity (descriptive)" in markdown
    assert "authoritative content identity" in markdown
    assert f"{REQUIRED_CHECK_TIMEOUT_SECONDS}-second timeout" in markdown


@pytest.mark.parametrize("staged", [True, False])
def test_staged_and_unstaged_modifications_enter_observed_tree(
    tmp_path: Path, staged: bool
) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    content = f"VALUE = {'2' if staged else '3'}\n"
    (repo / "src/existing.py").write_text(content, encoding="utf-8")
    if staged:
        _run(repo, "git", "add", "src/existing.py")
    evidence = _collect(repo, contract)
    assert "src/existing.py" in evidence.changed_paths
    assert _run(repo, "git", "show", f"{evidence.observed_tree}:src/existing.py") == content.strip()


def test_tracked_deletion_enters_observed_tree(tmp_path: Path) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    (repo / "delete_me.txt").unlink()
    evidence = _collect(repo, contract)
    assert "delete_me.txt" in evidence.changed_paths
    assert "delete_me.txt" not in _tree_paths(repo, evidence.observed_tree)


def test_nonignored_untracked_enters_observed_tree(tmp_path: Path) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    (repo / "new.py").write_text("VALUE = 2\n", encoding="utf-8")
    evidence = _collect(repo, contract)
    assert "new.py" in evidence.changed_paths
    assert "new.py" in _tree_paths(repo, evidence.observed_tree)


def test_ignored_file_does_not_enter_observed_tree(tmp_path: Path) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    ignored = repo / "ignored" / "cache.bin"
    ignored.parent.mkdir()
    ignored.write_bytes(b"ignored")
    evidence = _collect(repo, contract)
    assert "ignored/cache.bin" not in evidence.changed_paths
    assert "ignored/cache.bin" not in _tree_paths(repo, evidence.observed_tree)
    assert evidence.base_tree == evidence.observed_tree


def test_rename_records_old_and_new_paths(tmp_path: Path) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    (repo / "old_name.txt").rename(repo / "new_name.txt")
    evidence = _collect(repo, contract)
    assert {"old_name.txt", "new_name.txt"}.issubset(evidence.changed_paths)


def test_different_uncommitted_content_changes_tree_and_evidence_digest(tmp_path: Path) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    (repo / "calc.py").write_text("VALUE = 1\n", encoding="utf-8")
    first = _collect(repo, contract)
    (repo / "calc.py").write_text("VALUE = 2\n", encoding="utf-8")
    second = _collect(repo, contract)
    assert first.observed_tree != second.observed_tree
    assert first.digest != second.digest


def test_real_index_path_and_bytes_are_unchanged(tmp_path: Path) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    (repo / "calc.py").write_text("VALUE = 7\n", encoding="utf-8")
    _run(repo, "git", "add", "calc.py")
    raw_index = _run(repo, "git", "rev-parse", "--git-path", "index")
    index_path = (Path(raw_index) if Path(raw_index).is_absolute() else repo / raw_index).resolve()
    before = index_path.read_bytes()
    _collect(repo, contract)
    after_path_raw = _run(repo, "git", "rev-parse", "--git-path", "index")
    after_path = (
        Path(after_path_raw)
        if Path(after_path_raw).is_absolute()
        else repo / after_path_raw
    ).resolve()
    assert after_path == index_path
    assert after_path.read_bytes() == before


def test_allowed_untracked_whitespace_error_is_rejected(tmp_path: Path) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base)
    (repo / "new.py").write_text("VALUE = 1 \n", encoding="utf-8")
    evidence = _collect(repo, contract)
    result = accept_execution(contract, evidence)
    assert evidence.git_diff_check["exit_code"] != 0
    assert result.accepted is False
    assert "git_diff_check_failed" in result.blocking_reasons


def test_matching_contract_and_valid_trees_accept(tmp_path: Path) -> None:
    repo, contract, evidence, result = _accepted_fixture(tmp_path)
    assert repo.is_relative_to(tmp_path)
    assert evidence.contract_digest == contract.digest
    assert evidence.base_tree != evidence.observed_tree
    assert result.accepted is True
    assert result.contract_digest == contract.digest
    assert result.base_tree == evidence.base_tree
    assert result.observed_tree == evidence.observed_tree
    observation = observe_capability(contract, evidence, result)
    assert observation.success is True
    assert observation.elapsed_time == 2.0


def test_contract_digest_mismatch_rejects_agent_claim(tmp_path: Path) -> None:
    _, contract, evidence, _ = _accepted_fixture(tmp_path)
    tampered = replace(evidence, contract_digest="0" * 64)
    result = accept_execution(contract, tampered)
    assert tampered.agent_completion_claim is True
    assert result.accepted is False
    assert "contract_digest_mismatch" in result.blocking_reasons


def test_objective_and_allowed_paths_change_contract_digest() -> None:
    base = "a" * 40
    original = _contract(base)
    changed_objective = _contract(base, objective="Different objective.")
    changed_scope = _contract(base, allowed_paths=["calc.py"])
    assert original.digest != changed_objective.digest
    assert original.digest != changed_scope.digest


def test_exact_path_matches_only_exact_file() -> None:
    contract = _contract("a" * 40, allowed_paths=["src/app.py"])
    assert core._path_allowed("src/app.py", contract.allowed_paths)
    assert not core._path_allowed("src/nested/app.py", contract.allowed_paths)


def test_recursive_prefix_matches_direct_and_nested_descendants_only() -> None:
    contract = _contract("a" * 40, allowed_paths=["src/**"])
    assert core._path_allowed("src/a.py", contract.allowed_paths)
    assert core._path_allowed("src/nested/a.py", contract.allowed_paths)
    assert not core._path_allowed("src2/a.py", contract.allowed_paths)


def test_windows_separators_normalize_stably() -> None:
    contract = _contract("a" * 40, allowed_paths=[r"src\**", r"tools\run.py"])
    assert contract.allowed_paths == ("src/**", "tools/run.py")
    assert contract.digest == TaskContract.from_mapping(contract.to_dict()).digest


@pytest.mark.parametrize(
    "pattern",
    [
        "src/*.py",
        "src/**/a.py",
        "src/?",
        "src/[abc].py",
        "/absolute.py",
        r"C:\absolute.py",
        ".",
        "..",
        "src/../a.py",
        "src//a.py",
        "src/",
        "",
    ],
)
def test_invalid_allowed_path_grammar_rejects(pattern: str) -> None:
    with pytest.raises(ValueError):
        _contract("a" * 40, allowed_paths=[pattern])


def test_required_check_timeout_produces_failed_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _repo(tmp_path)
    contract = _contract(base, required_checks=["slow trusted check"])
    real_run = core._run

    def timeout_check(command, **kwargs):
        if kwargs.get("shell"):
            raise subprocess.TimeoutExpired(
                command,
                kwargs["timeout"],
                output="partial stdout",
                stderr="partial stderr",
            )
        return real_run(command, **kwargs)

    monkeypatch.setattr(core, "_run", timeout_check)
    evidence = _collect(repo, contract)
    check = evidence.required_check_results[0]
    assert check == {
        "command": "slow trusted check",
        "exit_code": None,
        "stdout": "partial stdout",
        "stderr": "partial stderr",
        "timed_out": True,
        "timeout_seconds": REQUIRED_CHECK_TIMEOUT_SECONDS,
    }
    result = accept_execution(contract, evidence)
    assert evidence.agent_completion_claim is True
    assert result.accepted is False
    assert "required_check_timeout:slow trusted check" in result.blocking_reasons


def test_agent_claim_cannot_override_scope_digest_or_diff_failure(tmp_path: Path) -> None:
    _, contract, evidence, _ = _accepted_fixture(tmp_path)
    variants = (
        replace(evidence, changed_paths=("forbidden.txt",)),
        replace(evidence, contract_digest="f" * 64),
        replace(
            evidence,
            git_diff_check={
                **evidence.git_diff_check,
                "exit_code": 1,
                "stderr": "whitespace error",
            },
        ),
    )
    for variant in variants:
        assert variant.agent_completion_claim is True
        assert accept_execution(contract, variant).accepted is False


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("base_commit", "", "base_commit_malformed"),
        ("base_tree", "", "base_tree_malformed"),
        ("observed_tree", "not-a-tree", "observed_tree_malformed"),
        ("contract_digest", "not-a-digest", "contract_digest_malformed"),
    ],
)
def test_malformed_binding_fields_fail_closed(
    tmp_path: Path, field: str, value: str, reason: str
) -> None:
    _, contract, evidence, _ = _accepted_fixture(tmp_path)
    result = accept_execution(contract, replace(evidence, **{field: value}))
    assert result.accepted is False
    assert reason in result.blocking_reasons


def test_missing_evidence_field_cannot_be_constructed(tmp_path: Path) -> None:
    _, _, evidence, _ = _accepted_fixture(tmp_path)
    payload = evidence.to_dict()
    payload.pop("observed_tree")
    with pytest.raises(TypeError):
        ExecutionEvidence(**payload)


def test_only_exact_required_checks_execute(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _repo(tmp_path)
    checks = ['python -c "print(11)"', 'python -c "print(22)"']
    contract = _contract(base, required_checks=checks)
    actual_run = subprocess.run
    shell_commands: list[str] = []

    def recording_run(command, **kwargs):
        if kwargs.get("shell"):
            shell_commands.append(command)
        return actual_run(command, **kwargs)

    monkeypatch.setattr(core.subprocess, "run", recording_run)
    evidence = _collect(repo, contract)
    assert shell_commands == checks
    assert [item["command"] for item in evidence.required_check_results] == checks


def test_all_subject_repositories_are_temporary_fixtures(tmp_path: Path) -> None:
    first, _ = _repo(tmp_path, "first")
    second, _ = _repo(tmp_path, "second")
    assert first.is_relative_to(tmp_path)
    assert second.is_relative_to(tmp_path)


@pytest.mark.parametrize("path,rule", [
    ("src/new.py", ""), ("tests/test_new.py", ""),
    ("../escape.py", "path_escape"), ("a/../../escape", "path_escape"),
    ("C:/outside.py", "path_escape"), (r"C:\outside.py", "path_escape"),
    (r"\\server\share\file", "path_escape"), ("/etc/file", "path_escape"),
    (r"a\..\escape", "path_escape"), ("a/node_modules/pkg/a.py", "package_payload"),
    ("~/Python/Python313/site-packages/pkg/a.py", "package_payload"),
    ("reverse_agent.egg-info/PKG-INFO", "package_payload"),
    ("~/AppData/Local/Nerelan/platform-v1/tasks.sqlite3", "runtime_artifact"),
    ("~/AppData/Local/Nerelan/platform-v1/tasks.sqlite3-wal", "runtime_artifact"),
    ("project/.platform_v1_runtime/tasks.sqlite3-shm", "runtime_artifact"),
    ("project/data.sqlite3", ""),
])
def test_portable_artifact_rules(path, rule):
    assert core.artifact_path_rule(path) == rule


def _make_pe(size=0x1000, lfanew=0x80):
    import struct
    pe = bytearray(max(size, lfanew + 4))
    pe[0:2] = b"MZ"
    struct.pack_into("<I", pe, 0x3C, lfanew)
    pe[lfanew:lfanew + 4] = b"PE\x00\x00"
    return bytes(pe)


@pytest.mark.parametrize("payload", [
    _make_pe(size=0x800, lfanew=0x80),
    b"\x7fELFfake",
    b"\xcf\xfa\xed\xfefake",
])
def test_snapshot_rejects_native_headers_without_arbitrary_binary_ban(tmp_path, payload):
    repo, base = _repo(tmp_path)
    (repo / "native").write_bytes(payload)
    (repo / "asset.bin").write_bytes(b"image\x00data")
    (repo / "new_test.py").write_text("def test_new(): pass\n", encoding="utf-8")
    _, tree, changed, hygiene = core._snapshot_workspace(repo, base)
    assert hygiene["exit_code"] != 0
    assert hygiene["artifact_violations"] == [{"path": "native", "rule": "native_executable"}]
    safe = core.safe_recovery_tree(repo, base, tree)
    paths = _run(repo, "git", "ls-tree", "-r", "--name-only", safe).splitlines()
    assert "native" not in paths and "asset.bin" in paths and "new_test.py" in paths
    assert (repo / "native").read_bytes() == payload


def test_pe_signature_at_0x2000_is_rejected_not_just_0x80(tmp_path):
    import struct
    repo, base = _repo(tmp_path)
    pe = bytearray(0x2004)
    pe[0:2] = b"MZ"
    struct.pack_into("<I", pe, 0x3C, 0x2000)
    pe[0x2000:0x2004] = b"PE\x00\x00"
    (repo / "extensionless_pe").write_bytes(bytes(pe))
    _, tree, _, hygiene = core._snapshot_workspace(repo, base)
    assert hygiene["exit_code"] != 0
    assert hygiene["artifact_violations"] == [{"path": "extensionless_pe", "rule": "native_executable"}]


def test_pe_smaller_than_0x40_is_accepted_header_only(tmp_path):
    repo, base = _repo(tmp_path)
    (repo / "tiny_mz").write_bytes(b"MZxx")
    _, tree, _, hygiene = core._snapshot_workspace(repo, base)
    assert hygiene["exit_code"] == 0


def test_long_mz_python_source_is_not_native_executable(tmp_path):
    repo, base = _repo(tmp_path)
    (repo / "ordinary.py").write_bytes(b"MZ = 1\n" + b"# ordinary source comment\n" * 5)
    _, tree, changed, hygiene = core._snapshot_workspace(repo, base)
    assert hygiene["exit_code"] == 0
    assert "ordinary.py" in changed


def test_runtime_sqlite_path_is_rejected_before_staging(tmp_path):
    repo, base = _repo(tmp_path)
    runtime = repo / "~" / "AppData" / "Local" / "Nerelan" / "platform-v1"
    runtime.mkdir(parents=True)
    payload = b"controlled fixture not a database"
    (runtime / "tasks.sqlite3").write_bytes(payload)
    oid = subprocess.check_output(["git", "hash-object", "--stdin"], cwd=repo, input=payload).decode().strip()
    assert subprocess.run(["git", "cat-file", "-e", oid], cwd=repo, capture_output=True).returncode != 0
    with pytest.raises(core.SnapshotIndirectionError) as excinfo:
        core._snapshot_workspace(repo, base)
    assert any(v["rule"] == "runtime_artifact" for v in excinfo.value.violations)
    assert subprocess.run(["git", "cat-file", "-e", oid], cwd=repo, capture_output=True).returncode != 0


def test_walk_permissionerror_on_subdirectory_fails_closed(tmp_path, monkeypatch):
    repo, base = _repo(tmp_path)
    folder = repo / "unverifiable"
    folder.mkdir()
    payload = b"controlled sentinel"
    (folder / "sentinel.txt").write_bytes(payload)
    oid = subprocess.check_output(["git", "hash-object", "--stdin"], cwd=repo, input=payload).decode().strip()
    assert subprocess.run(["git", "cat-file", "-e", oid], cwd=repo, capture_output=True).returncode != 0
    original_scandir = os.scandir

    def denied(path):
        if Path(path) == folder:
            raise PermissionError("controlled traversal error")
        return original_scandir(path)

    monkeypatch.setattr(os, "scandir", denied)
    with pytest.raises(core.SnapshotIndirectionError):
        core._snapshot_workspace(repo, base)
    assert subprocess.run(["git", "cat-file", "-e", oid], cwd=repo, capture_output=True).returncode != 0


def test_git_object_symlink_rejected_without_following_target(tmp_path):
    repo, base = _repo(tmp_path)
    oid = subprocess.check_output(["git", "hash-object", "-w", "--stdin"], cwd=repo,
                                  input=b"../../outside-secret").decode().strip()
    _run(repo, "git", "update-index", "--add", "--cacheinfo", "120000", oid, "link")
    tree = _run(repo, "git", "write-tree")
    assert core.artifact_tree_diagnostics(repo, base, tree) == [{"path": "link", "rule": "symlink"}]
    safe = core.safe_recovery_tree(repo, base, tree)
    assert "link" not in _run(repo, "git", "ls-tree", "-r", "--name-only", safe).splitlines()


def test_windows_junction_staging_is_prevented_by_prescan(tmp_path):
    repo, base = _repo(tmp_path)
    outside = tmp_path / "outside_sentinel"
    outside.mkdir()
    (outside / "payload.txt").write_text("OUTSIDE SECRET\n", encoding="utf-8")
    junction = repo / "outlink"
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
                       capture_output=True, check=True)
    else:
        junction.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError) as excinfo:
        core._snapshot_workspace(repo, base)
    assert "snapshot_indirection_detected" in str(excinfo.value)
    if junction.exists() and junction.is_dir() and not junction.is_symlink():
        junction.rmdir()
    elif junction.is_symlink():
        junction.unlink()


def test_permissionerror_on_reparse_detection_fails_closed_not_swallowed(tmp_path, monkeypatch):
    repo, base = _repo(tmp_path)

    def _fake_lstat(self):
        raise PermissionError("access denied")

    monkeypatch.setattr(Path, "lstat", _fake_lstat)
    with pytest.raises(ValueError) as excinfo:
        core._snapshot_workspace(repo, base)
    assert "snapshot_indirection_detected" in str(excinfo.value)
    assert "access_error" in str(excinfo.value)


def test_ignored_pycache_and_source_snapshot_only_source(tmp_path):
    repo, base = _repo(tmp_path)
    cache = repo / "__pycache__"
    cache.mkdir()
    (cache / "cache.pyc").write_bytes(b"controlled ignored cache")
    (repo / "ordinary.py").write_bytes(b"MZ = 1\n")
    _, tree, changed, hygiene = core._snapshot_workspace(repo, base)
    assert hygiene["exit_code"] == 0
    assert changed == ("ordinary.py",)


def test_installation_tree_paths_rejected_by_path_rule(tmp_path):
    repo, base = _repo(tmp_path)
    site_pkg = repo / "~" / "Python" / "Python313" / "site-packages" / "pkg"
    site_pkg.mkdir(parents=True)
    (site_pkg / "payload.py").write_text("installed = True\n", encoding="utf-8")
    _, tree, _, hygiene = core._snapshot_workspace(repo, base)
    assert hygiene["exit_code"] != 0
    assert hygiene["artifact_violations"] == [{"path": "~/Python/Python313/site-packages/pkg/payload.py", "rule": "package_payload"}]
    safe = core.safe_recovery_tree(repo, base, tree)
    paths = _run(repo, "git", "ls-tree", "-r", "--name-only", safe).splitlines()
    assert not any("site-packages" in p for p in paths)
    assert (site_pkg / "payload.py").read_text(encoding="utf-8") == "installed = True\n"
