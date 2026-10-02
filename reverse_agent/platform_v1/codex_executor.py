"""Thin native Codex CLI adapter; shared worktrees and Task validation stay local."""

from __future__ import annotations

import os
import hashlib
import queue
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .codex_protocol import CodexJsonl, CodexProtocolError, public_text
from .opencode_executor import _collect_final_product_files, _emit, _persist_usage_observations
from .repository_preparation import prepare_linked_worktree
from .task_runtime import ExecutorResult, ExecutorRuntimeError, LocalValidationRunner


def validate_codex_model(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value):
        raise ExecutorRuntimeError("codex_model_id_invalid")
    return value


def codex_child_env(parent: Mapping[str, str]) -> dict[str, str]:
    """CLI owns its saved login; provider keys, endpoints and relay tokens stay out."""
    allowed = {
        "path", "systemroot", "pathext", "home", "userprofile", "localappdata",
        "appdata", "temp", "tmp", "codex_home", "lang", "lc_all",
    }
    return {k: v for k, v in parent.items() if k.casefold() in allowed}


def resolve_codex_cli(exe: str | None = None) -> str:
    candidate = exe or os.environ.get("REVERSE_AGENT_CODEX_EXE") or shutil.which("codex.exe" if os.name == "nt" else "codex")
    if not candidate:
        raise ExecutorRuntimeError("codex_cli_missing")
    path = Path(candidate).resolve()
    if not path.is_file() or (os.name == "nt" and path.suffix.casefold() != ".exe"):
        raise ExecutorRuntimeError("codex_cli_requires_native_executable")
    return str(path)


def probe_codex_readiness(exe: str | None = None) -> str:
    """Opt-in trusted-host metadata probe; no inference or raw auth-file access."""
    try:
        cli = resolve_codex_cli(exe)
        environment = codex_child_env(os.environ)
        for args in (["exec", "--help"], ["login", "status"]):
            result = subprocess.run([cli, *args], env=environment, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5,
                check=False, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            output = result.stdout + result.stderr
            if len(output.encode()) > 32 * 1024:
                return "probe_output_invalid"
            if result.returncode:
                return "managed_login_unavailable" if args[0] == "login" else "cli_unavailable"
            if args[0] == "exec" and not all(flag in output for flag in ("--json", "--ephemeral", "--ignore-user-config", "--sandbox")):
                return "cli_incompatible"
            if args[0] == "login" and output.strip() != "Logged in using ChatGPT":
                return "managed_login_unavailable"
        return "managed_login_ready"
    except (ExecutorRuntimeError, OSError, subprocess.SubprocessError):
        return "cli_unavailable"


def build_codex_argv(cli: str, cwd: Path, model: str, sandbox: str) -> list[str]:
    if sandbox not in {"read-only", "workspace-write"}:
        raise ExecutorRuntimeError("codex_sandbox_invalid")
    return [cli, "exec", "--ignore-user-config", "--ephemeral", "--json", "--color", "never",
            "--sandbox", sandbox, "--model", validate_codex_model(model), "--cd", str(cwd),
            "-c", 'approval_policy="never"', "-c", 'model_provider="openai"', "-"]


@dataclass(frozen=True)
class CodexPreparedContext:
    worktree: Path
    base_sha: str
    execution_id: str
    cli_path: str
    executor_kind: str = "codex"


def codex_executor_kwargs(task, *, binding_resolver, artifact_input=None):
    """Resolve public saved binding and trusted source; no model/profile fallback."""
    from .binding_resolver import BindingResolver
    from .repository_workspace import resolve_repository_workspace
    binding_ref = getattr(task, "binding_ref", "")
    if isinstance(task, Mapping):
        binding_ref = task.get("binding_ref", "")
        repository, branch = task.get("repository", ""), task.get("branch", "")
    else:
        repository, branch = task.repository, task.branch
    if not binding_ref:
        raise ExecutorRuntimeError("codex_binding_required")
    resolved = (binding_resolver or BindingResolver()).resolve(binding_ref, task_executor="codex")
    source = resolve_repository_workspace(repository)
    base = artifact_input["producer"]["commit"] if artifact_input is not None else branch
    if not isinstance(base, str) or not re.fullmatch(r"[0-9a-f]{40}", base):
        raise ExecutorRuntimeError("codex_requires_exact_base_sha")
    return {"binding_resolution": resolved, "repo_dir": str(source.repo_dir), "base_ref": base}


class CodexExecutor:
    def __init__(self, *, model_id: str = "", binding_resolution=None, repo_dir: str = "",
                 base_ref: str = "", codex_exe: str | None = None, timeout: float = 300,
                 sandbox: str = "workspace-write", parent_env=None, process_factory=None,
                 readiness_probe=None):
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 600:
            raise ExecutorRuntimeError("codex_timeout_invalid")
        if binding_resolution is not None:
            if binding_resolution.executor_id != "codex" or binding_resolution.auth_method != "external_cli_session" or binding_resolution.relay_required:
                raise ExecutorRuntimeError("codex_requires_managed_session_binding")
            if binding_resolution.external_session_status not in {"available", "executor_managed"}:
                raise ExecutorRuntimeError("codex_session_unavailable")
            model_id = binding_resolution.model_id
        self._model_id = validate_codex_model(model_id)
        self._repo_dir = repo_dir
        self._base_ref = base_ref
        self._codex_exe = codex_exe
        self._timeout = float(timeout)
        self._sandbox = sandbox
        self._parent_env = os.environ if parent_env is None else parent_env
        self._process_factory = process_factory or subprocess.Popen
        self._readiness_probe = readiness_probe or probe_codex_readiness
        build_codex_argv("codex", Path("."), self._model_id, sandbox)

    def prepare_worktree_once(self, task_id, root_path, event_callback=None):
        cli = resolve_codex_cli(self._codex_exe)
        if self._readiness_probe(cli) != "managed_login_ready":
            raise ExecutorRuntimeError("codex_managed_login_unavailable")
        if not re.fullmatch(r"[0-9a-f]{40}", self._base_ref):
            raise ExecutorRuntimeError("codex_requires_exact_base_sha")
        worktree, base = prepare_linked_worktree(task_id, Path(root_path), event_callback,
            repo_dir_value=self._repo_dir, base_ref=self._base_ref)
        prepared = CodexPreparedContext(worktree, base, f"exec-{task_id}", cli)
        _emit(event_callback, task_id, {"type": "WORKSPACE_READY", "title": "Codex workspace ready",
            "description": "Isolated workspace bound to approved base", "metadata": {
                "workspace": str(worktree), "base_sha": base, "executor_kind": "codex",
                "execution_id": prepared.execution_id, "model": self._model_id}})
        return prepared

    def reconstruct_prepared_context(self, *, worktree_path, base_sha, execution_id, **_):
        worktree = Path(worktree_path).resolve()
        self._verify_workspace(worktree, base_sha)
        return CodexPreparedContext(worktree, base_sha, execution_id, resolve_codex_cli(self._codex_exe))

    def _verify_workspace(self, worktree, expected):
        self._verify_head(worktree, expected)
        source = Path(self._repo_dir).resolve()
        worktree = worktree.resolve()
        if expected != self._base_ref or worktree == source or source in worktree.parents:
            raise ExecutorRuntimeError("codex_worktree_identity_invalid")
        def common_directory(root):
            result = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=root,
                capture_output=True, text=True, timeout=10, check=False)
            if result.returncode or not result.stdout.strip() or len(result.stdout) > 4096:
                raise ExecutorRuntimeError("codex_worktree_identity_invalid")
            return (root / result.stdout.strip()).resolve()
        if not (worktree / ".git").is_file() or common_directory(source) != common_directory(worktree):
            raise ExecutorRuntimeError("codex_worktree_identity_invalid")

    @staticmethod
    def _verify_head(worktree, expected):
        if not re.fullmatch(r"[0-9a-f]{40}", expected) or not worktree.is_dir():
            raise ExecutorRuntimeError("codex_worktree_identity_invalid")
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=worktree, capture_output=True,
                                text=True, timeout=10, check=False)
        if result.returncode or result.stdout.strip() != expected:
            raise ExecutorRuntimeError("codex_worktree_head_mismatch")

    def execute(self, task_id, store, *, workspace_root="", event_callback=None):
        from .opencode_executor import RoleContext
        if not workspace_root:
            raise ExecutorRuntimeError("workspace_root_required")
        prepared = self.prepare_worktree_once(task_id, Path(workspace_root), event_callback)
        return self.execute_role_prepared(prepared, store,
            role_context=RoleContext("executor", task_id, prepared.worktree), event_callback=event_callback)

    def execute_role_prepared(self, prepared, store, *, role_context, event_callback=None):
        if role_context.role != "executor":
            raise ExecutorRuntimeError("codex_single_mode_only")
        if getattr(prepared, "executor_kind", "") != "codex" or Path(role_context.workspace).resolve() != prepared.worktree.resolve():
            raise ExecutorRuntimeError("codex_prepared_identity_mismatch")
        task_id = role_context.task_id
        if prepared.execution_id != f"exec-{task_id}" or prepared.worktree.name != task_id:
            raise ExecutorRuntimeError("codex_task_identity_mismatch")
        self._verify_workspace(prepared.worktree, prepared.base_sha)
        if (prepared.worktree / ".codex" / "config.toml").exists():
            # Do not inspect config that can install hooks or replace provider authority.
            raise ExecutorRuntimeError("codex_project_configuration_unapproved")
        task = store.get_task(task_id)
        title = getattr(task, "title", "")
        if not isinstance(title, str) or not title.strip() or len(title.encode()) > 64 * 1024:
            raise ExecutorRuntimeError("codex_task_instruction_invalid")
        prompt = ("Perform only this admitted task inside this isolated workspace. Preserve existing work. "
                  "Do not commit, push, merge, access credentials, install dependencies, or bypass policy. "
                  "Report changes and checks truthfully; CLI success is not functional acceptance.\n\n" + title)
        def progress(item):
            _emit(event_callback, task_id, {"type": "EXECUTOR_PROGRESS", "title": "Codex",
                "description": public_text(item.get("text") or item.get("command") or "Codex activity"),
                "metadata": {"executor_kind": "codex", "event": item}})
        parser = CodexJsonl(progress)
        code = None
        def persist_unknown_usage():
            identity = hashlib.sha256((prepared.execution_id + ":" + (parser.turn.thread_id or "no-thread")).encode()).hexdigest()
            _persist_usage_observations(store, task_id, [{
                "observation_id": "usage-codex-" + identity, "execution_id": prepared.execution_id,
                "role": "executor", "model_id": self._model_id, "provider_id": "codex",
                "source_kind": "assistant_message", "source_id": "codex-turn-" + identity,
                # CLI tokens do not provide reasoning/cache-write or dollar cost.
                "status": "UNKNOWN",
            }])
        try:
            code = self._stream(prepared, prompt, parser)
            turn = parser.finish()
            if code != 0 or turn.failed:
                raise CodexProtocolError(turn.failure_classification or "codex_process_failed")
            self._verify_workspace(prepared.worktree, prepared.base_sha)
        except (ExecutorRuntimeError, OSError) as exc:
            persist_unknown_usage()
            classification = str(exc) if isinstance(exc, ExecutorRuntimeError) else "codex_process_start_failed"
            return ExecutorResult(False, -1, "", "", "", error=classification,
                workspace=str(prepared.worktree), execution_id=prepared.execution_id,
                process_exit_code=code, failure_classification=classification)
        persist_unknown_usage()
        _emit(event_callback, task_id, {"type": "EXECUTOR_COMPLETED", "title": "Codex response",
            "description": public_text(turn.final_text), "metadata": {"executor_kind": "codex",
                "final_text": turn.final_text, "usage_status": "observed_tokens" if turn.usage is not None else "unknown",
                "token_usage": turn.usage, "cost_status": "unknown", "process_exit_code": code}})
        exit_code, summary, digest = LocalValidationRunner().run(task_id=task_id, command_id="git_diff_check", cwd=str(prepared.worktree))
        return ExecutorResult(exit_code == 0, exit_code, "git_diff_check", digest, summary,
            changed_files=_collect_final_product_files(prepared.worktree), workspace=str(prepared.worktree),
            execution_id=prepared.execution_id, process_exit_code=code,
            failure_classification="" if exit_code == 0 else "patch_hygiene_failed")

    def _stream(self, prepared, prompt, parser):
        from .functional_validation import _WindowsJob, _terminate
        job = _WindowsJob() if os.name == "nt" else None
        try:
            proc = self._process_factory(build_codex_argv(prepared.cli_path, prepared.worktree, self._model_id, self._sandbox),
                cwd=str(prepared.worktree), env=codex_child_env(self._parent_env), stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,
                start_new_session=os.name != "nt",
                creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW | 4) if job else 0)
            if job:
                try:
                    job.attach_and_resume(proc)
                except BaseException:
                    job.close()
                    if proc.poll() is None:
                        proc.kill()
                    proc.wait(timeout=5)
                    raise
        except BaseException:
            if job:
                job.close()
            raise
        packets = queue.Queue(maxsize=16)
        stopping = threading.Event()
        def send(packet):
            while not stopping.is_set():
                try:
                    packets.put(packet, timeout=0.1)
                    return
                except queue.Full:
                    pass
        def read(pipe, channel):
            try:
                while not stopping.is_set():
                    chunk = pipe.read1(4096) if hasattr(pipe, "read1") else pipe.read(4096)
                    if not chunk:
                        break
                    send((channel, chunk))
            except (OSError, ValueError):
                send(("reader_error", b""))
            finally:
                send((channel, None))
        readers = [threading.Thread(target=read, args=(proc.stdout, "out"), daemon=True),
                   threading.Thread(target=read, args=(proc.stderr, "err"), daemon=True)]
        def write_prompt():
            try:
                proc.stdin.write(prompt.encode())
                proc.stdin.close()
            except (OSError, ValueError):
                send(("writer_error", b""))
        readers.append(threading.Thread(target=write_prompt, daemon=True))
        for reader in readers:
            reader.start()
        deadline = time.monotonic() + self._timeout
        finished = set()
        stderr_bytes = 0
        try:
            while len(finished) < 2:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise CodexProtocolError("codex_timeout")
                try:
                    channel, chunk = packets.get(timeout=min(remaining, 0.1))
                except queue.Empty:
                    continue
                if channel == "reader_error":
                    raise CodexProtocolError("codex_stream_read_failed")
                if channel == "writer_error":
                    raise CodexProtocolError("codex_stdin_write_failed")
                if chunk is None:
                    finished.add(channel)
                elif channel == "out":
                    parser.feed(chunk)
                else:
                    stderr_bytes += len(chunk)
                    if stderr_bytes > 256 * 1024:
                        raise CodexProtocolError("codex_stderr_limit_exceeded")
            try:
                return proc.wait(timeout=max(0.001, deadline - time.monotonic()))
            except subprocess.TimeoutExpired as exc:
                raise CodexProtocolError("codex_timeout") from exc
        finally:
            stopping.set()
            # Close only this owned process tree, including surviving tool children.
            _terminate(proc, job)
            for pipe in (proc.stdin, proc.stdout, proc.stderr):
                pipe.close()
            for reader in readers:
                reader.join(timeout=1)
