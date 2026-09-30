"""Actual Git/subprocess regressions; full CI uses the real existing validators.

No model/provider, network, candidate-code execution, skipped tests or production
validator substitutes. Synthetic Git commits isolate trusted/candidate versions.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "tools/protected_governance.py"
SPEC = importlib.util.spec_from_file_location("protected_governance_under_test", ENTRY)
assert SPEC and SPEC.loader
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)
GIT = str(Path(shutil.which("git") or "/usr/bin/git").resolve())


def _git(repo: Path, *args: str, data: bytes | None = None) -> str:
    env = {"PATH": "/usr/bin:/bin", "HOME": str(repo), "LANG": "C.UTF-8",
           "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    result = subprocess.run([GIT, *args], cwd=repo, env=env, input=data,
                            capture_output=True, check=True, timeout=10)
    return result.stdout.decode().strip()


def _write(repo: Path, name: str, data: str | bytes) -> None:
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data.encode() if isinstance(data, str) else data)


def _decision(**changes: object) -> str:
    meta = {"decision_id": "test_decision", "round_id": "test_round",
            "status": "APPROVED", "mainline": "engineering_branch",
            "skill_profiles": ["reverse-agent-iteration@v2"]}
    command = {"command_id": "test.read", "command": "read only fixture",
               "phase": "validation", "required": True, "expected_exit_codes": [0],
               "execution_surface": "trusted_worker", "operations": ["code_read"],
               "network_access": False,
               "required_evidence_source": "repository_state_attestation"}
    command.update(changes)
    contract = {"transition_kernel_required": True, "required_branch": "owner/test",
                "bootstrap_exception_files": ["project_state/decision_packet.md"],
                "bootstrap_exception_commands": [], "allowed_commands": [command]}
    return ("```json decision_meta\n" + json.dumps(meta) + "\n```\n\n"
            "```json decision_contract\n" + json.dumps(contract) + "\n```\n")


@pytest.fixture
def repository(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "trusted-object-store"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Fixture")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "core.autocrlf", "false")
    for path in (adapter.ENTRY, *adapter.SOURCES):
        _write(repo, path, (ROOT / path).read_bytes())
    _write(repo, adapter.DECISION, _decision())
    _git(repo, "add", "--all")
    _git(repo, "commit", "-m", "trusted source fixture")
    return repo, _git(repo, "rev-parse", "HEAD")


def _commit(repo: Path) -> str:
    _git(repo, "add", "--all")
    _git(repo, "commit", "--allow-empty", "-m", "candidate data")
    return _git(repo, "rev-parse", "HEAD")


def _call(repository: tuple[Path, str], *, candidate: str | None = None,
          flags: tuple[str, ...] = ("-I", "-S", "-B"),
          environment: dict[str, str] | None = None,
          cwd: Path | None = None, entry: Path = ENTRY,
          git: str = GIT) -> tuple[int, dict]:
    repo, trusted = repository
    env = dict(os.environ)
    if environment:
        env.update(environment)
    result = subprocess.run(
        [sys.executable, *flags, str(entry), "--repository-dir", str(repo),
         "--git-executable", git, f"--trusted-ref={trusted}",
         f"--candidate-ref={candidate or trusted}"], cwd=cwd or repo,
        env=env, capture_output=True, timeout=40,
    )
    assert result.stderr == b"", result.stderr
    value = json.loads(result.stdout)
    assert value["claim_scope"] == "SHADOW_ONLY"
    for key in adapter.DENIED:
        assert value[key] is False, key
    return result.returncode, value


def test_real_existing_plan_validation_passes_without_authority(repository) -> None:
    code, value = _call(repository)
    assert code == 0, value
    assert value["status"] == "VALID"
    assert value["trusted_ref"] == repository[1]
    assert value["candidate_ref"] == repository[1]
    assert value["worker"]["command_count"] == 1
    assert set(value["worker"]["loaded_sources"]) == set(adapter.SOURCES)
    assert set(value["source_closure"]) == {adapter.ENTRY, *adapter.SOURCES}
    for relative, record in value["source_closure"].items():
        assert record["sha256"] == hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


@pytest.mark.parametrize("change", [
    {"operations": ["nonexistent_operation"]},
    {"operations": ["merge"], "execution_surface": "trusted_worker"},
    {"execution_surface": "local"},
    {"command_id": ""},
    {"operations": []},
])
def test_candidate_cannot_replace_its_own_judge(repository, change) -> None:
    repo, trusted = repository
    marker = repo.parent / "candidate-executed"
    payload = f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n"
    for path in ("reverse_agent/__init__.py", "reverse_agent/control_plane/__init__.py",
                 "sitecustomize.py", "usercustomize.py", "setup.py", "json.py",
                 "subprocess.py", ".github/actions/evil/main.py"):
        _write(repo, path, payload)
    _write(repo, "reverse_agent/control_plane/command_authority.py",
           payload + "def validate_command_plan(plan):\n    return ()\n")
    _write(repo, adapter.DECISION, _decision(**change))
    candidate = _commit(repo)
    code, value = _call((repo, trusted), candidate=candidate, cwd=repo,
                       environment={"PYTHONPATH": str(repo), "PYTHONHOME": str(repo)})
    assert code == 1 and value["status"] == "INVALID", value
    assert not marker.exists()
    assert value["candidate_ref"] == candidate
    assert value["trusted_ref"] == trusted


def test_valid_candidate_with_poisoned_packages_still_uses_trusted_sources(repository) -> None:
    repo, trusted = repository
    marker = repo.parent / "imported"
    payload = f"from pathlib import Path\nPath({str(marker)!r}).write_text('bad')\n"
    for path in ("reverse_agent/__init__.py", "reverse_agent/control_plane/legacy_adapter.py",
                 "sitecustomize.py", "setup.py", "tools/protected_governance.py"):
        _write(repo, path, payload)
    candidate = _commit(repo)
    code, value = _call((repo, trusted), candidate=candidate,
                       environment={"PYTHONPATH": str(repo)})
    assert code == 0, value
    assert not marker.exists()


def test_submitted_command_is_data_not_a_shell_invocation(repository) -> None:
    repo, trusted = repository
    marker = repo.parent / "command-ran"
    _write(repo, adapter.DECISION,
           _decision(command=f"touch {marker}; echo unsafe", operations=["code_read"]))
    candidate = _commit(repo)
    code, value = _call((repo, trusted), candidate=candidate)
    # This tool reuses plan lint, not Work Item shell validation. Even a
    # syntactically valid plan's command text must NEVER be executed here.
    assert code == 0, value
    assert not marker.exists()


def test_dirty_worktree_modules_and_bytecode_do_not_replace_committed_source(repository) -> None:
    repo, trusted = repository
    marker = repo.parent / "dirty-import"
    payload = f"from pathlib import Path\nPath({str(marker)!r}).write_text('bad')\n"
    _write(repo, "reverse_agent/control_plane/command_authority.py", payload)
    _write(repo, "reverse_agent/control_plane/command_authority.pyc", b"poisoned bytecode")
    code, value = _call((repo, trusted))
    assert code == 0, value
    assert not marker.exists()
    assert (repo / "reverse_agent/control_plane/command_authority.py").read_text() == payload


def test_parent_python_and_git_overrides_and_credentials_are_not_inherited(repository) -> None:
    repo, trusted = repository
    environment = {
        "GITHUB_TOKEN": "dummy-secret", "GH_TOKEN": "dummy-secret",
        "OPENAI_API_KEY": "dummy-secret", "PYTHONPATH": str(repo),
        "PYTHONHOME": str(repo), "GIT_DIR": "/does/not/exist",
        "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.fsmonitor",
        "GIT_CONFIG_VALUE_0": "evil", "GIT_OBJECT_DIRECTORY": "/wrong",
    }
    code, value = _call((repo, trusted), environment=environment)
    assert code == 0, value
    assert not set(environment).intersection(value["worker"]["environment_keys"])
    assert "dummy-secret" not in json.dumps(value)


@pytest.mark.parametrize("flags", [(), ("-I",), ("-S", "-B"), ("-I", "-S")])
def test_unsafe_startup_fails_before_project_import(repository, flags) -> None:
    code, value = _call(repository, flags=flags)
    assert code == 2 and value["status"] == "ERROR"


@pytest.mark.parametrize("reference", ["main", "HEAD", "a" * 39, "A" * 40,
                                      "-help", "a" * 40 + ":file", "0" * 40])
def test_mutable_malformed_or_missing_reference_fails(repository, reference) -> None:
    code, value = _call((repository[0], reference))
    assert code == 2 and value["status"] == "ERROR"


def test_candidate_ref_must_also_be_an_actual_commit(repository) -> None:
    repo, trusted = repository
    tree = _git(repo, "rev-parse", trusted + "^{tree}")
    code, value = _call(repository, candidate=tree)
    assert code == 2 and value["status"] == "ERROR"


@pytest.mark.parametrize("path,mode", [
    ("reverse_agent/control_plane/legacy_adapter.py", "120000"),
    ("reverse_agent/control_plane", "160000"),
    ("project_state/decision_packet.md", "120000"),
])
def test_nonregular_source_or_candidate_data_is_rejected(repository, path, mode) -> None:
    repo, trusted = repository
    if mode == "160000":
        # Real index gitlink, no platform symlink privilege needed.
        _git(repo, "rm", "-r", "--cached", path)
        oid = trusted
    else:
        oid = _git(repo, "hash-object", "-w", "--stdin", data=b"elsewhere")
    _git(repo, "update-index", "--add", "--cacheinfo", mode, oid, path)
    _git(repo, "commit", "-m", "nonregular Git mode")
    changed = _git(repo, "rev-parse", "HEAD")
    refs = (repo, trusted) if path == adapter.DECISION else (repo, changed)
    code, value = _call(refs, candidate=changed)
    assert code == 2 and value["status"] == "ERROR"


@pytest.mark.parametrize("path", ["reverse_agent/control_plane/models.py",
                                  "project_state/decision_packet.md"])
def test_missing_object_fails_without_fallback(repository, path) -> None:
    repo, trusted = repository
    _git(repo, "rm", path)
    _git(repo, "commit", "-m", "missing required input")
    changed = _git(repo, "rev-parse", "HEAD")
    refs = (repo, trusted) if path == adapter.DECISION else (repo, changed)
    code, value = _call(refs, candidate=changed)
    assert code == 2 and value["status"] == "ERROR"


@pytest.mark.parametrize("data", [b"\xff", b"not a Decision", b"x" * (adapter.MAX_DECISION + 1),
                                 (_decision() + _decision()).encode()])
def test_malformed_ambiguous_or_oversize_candidate_data_fails(repository, data) -> None:
    repo, trusted = repository
    _write(repo, adapter.DECISION, data)
    candidate = _commit(repo)
    code, value = _call((repo, trusted), candidate=candidate)
    assert code == 2 and value["status"] == "ERROR"


def test_launcher_must_match_trusted_object(repository, tmp_path) -> None:
    modified = tmp_path / "modified_launcher.py"
    modified.write_bytes(ENTRY.read_bytes() + b"\n# dirty launcher\n")
    code, value = _call(repository, entry=modified)
    assert code == 2 and value["status"] == "ERROR"


@pytest.mark.parametrize("git", ["git", "/nonexistent/git"])
def test_git_executable_must_be_explicit_and_absolute(repository, git) -> None:
    code, value = _call(repository, git=git)
    assert code == 2 and value["status"] == "ERROR"


def test_fixed_deadline_and_output_bound_use_real_subprocess(tmp_path) -> None:
    environment = adapter._environment(tmp_path)
    with pytest.raises(adapter.BoundaryError, match="execution_timeout"):
        adapter._process([sys.executable, "-I", "-S", "-c", "import time; time.sleep(3)"],
                         cwd=tmp_path, env=environment, deadline=time.monotonic() + 0.1, limit=100)
    with pytest.raises(adapter.BoundaryError, match="execution_output_too_large"):
        adapter._process([sys.executable, "-I", "-S", "-c", "print('x'*1001)"],
                         cwd=tmp_path, env=environment, deadline=time.monotonic() + 3, limit=100)


def test_workflow_never_checks_out_candidate_or_installs_candidate_dependencies() -> None:
    source = (ROOT / ".github/workflows/protected-governance.yml").read_text()
    assert "pull_request_target:" in source
    assert "ref: ${{ github.workflow_sha }}" in source
    assert "uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in source
    assert source.count("uses:") == 1
    assert "persist-credentials: false" in source
    assert "contents: read" in source
    assert "-I -S -B" in source
    assert "--no-recurse-submodules" in source
    assert "--no-write-fetch-head" in source
    for forbidden in ("contents: write", "pull-requests: write", "secrets.",
                      "pip install", "npm install", "actions/cache", "workflow_dispatch:",
                      "ref: ${{ github.event.pull_request.head.sha }}"):
        assert forbidden not in source
