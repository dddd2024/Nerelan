"""OpenCode executor unit tests.

All tests use a fake/injected CLI subprocess. No live OpenCode invocation occurs.
"""

import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

import pytest

from reverse_agent.platform_v1.opencode_executor import (
    OpenCodeExecutor,
    build_opencode_argv,
    build_prompt,
    redact_event,
    redact_secrets,
    resolve_opencode_cli,
    validate_model_id,
)
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import (
    ExecutorRuntimeError,
    ExecutorRouter,
    ExecutorResult,
)


def _make_git_repo(path: Path) -> None:
    """Initialize a minimal git repo with one committed file."""
    subprocess.run(["git", "init", "-q"], cwd=str(path), check=True)
    subprocess.run(["git", "config", "user.email", "test@reverse-agent.local"], cwd=str(path), check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(path), check=True)
    (path / "pyproject.toml").write_text("[project]\nname = \"test\"\n", encoding="utf-8")
    subprocess.run(["git", "add", "pyproject.toml"], cwd=str(path), check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=str(path), check=True)


def _fake_opencode_run(
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=[],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def _make_fake_opencode_run(
    orig_run: Callable[..., subprocess.CompletedProcess],
    *,
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
    timeout_after: int | None = None,
    diff_check_fail: bool = False,
    opencode_path: str = "/fake/opencode",
) -> Callable[..., subprocess.CompletedProcess]:
    call_count = {"n": 0}
    def fake_run(argv, **kwargs):
        if not argv or argv[0] != opencode_path:
            return orig_run(argv, **kwargs)
        call_count["n"] += 1
        if timeout_after is not None and call_count["n"] > timeout_after:
            raise subprocess.TimeoutExpired(cmd=argv, timeout=1)
        return _fake_opencode_run(stdout=stdout, stderr=stderr, returncode=returncode)
    fake_run._call_count = call_count  # type: ignore[attr-defined]
    return fake_run


# ---------------------------------------------------------------------------
# CLI resolution
# ---------------------------------------------------------------------------

def test_resolve_opencode_cli_injected_path() -> None:
    cli, is_cmd = resolve_opencode_cli("/usr/bin/opencode")
    assert cli == "/usr/bin/opencode"
    assert is_cmd is False


def test_resolve_opencode_cli_cmd_path() -> None:
    cli, is_cmd = resolve_opencode_cli("C:\\tools\\opencode.cmd")
    assert cli == "C:\\tools\\opencode.cmd"
    assert is_cmd is True


def test_resolve_opencode_cli_not_found_raises() -> None:
    import reverse_agent.platform_v1.opencode_executor as exec_mod
    original_where = subprocess.run

    def fake_where(argv, **kwargs):
        return subprocess.CompletedProcess(args=argv, returncode=1, stdout="", stderr="")

    subprocess.run = fake_where
    try:
        with pytest.raises(ExecutorRuntimeError, match="opencode_cli_not_found"):
            resolve_opencode_cli(None)
    finally:
        subprocess.run = original_where


# ---------------------------------------------------------------------------
# Command construction
# ---------------------------------------------------------------------------

def test_build_opencode_argv_native() -> None:
    argv, prompt = build_opencode_argv(
        "/usr/bin/opencode",
        is_cmd=False,
        model_id="sensetime/sensenova-6.7-flash-lite",
        worktree="/tmp/ws",
        prompt_file="/tmp/prompt.txt",
    )
    assert argv == [
        "/usr/bin/opencode",
        "run",
        "--model",
        "sensetime/sensenova-6.7-flash-lite",
        "--dir",
        "/tmp/ws",
        "--format",
        "json",
        "--file",
        "/tmp/prompt.txt",
        "--",
        "execute bounded task from attached prompt file",
    ]


def test_build_opencode_argv_cmd_path_passed_directly() -> None:
    argv, prompt = build_opencode_argv(
        "C:\\tools\\opencode.cmd",
        is_cmd=True,
        model_id="sensetime/sensenova-6.7-flash-lite",
        worktree="C:\\ws",
        prompt_file="C:\\prompt.txt",
    )
    assert argv[0] == "C:\\tools\\opencode.cmd"
    assert "run" in argv
    assert "--model" in argv
    assert "sensetime/sensenova-6.7-flash-lite" in argv
    assert "--file" in argv
    assert "C:\\prompt.txt" in argv


def test_build_opencode_argv_auto_flag() -> None:
    argv, _ = build_opencode_argv(
        "/usr/bin/opencode",
        is_cmd=False,
        model_id="m",
        worktree="/ws",
        prompt_file="/tmp/p.txt",
        use_auto=True,
    )
    assert "--auto" in argv

    argv_no_auto, _ = build_opencode_argv(
        "/usr/bin/opencode",
        is_cmd=False,
        model_id="m",
        worktree="/ws",
        prompt_file="/tmp/p.txt",
        use_auto=False,
    )
    assert "--auto" not in argv_no_auto


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

def test_build_prompt_contains_authority_envelope() -> None:
    prompt = build_prompt("create alpha-ok file", "/tmp/ws")
    assert "AUTHORITY CONSTRAINTS" in prompt
    assert "END AUTHORITY CONSTRAINTS" in prompt
    assert "USER TASK" in prompt
    assert "END USER TASK" in prompt
    assert "create alpha-ok file" in prompt
    assert "/tmp/ws" in prompt
    assert "commit" in prompt
    assert "credentials" in prompt


# ---------------------------------------------------------------------------
# Model identifier validation
# ---------------------------------------------------------------------------

def test_validate_model_id_accepts_required_model() -> None:
    assert validate_model_id("sensetime/sensenova-6.7-flash-lite") == "sensetime/sensenova-6.7-flash-lite"


@pytest.mark.parametrize("bad", [
    "",
    "  ",
    "a",
    "/model",
    "provider/",
    "provider/model\nextra",
    "provider\x00/model",
    "provider model",
    "provider; drop table x --/model",
    "&&|><",
])
def test_validate_model_id_rejects_malformed(bad) -> None:
    with pytest.raises(ExecutorRuntimeError):
        validate_model_id(bad)


def test_validate_model_id_rejects_too_long() -> None:
    with pytest.raises(ExecutorRuntimeError):
        validate_model_id("a" * 200 + "/" + "b" * 200)


# ---------------------------------------------------------------------------
# Secret redaction
# ---------------------------------------------------------------------------

def test_redact_secrets_auth_header() -> None:
    text = "Authorization: Bearer ghp_abcdefghijklmnopqrstuvwxyz123456"
    result = redact_secrets(text)
    assert "ghp_" not in result
    assert "abcdefghijklmnopqrstuvwxyz" not in result


def test_redact_secrets_api_key() -> None:
    text = 'config: { "api_key": "sk-1234567890abcdef" }'
    result = redact_secrets(text)
    assert "sk-1234567890abcdef" not in result


def test_redact_secrets_token() -> None:
    text = "token = abcdefghijklmnop"
    result = redact_secrets(text)
    assert "abcdefghijklmnop" not in result


def test_redact_secrets_no_false_positives() -> None:
    text = "The author wrote a nice token for the API"
    result = redact_secrets(text)
    assert result == text


def test_redact_event_replaces_sensitive_keys() -> None:
    event = {"token": "secret123", "message": "hello"}
    result = redact_event(event)
    assert result["token"] == "[REDACTED]"
    assert result["message"] == "hello"


def test_redact_event_long_string_truncated_and_redacted() -> None:
    event = {"output": "x" * 300 + " api_key=realkey12345678 " + "y" * 300}
    result = redact_event(event)
    assert "realkey12345678" not in result["output"]
    assert len(result["output"]) <= 512 + len("...[TRUNCATED]")


# ---------------------------------------------------------------------------
# Fake subprocess runner for executor tests
# ---------------------------------------------------------------------------

def _run_with_fake_executor(
    fake_stdout: str = "",
    fake_stderr: str = "",
    fake_returncode: int = 0,
    fake_timeout: bool = False,
    model_id: str = "sensetime/sensenova-6.7-flash-lite",
    timeout: int = 30,
) -> tuple[OpenCodeExecutor, ExecutorResult]:
    """Run OpenCodeExecutor with a fake CLI that simulates subprocess behavior."""
    with tempfile.TemporaryDirectory() as td:
        store = TaskStore(":memory:")
        store.create_task(
            title="fake opencode task",
            executor_kind="opencode",
            model_profile_ref=model_id,
        )
        tasks = store.list_tasks()
        task_id = tasks[0].id

        class _FakeExecutor(OpenCodeExecutor):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self._received_argv: list[str] | None = None
                self._received_cwd: str | None = None

            def _run_fake(
                self,
                argv: list[str],
                cwd: str,
            ) -> subprocess.CompletedProcess:
                self._received_argv = argv
                self._received_cwd = cwd
                if self._fake_timeout:
                    raise subprocess.TimeoutExpired(cmd=argv, timeout=self._timeout)
                return subprocess.CompletedProcess(
                    args=argv,
                    returncode=self._fake_returncode,
                    stdout=self._fake_stdout,
                    stderr=self._fake_stderr,
                )

            def execute(self, task_id, store, *, workspace_root="", event_callback=None):
                from pathlib import Path
                import shutil

                root_path = Path(workspace_root)
                root_path.mkdir(parents=True, exist_ok=True)
                worktree = root_path / task_id
                if worktree.exists():
                    shutil.rmtree(worktree)
                worktree.mkdir(parents=True, exist_ok=True)

                execution_id = "exec-%s" % task_id
                if event_callback:
                    event_callback(task_id, {
                        "type": "WORKSPACE_READY",
                        "title": "Workspace ready",
                        "description": "OpenCode worktree created at %s" % worktree,
                        "metadata": {
                            "workspace": str(worktree),
                            "execution_id": execution_id,
                        },
                    })

                cli_path = "/fake/opencode"
                is_cmd = False
                git_ready = self._prepare_git_worktree(worktree)
                task_title = self._task_title(store, task_id)
                prompt = build_prompt(task_title, str(worktree))

                cli_argv, _ = build_opencode_argv(
                    cli_path,
                    is_cmd=is_cmd,
                    model_id=self._model_id,
                    worktree=str(worktree),
                    prompt=prompt,
                    use_auto=self._use_auto,
                )

                if event_callback:
                    event_callback(task_id, {
                        "type": "EXECUTOR_RUNNING",
                        "title": "OpenCode CLI started",
                        "description": "OpenCode child process launched",
                        "metadata": {
                            "execution_id": execution_id,
                            "executor_kind": "opencode",
                            "model": self._model_id,
                            "cli_path": cli_path,
                        },
                    })

                proc = self._run_fake(cli_argv, str(worktree))
                exit_code = proc.returncode
                stdout = proc.stdout or ""
                stderr = proc.stderr or ""

                events_raw, json_error = self._parse_json_lines(stdout)

                if exit_code != 0:
                    fail_class = self._classify_exit(exit_code, events_raw)
                    from reverse_agent.platform_v1.opencode_executor import (
                        _sanitize_output as _so,
                    )
                    stderr_redacted = redact_secrets(_so(stderr, 2048))
                    changed_files = self._collect_changed_files(worktree)
                    return ExecutorResult(
                        success=False,
                        validation_exit_code=-1,
                        validation_command_id="",
                        validation_output_digest="",
                        validation_output_summary=stderr_redacted[:1024],
                        changed_files=changed_files,
                        error="opencode_nonzero:exit=%d:%s" % (exit_code, fail_class),
                        workspace=str(worktree),
                        execution_id=execution_id,
                        process_exit_code=exit_code,
                        failure_classification=fail_class,
                    )

                changed_files = self._collect_changed_files(worktree)
                if event_callback:
                    event_callback(task_id, {
                        "type": "EXECUTOR_FINISHED",
                        "title": "OpenCode CLI finished",
                        "description": "exit=0 changed_files=%d" % len(changed_files),
                        "metadata": {"execution_id": execution_id, "exit_code": exit_code},
                    })

                from reverse_agent.platform_v1.task_runtime import LocalValidationRunner
                runner = LocalValidationRunner()
                val_exit, val_output, val_digest = runner.run(
                    task_id=task_id,
                    command_id="git_diff_check",
                    cwd=str(worktree),
                )
                if val_exit == 0:
                    return ExecutorResult(
                        success=True,
                        validation_exit_code=val_exit,
                        validation_command_id="git_diff_check",
                        validation_output_digest=val_digest,
                        validation_output_summary="",
                        changed_files=changed_files,
                        workspace=str(worktree),
                        execution_id=execution_id,
                        process_exit_code=exit_code,
                    )

                return ExecutorResult(
                    success=False,
                    validation_exit_code=val_exit,
                    validation_command_id="git_diff_check",
                    validation_output_digest=val_digest,
                    validation_output_summary="",
                    changed_files=changed_files,
                    workspace=str(worktree),
                    execution_id=execution_id,
                    process_exit_code=exit_code,
                    failure_classification="deterministic_validation_failure",
                )

        fake = _FakeExecutor(model_id=model_id, opencode_exe="/fake/opencode", timeout=timeout)
        fake._fake_stdout = fake_stdout
        fake._fake_stderr = fake_stderr
        fake._fake_returncode = fake_returncode
        fake._fake_timeout = fake_timeout
        fake._received_argv = None
        fake._received_cwd = None

        result = fake.execute(
            task_id,
            store,
            workspace_root=td,
        )
        return fake, result


def _collect_changed_files(worktree: Path):
    try:
        proc = subprocess.run(
            ["git", "diff", "--numstat", "HEAD"],
            cwd=str(worktree),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    files = []
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added, deleted, path = parts[0], parts[1], parts[2]
        files.append({
            "path": path,
            "status": "added" if added != "-" and deleted == "0" else "modified",
            "additions": 0 if added == "-" else int(added),
            "deletions": 0 if deleted == "-" else int(deleted),
            "diff_digest": "",
        })
    return files


# ---------------------------------------------------------------------------
# Executor success path
# ---------------------------------------------------------------------------

def test_executor_success_with_json_events() -> None:
    stdout_lines = [
        json.dumps({"type": "tool_call", "action": "write_file", "path": "alpha-ok.txt"}),
        json.dumps({"type": "tool_call", "action": "shell", "command": "ls"}),
    ]
    stdout = "\n".join(stdout_lines) + "\n"

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        _make_git_repo(repo)

        workspace_root = Path(td) / "ws"
        workspace_root.mkdir()

        store = TaskStore(":memory:")
        store.create_task(title="test", executor_kind="opencode", model_profile_ref="m")
        tasks = store.list_tasks()
        task_id = tasks[0].id

        executor = OpenCodeExecutor(
            model_id="sensetime/sensenova-6.7-flash-lite",
            repo_dir=str(repo),
            opencode_exe="/fake/opencode",
        )

        import reverse_agent.platform_v1.opencode_executor as exec_mod
        original_run = subprocess.run
        exec_mod.subprocess.run = _make_fake_opencode_run(
            original_run,
            stdout=stdout,
            returncode=0,
        )
        try:
            result = executor.execute(task_id, store, workspace_root=str(workspace_root))
            assert result.success is True
            assert result.validation_exit_code == 0
            assert result.validation_command_id == "git_diff_check"
            assert result.execution_id
            assert result.executor_evidence
            assert any(e["category"] == "ExecutorAction" for e in result.executor_evidence)
        finally:
            exec_mod.subprocess.run = original_run


def test_executor_requires_model_id() -> None:
    with pytest.raises(ExecutorRuntimeError, match="model_id_required"):
        OpenCodeExecutor(model_id="")


def test_executor_requires_workspace_root() -> None:
    exec_ = OpenCodeExecutor(model_id="sensetime/sensenova-6.7-flash-lite", opencode_exe="/fake/opencode")
    with pytest.raises(ExecutorRuntimeError, match="workspace_root_required"):
        exec_.execute("t", TaskStore(":memory:"))


# ---------------------------------------------------------------------------
# Failure paths
# ---------------------------------------------------------------------------

def test_executor_nonzero_exit_classification() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        _make_git_repo(repo)

        workspace_root = Path(td) / "ws"
        workspace_root.mkdir()

        store = TaskStore(":memory:")
        store.create_task(title="test", executor_kind="opencode", model_profile_ref="m")
        tasks = store.list_tasks()
        task_id = tasks[0].id

        executor = OpenCodeExecutor(
            model_id="sensetime/sensenova-6.7-flash-lite",
            repo_dir=str(repo),
            opencode_exe="/fake/opencode",
        )

        import reverse_agent.platform_v1.opencode_executor as exec_mod
        original_run = subprocess.run
        exec_mod.subprocess.run = _make_fake_opencode_run(
            original_run,
            stderr="auth failure",
            returncode=42,
        )
        try:
            result = executor.execute(task_id, store, workspace_root=str(workspace_root))
            assert result.success is False
            assert result.failure_classification == "executor_nonzero"
            assert result.process_exit_code == 42
        finally:
            exec_mod.subprocess.run = original_run


def test_executor_timeout() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        _make_git_repo(repo)

        workspace_root = Path(td) / "ws"
        workspace_root.mkdir()

        store = TaskStore(":memory:")
        store.create_task(title="test", executor_kind="opencode", model_profile_ref="m")
        tasks = store.list_tasks()
        task_id = tasks[0].id

        executor = OpenCodeExecutor(
            model_id="sensetime/sensenova-6.7-flash-lite",
            repo_dir=str(repo),
            opencode_exe="/fake/opencode",
            timeout=1,
        )

        import reverse_agent.platform_v1.opencode_executor as exec_mod
        original_run = subprocess.run
        exec_mod.subprocess.run = _make_fake_opencode_run(
            original_run,
            timeout_after=0,
        )
        try:
            result = executor.execute(task_id, store, workspace_root=str(workspace_root))
            assert result.success is False
            assert result.failure_classification == "timeout"
        finally:
            exec_mod.subprocess.run = original_run


def test_executor_malformed_json_does_not_crash() -> None:
    stdout = '{"partial": true\nnot json at all\n{"another": "ok"}\n'

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        _make_git_repo(repo)

        workspace_root = Path(td) / "ws"
        workspace_root.mkdir()

        store = TaskStore(":memory:")
        store.create_task(title="test", executor_kind="opencode", model_profile_ref="m")
        tasks = store.list_tasks()
        task_id = tasks[0].id

        executor = OpenCodeExecutor(
            model_id="sensetime/sensenova-6.7-flash-lite",
            repo_dir=str(repo),
            opencode_exe="/fake/opencode",
        )

        import reverse_agent.platform_v1.opencode_executor as exec_mod
        original_run = subprocess.run
        exec_mod.subprocess.run = _make_fake_opencode_run(
            original_run,
            stdout=stdout,
            returncode=0,
        )
        try:
            result = executor.execute(task_id, store, workspace_root=str(workspace_root))
            assert result.success is True
        finally:
            exec_mod.subprocess.run = original_run


def test_executor_changed_files_collected() -> None:
    stdout = '{"type": "tool", "action": "write"}\n'

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        _make_git_repo(repo)

        workspace_root = Path(td) / "ws"
        workspace_root.mkdir()

        store = TaskStore(":memory:")
        store.create_task(title="test", executor_kind="opencode", model_profile_ref="m")
        tasks = store.list_tasks()
        task_id = tasks[0].id

        executor = OpenCodeExecutor(
            model_id="sensetime/sensenova-6.7-flash-lite",
            repo_dir=str(repo),
            opencode_exe="/fake/opencode",
        )

        import reverse_agent.platform_v1.opencode_executor as exec_mod
        original_run = subprocess.run

        def fake_run(argv, **kwargs):
            if not argv or argv[0] != "/fake/opencode":
                joined = " ".join(str(a) for a in argv)
                if "numstat" in joined:
                    return subprocess.CompletedProcess(
                        args=argv,
                        returncode=0,
                        stdout="1\t0\talpha-ok.txt\n2\t1\tbeta.txt\n",
                        stderr="",
                    )
                return original_run(argv, **kwargs)
            return _fake_opencode_run(stdout=stdout, returncode=0)

        exec_mod.subprocess.run = fake_run
        try:
            result = executor.execute(task_id, store, workspace_root=str(workspace_root))
            assert result.success is True
            paths = [f["path"] for f in result.changed_files]
            assert "alpha-ok.txt" in paths
            assert "beta.txt" in paths
            alpha = next(f for f in result.changed_files if f["path"] == "alpha-ok.txt")
            assert alpha["additions"] == 1
            assert alpha["deletions"] == 0
        finally:
            exec_mod.subprocess.run = original_run


# ---------------------------------------------------------------------------
# Router dispatch
# ---------------------------------------------------------------------------

def test_router_dispatches_opencode() -> None:
    router = ExecutorRouter()
    assert "opencode" in router._registry

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        _make_git_repo(repo)

        workspace_root = Path(td) / "ws"
        workspace_root.mkdir()

        store = TaskStore(":memory:")
        store.create_task(title="t", executor_kind="opencode", model_profile_ref="m")
        tasks = store.list_tasks()
        task_id = tasks[0].id

        import reverse_agent.platform_v1.opencode_executor as exec_mod
        original_run = subprocess.run
        exec_mod.subprocess.run = _make_fake_opencode_run(original_run, stdout="", returncode=0)
        try:
            result = router.dispatch_execute(
                task_id=task_id,
                store=store,
                executor_kind="opencode",
                workspace_root=str(workspace_root),
                model_id="sensetime/sensenova-6.7-flash-lite",
                opencode_exe="/fake/opencode",
                repo_dir=str(repo),
            )
            assert isinstance(result, ExecutorResult)
        finally:
            exec_mod.subprocess.run = original_run


def test_router_dispatches_fixture_unchanged() -> None:
    router = ExecutorRouter()
    with tempfile.TemporaryDirectory() as td:
        store = TaskStore(":memory:")
        result = router.dispatch_execute(
            task_id="task-fix",
            store=store,
            executor_kind="deterministic_fixture",
            workspace_root=td,
        )
        assert result.success is True
        assert result.validation_exit_code == 0
        assert result.changed_files


# ---------------------------------------------------------------------------
# Deterministic validation independent of executor
# ---------------------------------------------------------------------------

def test_validation_fails_on_whitespace_error() -> None:
    stdout = '{"type": "tool", "action": "write"}\n'

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        _make_git_repo(repo)

        workspace_root = Path(td) / "ws"
        workspace_root.mkdir()

        store = TaskStore(":memory:")
        store.create_task(title="test", executor_kind="opencode", model_profile_ref="m")
        tasks = store.list_tasks()
        task_id = tasks[0].id

        executor = OpenCodeExecutor(
            model_id="sensetime/sensenova-6.7-flash-lite",
            repo_dir=str(repo),
            opencode_exe="/fake/opencode",
        )

        import reverse_agent.platform_v1.opencode_executor as exec_mod
        import reverse_agent.platform_v1.task_runtime as rt_mod
        original_run = subprocess.run

        def fake_run(argv, **kwargs):
            if not argv:
                return original_run(argv, **kwargs)
            if argv[0] != "/fake/opencode":
                if argv[0] == "git" and "--check" in argv:
                    return subprocess.CompletedProcess(
                        args=argv,
                        returncode=1,
                        stdout="warning: trailing whitespace in alpha.txt:1\n",
                        stderr="",
                    )
                return original_run(argv, **kwargs)
            return _fake_opencode_run(stdout=stdout, returncode=0)

        exec_mod.subprocess.run = fake_run
        rt_mod.subprocess.run = fake_run
        try:
            result = executor.execute(task_id, store, workspace_root=str(workspace_root))
            assert result.success is False
            assert result.validation_exit_code == 1
            assert result.failure_classification == "deterministic_validation_failure"
        finally:
            exec_mod.subprocess.run = original_run
            rt_mod.subprocess.run = original_run


# ---------------------------------------------------------------------------
# Recursive redaction
# ---------------------------------------------------------------------------

def test_redact_event_nested_authorization_header() -> None:
    event = {"headers": {"Authorization": "Bearer ghp_abcdefghijklmnopqrstuvwxyz123456"}}
    result = redact_event(event)
    assert result["headers"]["Authorization"] == "[REDACTED]"


def test_redact_event_nested_credentials_list() -> None:
    event = {"request": {"credentials": [{"token": "verysecret123456"}, {"safe": "value"}]}}
    result = redact_event(event)
    assert result["request"]["credentials"][0]["token"] == "[REDACTED]"
    assert result["request"]["credentials"][1]["safe"] == "value"


def test_redact_event_preserves_safe_structure() -> None:
    event = {"safe_key": "safe_value", "nested": {"a": 1, "b": [2, 3]}}
    result = redact_event(event)
    assert result["safe_key"] == "safe_value"
    assert result["nested"]["a"] == 1
    assert result["nested"]["b"] == [2, 3]


def test_redact_event_bounded_depth() -> None:
    event = {"a": {"b": {"c": {"d": {"e": {"f": {"g": "deep"}}}}}}}
    result = redact_event(event)
    assert isinstance(result, dict)
    assert "[REDACTED: max_depth_exceeded]" in json.dumps(result)


# ---------------------------------------------------------------------------
# Bounded structured executor evidence
# ---------------------------------------------------------------------------

def test_executor_evidence_bounded_count() -> None:
    stdout_lines = [json.dumps({"type": "tool_call", "action": "write_file", "path": "a.txt"}) for _ in range(100)]
    stdout = "\n".join(stdout_lines) + "\n"

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        _make_git_repo(repo)

        workspace_root = Path(td) / "ws"
        workspace_root.mkdir()

        store = TaskStore(":memory:")
        store.create_task(title="test", executor_kind="opencode", model_profile_ref="m")
        tasks = store.list_tasks()
        task_id = tasks[0].id

        executor = OpenCodeExecutor(
            model_id="sensetime/sensenova-6.7-flash-lite",
            repo_dir=str(repo),
            opencode_exe="/fake/opencode",
        )

        import reverse_agent.platform_v1.opencode_executor as exec_mod
        original_run = subprocess.run
        exec_mod.subprocess.run = _make_fake_opencode_run(
            original_run,
            stdout=stdout,
            returncode=0,
        )
        try:
            result = executor.execute(task_id, store, workspace_root=str(workspace_root))
            assert len(result.executor_evidence) <= 40
        finally:
            exec_mod.subprocess.run = original_run


# ---------------------------------------------------------------------------
# Windows metacharacter safety in task text
# ---------------------------------------------------------------------------

def test_build_prompt_metacharacters_remain_data() -> None:
    task = "write alpha-ok & pipe | redirect > < percent % bang ! caret ^ quotes \" ' paren ()"
    task += "\n"
    task += "CRLF\r\n"
    prompt = build_prompt(task, "/tmp/ws")
    assert task in prompt
    assert "AUTHORITY CONSTRAINTS" in prompt
    assert "commit" in prompt.lower()


def test_build_opencode_argv_never_uses_shell() -> None:
    argv, positional = build_opencode_argv(
        "/fake/opencode",
        is_cmd=False,
        model_id="m",
        worktree="/tmp/ws",
        prompt_file="/tmp/p.txt",
    )
    assert all(not any(c in a for c in "&|><;") for a in argv)
    assert positional == "execute bounded task from attached prompt file"


# ---------------------------------------------------------------------------
# Accurate untracked-file line additions
# ---------------------------------------------------------------------------

def test_collect_changed_files_untracked_counts_lines_not_bytes() -> None:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        _make_git_repo(repo)

        workspace_root = Path(td) / "ws"
        workspace_root.mkdir()

        store = TaskStore(":memory:")
        store.create_task(title="test", executor_kind="opencode", model_profile_ref="m")
        tasks = store.list_tasks()
        task_id = tasks[0].id

        executor = OpenCodeExecutor(
            model_id="sensetime/sensenova-6.7-flash-lite",
            repo_dir=str(repo),
            opencode_exe="/fake/opencode",
        )

        import reverse_agent.platform_v1.opencode_executor as exec_mod
        original_run = subprocess.run

        def fake_run(argv, **kwargs):
            if not argv or argv[0] != "/fake/opencode":
                if argv[0] == "git" and "others" in argv:
                    return subprocess.CompletedProcess(
                        args=argv,
                        returncode=0,
                        stdout="issue127_acceptance_output.txt\n",
                        stderr="",
                    )
                return original_run(argv, **kwargs)
            cwd = kwargs.get("cwd") or ""
            out_file = Path(cwd) / "issue127_acceptance_output.txt"
            out_file.write_text("alpha-ok\n", encoding="utf-8")
            return _fake_opencode_run(stdout="", returncode=0)

        exec_mod.subprocess.run = fake_run
        try:
            result = executor.execute(task_id, store, workspace_root=str(workspace_root))
            paths = [f["path"] for f in result.changed_files]
            assert "issue127_acceptance_output.txt" in paths
            entry = next(f for f in result.changed_files if f["path"] == "issue127_acceptance_output.txt")
            assert entry["additions"] == 1
        finally:
            exec_mod.subprocess.run = original_run
