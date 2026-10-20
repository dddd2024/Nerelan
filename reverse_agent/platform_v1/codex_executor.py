"""Thin native Codex CLI adapter; shared worktrees and Task validation stay local."""

from __future__ import annotations

import os
import hashlib
import queue
import re
import secrets
import shutil
import stat
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


_TASK_TEMP = ".nt"  # Legacy fixed name: older residue is never adopted or deleted.
_TASK_TEMP_PREFIX = ".nt-"
_ANCHORED_WRITE = (hasattr(os, "O_DIRECTORY") and hasattr(os, "O_NOFOLLOW")
                   and os.open in os.supports_dir_fd)


def _is_task_temp(path: str) -> bool:
    top = path.replace("\\", "/").split("/", 1)[0]
    return top == _TASK_TEMP or top.startswith(_TASK_TEMP_PREFIX)


def _plain_directory(info: os.stat_result) -> bool:
    return (stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode)
            and not getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _write_scratch_ignore(scratch: Path, identity: tuple[int, int]) -> None:
    """Create the local ignore file inside the exact directory just made.

    Where the platform supports it, the write is anchored to a no-follow
    directory handle so a swapped path cannot redirect it. Otherwise the
    exclusive create can only add a new file, and the directory identity is
    re-checked afterwards so a substitution still fails closed.
    """
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if _ANCHORED_WRITE:
        directory = os.open(scratch, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            info = os.fstat(directory)
            if (info.st_dev, info.st_ino) != identity:
                raise OSError("scratch replaced")
            handle = os.open(".gitignore", flags | os.O_NOFOLLOW, 0o666, dir_fd=directory)
        finally:
            os.close(directory)
    else:
        handle = os.open(scratch / ".gitignore", flags, 0o666)
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write("*\n")
    info = scratch.lstat()
    if not _plain_directory(info) or (info.st_dev, info.st_ino) != identity:
        raise OSError("scratch replaced")


def _task_temp_env(worktree: Path, environment: Mapping[str, str]) -> dict[str, str]:
    """Create fresh, short execution scratch, never reuse repository content.

    No readiness probe calls this. Every native attempt gets its own
    unpredictable ``.nt-*`` directory, created exclusively, so a retry in the
    same worktree never collides with an earlier attempt. Earlier scratch,
    including the legacy ``.nt``, is never adopted, followed or deleted.
    """
    try:
        root = worktree.absolute()
        for component in (*reversed(root.parents), root):
            if not _plain_directory(component.lstat()):
                raise OSError("unverifiable workspace")
        if root.resolve(strict=True) != root:
            raise OSError("unverifiable workspace")
        tracked = subprocess.run(["git", "ls-files", "--", _TASK_TEMP, _TASK_TEMP_PREFIX + "*"], cwd=root,
            capture_output=True, timeout=10, check=False)
        if tracked.returncode:
            # A read-only planner may operate in an ordinary (non-Git)
            # directory. Do not require a Git index where none exists.
            # Any visible Git marker, including a worktree .git file,
            # means a failed index check must remain fatal.
            for ancestor in (root, *root.parents):
                try:
                    (ancestor / ".git").lstat()
                except FileNotFoundError:
                    continue
                raise OSError("Git index unavailable")
            if b"not a git repository" not in tracked.stderr.lower():
                raise OSError("Git index unavailable")
        if tracked.stdout:
            # Scratch is excluded from product evidence, so tracked
            # repository content under its names must never be hidden.
            raise OSError("reserved scratch is tracked")
        scratch = root / (_TASK_TEMP_PREFIX + secrets.token_hex(6))
        scratch.mkdir()  # Inherit workspace permissions; no exist_ok or parents.
        info = scratch.lstat()
        if not _plain_directory(info) or scratch.resolve(strict=True) != scratch:
            raise OSError("unverifiable scratch")
        # Local ignore only: no shared Git configuration or exclude-file edits.
        # This also keeps ordinary Git-based role snapshots free of scratch.
        _write_scratch_ignore(scratch, (info.st_dev, info.st_ino))
        if scratch.resolve(strict=True) != scratch:
            raise OSError("scratch escaped workspace")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        raise ExecutorRuntimeError("native_task_temp_unavailable") from exc
    result = {k: v for k, v in environment.items() if k.casefold() not in {"temp", "tmp", "tmpdir"}}
    result.update(TEMP=str(scratch), TMP=str(scratch))
    if os.name != "nt":
        result["TMPDIR"] = str(scratch)
    return result


def validate_codex_model(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value):
        raise ExecutorRuntimeError("codex_model_id_invalid")
    return value


def codex_child_env(parent: Mapping[str, str]) -> dict[str, str]:
    """CLI owns its saved login; provider keys, endpoints and relay tokens stay out."""
    allowed = {
        "path", "systemroot", "pathext", "home", "userprofile", "localappdata",
        "appdata", "temp", "tmp", "codex_home", "lang", "lc_all",
        # Proxy variables stay out: their URLs can carry credentials.
        "systemdrive", "comspec", "windir", "programfiles", "programfiles(x86)", "programdata",
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
    argv = [cli, "exec", "--ignore-user-config", "--ephemeral", "--json", "--color", "never",
            "--sandbox", sandbox, "--model", validate_codex_model(model), "--cd", str(cwd),
            "-c", 'approval_policy="never"', "-c", 'model_provider="openai"']
    if os.name == "nt":
        # Ignoring user config also removes the configured Windows sandbox.
        # Select the provisioned restricted sandbox; never fall back to full access.
        argv.extend(["-c", 'windows.sandbox="elevated"'])
    return [*argv, "-"]


@dataclass(frozen=True)
class CodexPreparedContext:
    worktree: Path
    base_sha: str
    execution_id: str
    cli_path: str
    executor_kind: str = "codex"


def codex_executor_kwargs(task, *, binding_resolver, artifact_input=None, kind="codex"):
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
        raise ExecutorRuntimeError(f"{kind}_binding_required")
    resolved = (binding_resolver or BindingResolver()).resolve(binding_ref, task_executor=kind)
    source = resolve_repository_workspace(repository)
    base = artifact_input["producer"]["commit"] if artifact_input is not None else branch
    if not isinstance(base, str) or not re.fullmatch(r"[0-9a-f]{40}", base):
        raise ExecutorRuntimeError(f"{kind}_requires_exact_base_sha")
    return {"binding_resolution": resolved, "repo_dir": str(source.repo_dir), "base_ref": base}


class CodexExecutor:
    """Native Codex CLI executor. Subclasses override only the CLI-specific hooks."""

    KIND = "codex"
    LABEL = "Codex"
    PROVIDER_ID = "codex"
    # Workspace config that could install hooks or replace provider authority.
    PROJECT_CONFIG: tuple[str, ...] = (".codex/config.toml",)
    default_readiness_probe = staticmethod(probe_codex_readiness)

    def _e(self, suffix: str) -> str:
        return f"{self.KIND}_{suffix}"

    def _validate_options(self) -> None:
        build_codex_argv("codex", Path("."), self._model_id, self._sandbox)

    def _resolve_cli(self) -> str:
        return resolve_codex_cli(self._codex_exe)

    def _argv(self, prepared) -> list[str]:
        return build_codex_argv(prepared.cli_path, prepared.worktree, self._model_id, self._sandbox)

    def _child_env(self) -> dict[str, str]:
        return codex_child_env(self._parent_env)

    def _parser(self, callback):
        return CodexJsonl(callback)

    def __init__(self, *, model_id: str = "", binding_resolution=None, repo_dir: str = "",
                 base_ref: str = "", codex_exe: str | None = None, timeout: float = 300,
                 sandbox: str = "workspace-write", parent_env=None, process_factory=None,
                 readiness_probe=None, lease_provider=None):
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 3600:
            raise ExecutorRuntimeError(self._e("timeout_invalid"))
        self._binding_resolution = binding_resolution
        self._lease_provider = lease_provider
        if binding_resolution is not None:
            self._accept_binding(binding_resolution)
            model_id = binding_resolution.model_id
        self._model_id = self._validate_model(model_id)
        self._repo_dir = repo_dir
        self._base_ref = base_ref
        self._codex_exe = codex_exe
        self._timeout = float(timeout)
        self._sandbox = sandbox
        self._parent_env = os.environ if parent_env is None else parent_env
        self._process_factory = process_factory or subprocess.Popen
        self._readiness_probe = readiness_probe or type(self).default_readiness_probe
        self._validate_options()

    def _validate_model(self, model: str) -> str:
        return validate_codex_model(model)

    def _accept_binding(self, resolution) -> None:
        """Native CLIs run on the Owner's own managed login, never on a relayed API key."""
        if resolution.executor_id != self.KIND or resolution.auth_method != "external_cli_session" or resolution.relay_required:
            raise ExecutorRuntimeError(self._e("requires_managed_session_binding"))
        if resolution.external_session_status not in {"available", "executor_managed"}:
            raise ExecutorRuntimeError(self._e("session_unavailable"))

    def _require_ready(self, cli) -> None:
        if self._readiness_probe(cli) != "managed_login_ready":
            raise ExecutorRuntimeError(self._e("managed_login_unavailable"))

    def prepare_worktree_once(self, task_id, root_path, event_callback=None):
        cli = self._resolve_cli()
        self._require_ready(cli)
        if not re.fullmatch(r"[0-9a-f]{40}", self._base_ref):
            raise ExecutorRuntimeError(self._e("requires_exact_base_sha"))
        worktree, base = prepare_linked_worktree(task_id, Path(root_path), event_callback,
            repo_dir_value=self._repo_dir, base_ref=self._base_ref)
        prepared = CodexPreparedContext(worktree, base, f"exec-{task_id}", cli, self.KIND)
        _emit(event_callback, task_id, {"type": "WORKSPACE_READY", "title": f"{self.LABEL} workspace ready",
            "description": "Isolated workspace bound to approved base", "metadata": {
                "workspace": str(worktree), "base_sha": base, "executor_kind": self.KIND,
                "execution_id": prepared.execution_id, "model": self._model_id}})
        return prepared

    def reconstruct_prepared_context(self, *, worktree_path, base_sha, execution_id, **_):
        worktree = Path(worktree_path).resolve()
        self._verify_workspace(worktree, base_sha)
        return CodexPreparedContext(worktree, base_sha, execution_id, self._resolve_cli(), self.KIND)

    def _verify_workspace(self, worktree, expected):
        self._verify_head(worktree, expected)
        source = Path(self._repo_dir).resolve()
        worktree = worktree.resolve()
        if expected != self._base_ref or worktree == source or source in worktree.parents:
            raise ExecutorRuntimeError(self._e("worktree_identity_invalid"))
        def common_directory(root):
            result = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=root,
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=10, check=False)
            if result.returncode or not result.stdout.strip() or len(result.stdout) > 4096:
                raise ExecutorRuntimeError(self._e("worktree_identity_invalid"))
            return (root / result.stdout.strip()).resolve()
        if not (worktree / ".git").is_file() or common_directory(source) != common_directory(worktree):
            raise ExecutorRuntimeError(self._e("worktree_identity_invalid"))

    def _verify_head(self, worktree, expected):
        if not re.fullmatch(r"[0-9a-f]{40}", expected) or not worktree.is_dir():
            raise ExecutorRuntimeError(self._e("worktree_identity_invalid"))
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=worktree, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=10, check=False)
        if result.returncode or result.stdout.strip() != expected:
            raise ExecutorRuntimeError(self._e("worktree_head_mismatch"))

    def execute(self, task_id, store, *, workspace_root="", event_callback=None):
        from .opencode_executor import RoleContext
        if not workspace_root:
            raise ExecutorRuntimeError("workspace_root_required")
        prepared = self.prepare_worktree_once(task_id, Path(workspace_root), event_callback)
        return self.execute_role_prepared(prepared, store,
            role_context=RoleContext("executor", task_id, prepared.worktree), event_callback=event_callback)

    def execute_role_prepared(self, prepared, store, *, role_context, event_callback=None):
        if role_context.role != "executor":
            raise ExecutorRuntimeError(self._e("single_mode_only"))
        if getattr(prepared, "executor_kind", "") != self.KIND or Path(role_context.workspace).resolve() != prepared.worktree.resolve():
            raise ExecutorRuntimeError(self._e("prepared_identity_mismatch"))
        task_id = role_context.task_id
        if prepared.execution_id != f"exec-{task_id}" or prepared.worktree.name != task_id:
            raise ExecutorRuntimeError(self._e("task_identity_mismatch"))
        self._verify_workspace(prepared.worktree, prepared.base_sha)
        if any((prepared.worktree / relative).exists() for relative in self.PROJECT_CONFIG):
            # Do not inspect config that can install hooks or replace provider authority.
            raise ExecutorRuntimeError(self._e("project_configuration_unapproved"))
        task = store.get_task(task_id)
        title = getattr(task, "title", "")
        if not isinstance(title, str) or not title.strip() or len(title.encode()) > 64 * 1024:
            raise ExecutorRuntimeError(self._e("task_instruction_invalid"))
        prompt = ("Perform only this admitted task inside this isolated workspace. Preserve existing work. "
                  "Do not commit, push, merge, access credentials, install dependencies, or bypass policy. "
                  "Report changes and checks truthfully; CLI success is not functional acceptance.\n\n" + title)
        from .context_builder import executor_context
        context = executor_context(store, task_id=task_id, workspace=prepared.worktree,
                                   expected_head=prepared.base_sha)
        prompt += context
        if context:
            context_blob = context.rsplit("\n", 1)[-1].encode()
            _emit(event_callback, task_id, {"type":"EXECUTOR_RUNNING", "title":"Durable context rebuilt",
                "description":"Non-authoritative projection from current TaskStore and Git",
                "metadata":{"context_packet_digest":hashlib.sha256(context_blob).hexdigest(),
                            "context_packet_bytes":len(context_blob), "measured_context_packet_tokens":len(context.encode("utf-8")), "base_sha":prepared.base_sha}})
        def progress(item):
            _emit(event_callback, task_id, {"type": "EXECUTOR_PROGRESS", "title": self.LABEL,
                "description": public_text(item.get("text") or item.get("command") or f"{self.LABEL} activity"),
                "metadata": {"executor_kind": self.KIND, "event": item}})
        parser = self._parser(progress)
        code = None
        def persist_unknown_usage():
            identity = hashlib.sha256((prepared.execution_id + ":" + (parser.turn.thread_id or "no-thread")).encode()).hexdigest()
            _persist_usage_observations(store, task_id, [{
                "observation_id": f"usage-{self.KIND}-" + identity, "execution_id": prepared.execution_id,
                "role": "executor", "model_id": self._model_id, "provider_id": self.PROVIDER_ID,
                "source_kind": "assistant_message", "source_id": f"{self.KIND}-turn-" + identity,
                # CLI tokens do not provide reasoning/cache-write or dollar cost.
                "status": "UNKNOWN",
            }])
        try:
            code = self._stream(prepared, prompt, parser)
            turn = parser.finish()
            if code != 0 or turn.failed:
                raise CodexProtocolError(turn.failure_classification or self._e("process_failed"))
            if turn.tool_launch_failed:
                # The model may finish its turn after a Windows sandbox helper
                # failure. Patch hygiene cannot convert that into a successful
                # executor result or an eligible READY_FOR_REVIEW Task.
                raise CodexProtocolError(self._e("tool_launch_failed"))
            self._verify_workspace(prepared.worktree, prepared.base_sha)
        except (ExecutorRuntimeError, OSError) as exc:
            persist_unknown_usage()
            classification = str(exc) if isinstance(exc, ExecutorRuntimeError) else self._e("process_start_failed")
            return ExecutorResult(False, -1, "", "", "", error=classification,
                workspace=str(prepared.worktree), execution_id=prepared.execution_id,
                process_exit_code=code, failure_classification=classification)
        persist_unknown_usage()
        _emit(event_callback, task_id, {"type": "EXECUTOR_COMPLETED", "title": f"{self.LABEL} response",
            "description": public_text(turn.final_text), "metadata": {"executor_kind": self.KIND,
                "final_text": turn.final_text, "usage_status": "observed_tokens" if turn.usage is not None else "unknown",
                "token_usage": turn.usage, "cost_status": "unknown", "process_exit_code": code,
                **({"models": turn.models} if turn.models else {}),
                **({"rate_limits": turn.rate_limits} if turn.rate_limits else {}),
                **({"cli_reported_cost_usd": turn.reported_cost_usd}
                   if turn.reported_cost_usd is not None else {})}})
        exit_code, summary, digest = LocalValidationRunner().run(task_id=task_id, command_id="git_diff_check", cwd=str(prepared.worktree))
        changed_files = [f for f in _collect_final_product_files(prepared.worktree)
                         if not _is_task_temp(f["path"])]
        # git diff --check returns zero for an unchanged worktree. That proves
        # only patch hygiene, not that an implementation task produced work.
        # An empty result must never be promoted to READY_FOR_REVIEW.
        no_product_changes = exit_code == 0 and not changed_files
        return ExecutorResult(exit_code == 0 and not no_product_changes, exit_code,
            "git_diff_check", digest,
            "No product changes were produced; patch hygiene is not functional acceptance."
            if no_product_changes else summary,
            changed_files=changed_files, workspace=str(prepared.worktree),
            execution_id=prepared.execution_id, process_exit_code=code,
            failure_classification=(self._e("no_product_changes") if no_product_changes
                                    else ("" if exit_code == 0 else "patch_hygiene_failed")))

    def _stream(self, prepared, prompt, parser):
        from .functional_validation import _WindowsJob, _terminate
        environment = _task_temp_env(prepared.worktree, self._child_env())
        job = _WindowsJob() if os.name == "nt" else None
        try:
            proc = self._process_factory(self._argv(prepared),
                cwd=str(prepared.worktree), env=environment, stdin=subprocess.PIPE,
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
                    raise CodexProtocolError(self._e("timeout"))
                try:
                    channel, chunk = packets.get(timeout=min(remaining, 0.1))
                except queue.Empty:
                    continue
                if channel == "reader_error":
                    raise CodexProtocolError(self._e("stream_read_failed"))
                if channel == "writer_error":
                    raise CodexProtocolError(self._e("stdin_write_failed"))
                if chunk is None:
                    finished.add(channel)
                elif channel == "out":
                    parser.feed(chunk)
                else:
                    stderr_bytes += len(chunk)
                    if stderr_bytes > 256 * 1024:
                        raise CodexProtocolError(self._e("stderr_limit_exceeded"))
            try:
                return proc.wait(timeout=max(0.001, deadline - time.monotonic()))
            except subprocess.TimeoutExpired as exc:
                raise CodexProtocolError(self._e("timeout")) from exc
        finally:
            stopping.set()
            # Close only this owned process tree, including surviving tool children.
            _terminate(proc, job)
            for pipe in (proc.stdin, proc.stdout, proc.stderr):
                pipe.close()
            for reader in readers:
                reader.join(timeout=1)
