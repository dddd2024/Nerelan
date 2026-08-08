"""OpenCode executor unit tests.

All tests use a fake/injected CLI subprocess. No live OpenCode invocation occurs.
"""

import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path

import pytest

from reverse_agent.platform_v1.opencode_executor import (
    OpenCodeExecutor,
    build_opencode_argv,
    build_prompt,
    redact_event,
    redact_secrets,
    resolve_opencode_cli,
)
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import (
    ExecutorRuntimeError,
    ExecutorRouter,
    ExecutorResult,
)


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
        prompt="create alpha-ok file",
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
        "--",
        "create alpha-ok file",
    ]


def test_build_opencode_argv_cmd_path_passed_directly() -> None:
    argv, prompt = build_opencode_argv(
        "C:\\tools\\opencode.cmd",
        is_cmd=True,
        model_id="sensetime/sensenova-6.7-flash-lite",
        worktree="C:\\ws",
        prompt="do stuff",
    )
    assert argv[0] == "C:\\tools\\opencode.cmd"
    assert "run" in argv
    assert "--model" in argv
    assert "sensetime/sensenova-6.7-flash-lite" in argv


def test_build_opencode_argv_auto_flag() -> None:
    argv, _ = build_opencode_argv(
        "/usr/bin/opencode",
        is_cmd=False,
        model_id="m",
        worktree="/ws",
        prompt="p",
        use_auto=True,
    )
    assert "--auto" in argv

    argv_no_auto, _ = build_opencode_argv(
        "/usr/bin/opencode",
        is_cmd=False,
        model_id="m",
        worktree="/ws",
        prompt="p",
        use_auto=False,
    )
    assert "--auto" not in argv_no_auto


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

def test_build_prompt_contains_task() -> None:
    prompt = build_prompt("create alpha-ok file", "/tmp/ws")
    assert "create alpha-ok file" in prompt


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
    assert len(result["output"]) <= 250


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
        store = TaskStore(":memory:")
        store.create_task(title="test", executor_kind="opencode", model_profile_ref="m")
        tasks = store.list_tasks()
        task_id = tasks[0].id

        executor = OpenCodeExecutor(
            model_id="sensetime/sensenova-6.7-flash-lite",
            opencode_exe="/fake/opencode",
        )
        received_argvs: list[list[str]] = []

        original_run = subprocess.run

        def fake_run(argv, **kwargs):
            received_argvs.append(list(argv))
            return subprocess.CompletedProcess(
                args=argv,
                returncode=0,
                stdout=stdout,
                stderr="",
            )

        import reverse_agent.platform_v1.opencode_executor as exec_mod
        exec_mod.subprocess.run = fake_run
        try:
            result = executor.execute(task_id, store, workspace_root=td)
            assert result.success is True
            assert result.validation_exit_code == 0
            assert result.validation_command_id == "git_diff_check"
            assert result.execution_id
            assert received_argvs
            opencode_call = next(
                (a for a in received_argvs if a[0] == "/fake/opencode"),
                None,
            )
            assert opencode_call is not None
            assert "run" in opencode_call
            assert "--model" in opencode_call
            assert "sensetime/sensenova-6.7-flash-lite" in opencode_call
            assert "--format" in opencode_call
            assert "json" in opencode_call
        finally:
            exec_mod.subprocess.run = original_run


def test_executor_requires_model_id() -> None:
    with pytest.raises(ExecutorRuntimeError, match="model_id_required"):
        OpenCodeExecutor(model_id="")


def test_executor_requires_workspace_root() -> None:
    exec_ = OpenCodeExecutor(model_id="m", opencode_exe="/fake/opencode")
    with pytest.raises(ExecutorRuntimeError, match="workspace_root_required"):
        exec_.execute("t", TaskStore(":memory:"))


# ---------------------------------------------------------------------------
# Failure paths
# ---------------------------------------------------------------------------

def test_executor_nonzero_exit_classification() -> None:
    with tempfile.TemporaryDirectory() as td:
        store = TaskStore(":memory:")
        store.create_task(title="test", executor_kind="opencode", model_profile_ref="m")
        tasks = store.list_tasks()
        task_id = tasks[0].id

        executor = OpenCodeExecutor(
            model_id="m",
            opencode_exe="/fake/opencode",
        )

        import reverse_agent.platform_v1.opencode_executor as exec_mod
        original_run = subprocess.run

        def fake_run(argv, **kwargs):
            if argv[:2] == ["git", "init"]:
                return subprocess.CompletedProcess(args=argv, returncode=0, stdout="", stderr="")
            if argv[:1] == ["cmd.exe"]:
                return subprocess.CompletedProcess(args=argv, returncode=0, stdout="", stderr="")
            return subprocess.CompletedProcess(args=argv, returncode=42, stdout="", stderr="auth failure")

        exec_mod.subprocess.run = fake_run
        try:
            result = executor.execute(task_id, store, workspace_root=td)
            assert result.success is False
            assert result.failure_classification == "executor_nonzero"
            assert result.process_exit_code == 42
        finally:
            exec_mod.subprocess.run = original_run


def test_executor_timeout() -> None:
    with tempfile.TemporaryDirectory() as td:
        store = TaskStore(":memory:")
        store.create_task(title="test", executor_kind="opencode", model_profile_ref="m")
        tasks = store.list_tasks()
        task_id = tasks[0].id

        executor = OpenCodeExecutor(
            model_id="m",
            opencode_exe="/fake/opencode",
            timeout=1,
        )

        import reverse_agent.platform_v1.opencode_executor as exec_mod
        original_run = subprocess.run

        call_count = {"n": 0}

        def fake_run(argv, **kwargs):
            call_count["n"] += 1
            if call_count["n"] > 5:
                raise subprocess.TimeoutExpired(cmd=argv, timeout=1)
            return subprocess.CompletedProcess(args=argv, returncode=0, stdout="", stderr="")

        exec_mod.subprocess.run = fake_run
        try:
            result = executor.execute(task_id, store, workspace_root=td)
            assert result.success is False
            assert result.failure_classification == "timeout"
        finally:
            exec_mod.subprocess.run = original_run


def test_executor_malformed_json_does_not_crash() -> None:
    stdout = '{"partial": true\nnot json at all\n{"another": "ok"}\n'

    with tempfile.TemporaryDirectory() as td:
        store = TaskStore(":memory:")
        store.create_task(title="test", executor_kind="opencode", model_profile_ref="m")
        tasks = store.list_tasks()
        task_id = tasks[0].id

        executor = OpenCodeExecutor(
            model_id="m",
            opencode_exe="/fake/opencode",
        )

        import reverse_agent.platform_v1.opencode_executor as exec_mod
        original_run = subprocess.run

        def fake_run(argv, **kwargs):
            return subprocess.CompletedProcess(args=argv, returncode=0, stdout=stdout, stderr="")

        exec_mod.subprocess.run = fake_run
        try:
            result = executor.execute(task_id, store, workspace_root=td)
            assert result.success is True
        finally:
            exec_mod.subprocess.run = original_run


def test_executor_changed_files_collected() -> None:
    stdout = '{"type": "tool", "action": "write"}\n'

    with tempfile.TemporaryDirectory() as td:
        store = TaskStore(":memory:")
        store.create_task(title="test", executor_kind="opencode", model_profile_ref="m")
        tasks = store.list_tasks()
        task_id = tasks[0].id

        executor = OpenCodeExecutor(
            model_id="m",
            opencode_exe="/fake/opencode",
        )

        import reverse_agent.platform_v1.opencode_executor as exec_mod
        original_run = subprocess.run

        def fake_run(argv, **kwargs):
            if argv[:1] == ["git"] and "diff" in argv:
                return subprocess.CompletedProcess(
                    args=argv,
                    returncode=0,
                    stdout="1\t0\talpha-ok.txt\n2\t1\tbeta.txt\n",
                    stderr="",
                )
            if "commit" in argv:
                return subprocess.CompletedProcess(args=argv, returncode=0, stdout="", stderr="")
            if "config" in argv:
                return subprocess.CompletedProcess(args=argv, returncode=0, stdout="", stderr="")
            return subprocess.CompletedProcess(args=argv, returncode=0, stdout=stdout, stderr="")

        exec_mod.subprocess.run = fake_run
        try:
            result = executor.execute(task_id, store, workspace_root=td)
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
        store = TaskStore(":memory:")
        store.create_task(title="t", executor_kind="opencode", model_profile_ref="m")
        tasks = store.list_tasks()
        task_id = tasks[0].id

        import reverse_agent.platform_v1.opencode_executor as exec_mod
        original_run = subprocess.run

        def fake_run(argv, **kwargs):
            return subprocess.CompletedProcess(args=argv, returncode=0, stdout="", stderr="")

        exec_mod.subprocess.run = fake_run
        try:
            result = router.dispatch_execute(
                task_id=task_id,
                store=store,
                executor_kind="opencode",
                workspace_root=td,
                model_id="sensetime/sensenova-6.7-flash-lite",
                opencode_exe="/fake/opencode",
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
        store = TaskStore(":memory:")
        store.create_task(title="test", executor_kind="opencode", model_profile_ref="m")
        tasks = store.list_tasks()
        task_id = tasks[0].id

        executor = OpenCodeExecutor(
            model_id="m",
            opencode_exe="/fake/opencode",
        )

        import reverse_agent.platform_v1.opencode_executor as exec_mod
        original_run = subprocess.run

    call_num = {"n": 0}

    def fake_run(argv, **kwargs):
        call_num["n"] += 1
        if any("check" in str(a) for a in argv):
            return subprocess.CompletedProcess(
                args=argv,
                returncode=1,
                stdout="warning: trailing whitespace in alpha.txt:1\n",
                stderr="",
            )
        if "commit" in argv or "config" in argv or "init" in argv or "add" in argv:
            return subprocess.CompletedProcess(args=argv, returncode=0, stdout="", stderr="")
        return subprocess.CompletedProcess(args=argv, returncode=0, stdout=stdout, stderr="")

        exec_mod.subprocess.run = fake_run
        try:
            result = executor.execute(task_id, store, workspace_root=td)
            assert result.success is False
            assert result.validation_exit_code == 1
            assert result.failure_classification == "deterministic_validation_failure"
        finally:
            exec_mod.subprocess.run = original_run
