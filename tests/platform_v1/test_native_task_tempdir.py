"""Provider-free native executions with real Git and Python child processes."""
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1.codex_executor import CodexExecutor, _task_temp_env, _release_owned_task_temp
from reverse_agent.platform_v1.claude_executor import ClaudeCodeExecutor
from reverse_agent.platform_v1.opencode_executor import RoleContext, _collect_product_diff
from reverse_agent.platform_v1.task_runtime import ExecutorRuntimeError


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True,
                          text=True, check=True).stdout.strip()


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init")
    git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "--allow-empty", "-m", "fixture")
    return root, git(root, "rev-parse", "HEAD")


@pytest.mark.parametrize("kind", [CodexExecutor, ClaudeCodeExecutor])
@pytest.mark.parametrize("edit", [False, True])
def test_real_child_scoped_temp_and_product_detection(repository, tmp_path, kind, edit):
    repo, base = repository
    parent = {"PATH": str(Path(sys.executable).parent), "TEMP": "inaccessible-parent",
              "tMp": "also-inaccessible", "OPENAI_API_KEY": "fixture-key",
              "ANTHROPIC_API_KEY": "fixture-key", "ANTHROPIC_AUTH_TOKEN": "untrusted"}
    original = dict(parent)
    host_temp = {k: os.environ.get(k) for k in ("TEMP", "TMP", "TMPDIR")}
    claude = kind is ClaudeCodeExecutor
    events = ([{"type": "system", "subtype": "init", "session_id": "fixture"},
               {"type": "result", "subtype": "success", "is_error": False, "result": "done"}]
              if claude else [{"type": "thread.started", "thread_id": "fixture"},
                              {"type": "turn.started"},
                              {"type": "item.completed", "item": {"type": "agent_message", "text": "done"}},
                              {"type": "turn.completed"}])
    script = "\n".join([
        "import os, sys, tempfile",
        "from pathlib import Path",
        "sys.stdin.read()",
        "root = Path.cwd() / '.nt'",
        "assert Path(tempfile.gettempdir()) == root",
        "assert os.environ['TEMP'] == os.environ['TMP'] == str(root)",
        "assert 'OPENAI_API_KEY' not in os.environ and 'ANTHROPIC_API_KEY' not in os.environ",
        ("assert os.environ['ANTHROPIC_AUTH_TOKEN'] == 'fixture-lease'" if claude
         else "assert 'ANTHROPIC_AUTH_TOKEN' not in os.environ"),
        ("assert os.environ['ANTHROPIC_BASE_URL'] == 'http://127.0.0.1:1234'" if claude else "pass"),
        "with tempfile.NamedTemporaryFile(delete=False) as f: f.write(b'scoped write')",
        "assert Path(f.name).read_bytes() == b'scoped write'",
        "Path('product.txt').write_text('implementation')" if edit else "pass",
        "print(" + repr("\n".join(json.dumps(e) for e in events)) + ")",
    ])
    launched = []
    def factory(argv, **kwargs):
        proc = subprocess.Popen([sys.executable, "-u", "-c", script], **kwargs)
        launched.append(proc)
        return proc
    executor = kind(model_id="fixture", repo_dir=str(repo), base_ref=base,
                    process_factory=factory, parent_env=parent, timeout=10,
                    readiness_probe=lambda _: "managed_login_ready",
                    **({"claude_exe": sys.executable} if claude else {"codex_exe": sys.executable}))
    prepared = executor.prepare_worktree_once("native-temp", tmp_path / "workspaces")
    # Preparation/readiness/metadata reconstruction never creates execution scratch.
    executor.reconstruct_prepared_context(worktree_path=prepared.worktree, base_sha=base,
                                         execution_id=prepared.execution_id)
    assert not (prepared.worktree / ".nt").exists()
    if claude:
        # Synthetic relay override, exercising the actual subclass environment hook.
        executor._relay_env = {"ANTHROPIC_AUTH_TOKEN": "fixture-lease",
                               "ANTHROPIC_BASE_URL": "http://127.0.0.1:1234"}
    store = SimpleNamespace(get_task=lambda _: SimpleNamespace(title="Implement fixture"))
    result = executor.execute_role_prepared(prepared, store,
        role_context=RoleContext("executor", "native-temp", prepared.worktree))
    assert len(launched) == 1 and launched[0].poll() == 0
    assert result.process_exit_code == 0
    assert result.success == edit
    assert [f["path"] for f in result.changed_files] == (["product.txt"] if edit else [])
    assert [f["path"] for f in _collect_product_diff(prepared.worktree)] == (["product.txt"] if edit else [])
    if not edit:
        assert result.failure_classification == executor._e("no_product_changes")
    assert parent == original
    assert {k: os.environ.get(k) for k in host_temp} == host_temp
    assert not (prepared.worktree / ".nt").exists()
    # A completed child must release only its owned scratch: another native
    # attempt in this identical workspace should not be blocked by stale .nt.
    result_again = executor.execute_role_prepared(prepared, store,
        role_context=RoleContext("executor", "native-temp", prepared.worktree))
    assert len(launched) == 2
    assert result_again.success == edit
    assert result_again.process_exit_code == 0
    assert not (prepared.worktree / ".nt").exists()



def test_failed_native_launch_releases_owned_scratch_for_new_attempt(repository, tmp_path):
    repo, base = repository
    calls = []
    def fail_start(argv, **kwargs):
        calls.append(True)
        raise OSError("fixture spawn failure")
    executor = CodexExecutor(model_id="fixture", repo_dir=str(repo), base_ref=base,
                             codex_exe=sys.executable, readiness_probe=lambda _: "managed_login_ready",
                             process_factory=fail_start, timeout=10)
    prepared = executor.prepare_worktree_once("failed-launch", tmp_path / "workspaces")
    task = SimpleNamespace(get_task=lambda _: SimpleNamespace(title="fixture"))
    role = RoleContext("executor", "failed-launch", prepared.worktree)
    outcome = executor.execute_role_prepared(prepared, task, role_context=role)
    assert not outcome.success
    assert outcome.failure_classification == "codex_process_start_failed"
    assert calls == [True]
    assert not (prepared.worktree / ".nt").exists()

    events = [
        {"type": "thread.started", "thread_id": "fixture"},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "done"}},
        {"type": "turn.completed"},
    ]
    script = ("import sys; from pathlib import Path; sys.stdin.read(); "
              "Path('product.txt').write_text('success'); print(" +
              repr("\n".join(json.dumps(e) for e in events)) + ")")
    executor._process_factory = lambda argv, **kwargs: subprocess.Popen(
        [sys.executable, "-c", script], **kwargs)
    second = executor.execute_role_prepared(prepared, task, role_context=role)
    assert second.success
    assert [row["path"] for row in second.changed_files] == ["product.txt"]
    assert not (prepared.worktree / ".nt").exists()


def test_plain_directory_for_read_only_planner_gets_scoped_temp(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    child = _task_temp_env(plain, {"PATH": "test", "TEMP": "untrusted"})
    assert child["TEMP"] == child["TMP"] == str(plain / ".nt")
    if os.name != "nt":
        assert child["TMPDIR"] == str(plain / ".nt")
    assert (plain / ".nt" / ".gitignore").read_text() == "*\n"


def test_broken_git_marker_never_downgrades_index_failure(tmp_path):
    repo = tmp_path / "broken-repo"
    repo.mkdir()
    (repo / ".git").write_text("gitdir: /missing/git/worktree\\n")
    with pytest.raises(ExecutorRuntimeError, match="native_task_temp_unavailable"):
        _task_temp_env(repo, {})
    assert not (repo / ".nt").exists()


def test_owned_scratch_cleanup_refuses_child_created_symlink(repository, tmp_path):
    root, _ = repository
    scratch = Path(_task_temp_env(root, {})["TEMP"])
    outside = tmp_path / "outside-data"
    outside.mkdir()
    (outside / "sensitive").write_text("preserve")
    try:
        (scratch / "unsafe-link").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink privilege unavailable")
    with pytest.raises(ExecutorRuntimeError, match="native_task_temp_cleanup_failed"):
        _release_owned_task_temp(root)
    assert (outside / "sensitive").read_text() == "preserve"
    assert scratch.is_dir()


@pytest.mark.parametrize("entry", ["directory", "file", "tracked", "symlink", "junction"])
def test_preexisting_scratch_refused(repository, tmp_path, entry):
    root, _ = repository
    scratch = root / ".nt"
    outside = tmp_path / "outside"
    outside.mkdir()
    if entry == "directory":
        scratch.mkdir()
    elif entry in {"file", "tracked"}:
        scratch.write_text("preserve")
        if entry == "tracked":
            git(root, "add", ".nt")
            scratch.unlink()  # A tracked deletion must not become runtime scratch.
    elif entry == "symlink":
        try:
            scratch.symlink_to(outside, target_is_directory=True)
        except OSError:
            pytest.skip("symlink privilege unavailable")
    else:
        if os.name != "nt":
            pytest.skip("Windows junction")
        subprocess.run(["cmd", "/c", "mklink", "/J", str(scratch), str(outside)],
                       capture_output=True, check=True)
    with pytest.raises(ExecutorRuntimeError, match="native_task_temp_unavailable"):
        _task_temp_env(root, {})
    assert list(outside.iterdir()) == []
    if entry == "file":
        assert scratch.read_text() == "preserve"


def test_unverifiable_metadata_and_create_error_refused(repository, monkeypatch):
    root, _ = repository
    original = Path.lstat
    def denied(path, *args, **kwargs):
        if path == root:
            raise PermissionError("fixture")
        return original(path, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", denied)
        with pytest.raises(ExecutorRuntimeError, match="native_task_temp_unavailable"):
            _task_temp_env(root, {})
    assert not (root / ".nt").exists()
    def no_create(*args, **kwargs):
        raise PermissionError("fixture")
    monkeypatch.setattr(Path, "mkdir", no_create)
    with pytest.raises(ExecutorRuntimeError, match="native_task_temp_unavailable"):
        _task_temp_env(root, {})
