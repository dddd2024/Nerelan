"""Host-owned provisioning of Node dependencies inside a task workspace.

A task workspace is a fresh linked Git worktree: it carries the repository
content and nothing else. ``node_modules`` is not tracked, so an ``npm_test``
functional check inside a fresh workspace fails with "vitest is not
recognized" before any product code is even read (#1503).

This module is the single place where that gap is closed:

* the *plan* is derived from the frozen functional contract, so a plan without
  Node checks never runs npm at all;
* the install runs **from the base commit's lockfile**, not from the agent's
  tree, so the agent cannot influence what the host installs before it starts;
* the install is bounded (timeout, sanitized environment, ``--ignore-scripts``,
  ``--no-audit``, ``--no-fund``) and recorded as its own evidence row;
* a failed install is a **host fault** (``workspace_dependencies_unavailable``),
  never a model failure, so it does not spend ``max_retries``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import time
from typing import Any, Callable, Mapping, Sequence

from .run_store import TaskStoreError

DEPENDENCY_CATEGORY = "WorkspaceDependencies"
DEPENDENCY_FAILURE_CODE = "workspace_dependencies_unavailable"
DEPENDENCY_LABEL = "workspace_dependencies"
LOCKFILE_NAME = "package-lock.json"
# npm's own default ceiling is generous; the host bounds it more tightly so a
# hung install cannot outlive the task's own budget.
INSTALL_TIMEOUT_SECONDS = 600
MAX_LOCKFILE_BYTES = 32 * 1024 * 1024
MAX_PACKAGE_BYTES = 4 * 1024 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
# The frozen contract already constrains working_directory to a relative,
# forward-slash path without "." or ".." segments; this guards the host side.
_RELATIVE_DIR = re.compile(r"[A-Za-z0-9_./-]{1,240}\Z")


class WorkspaceDependencyError(TaskStoreError):
    """A host-side dependency install failed; the step is blocked, not failed."""

    def __init__(self, code: str = DEPENDENCY_FAILURE_CODE, detail: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.code


@dataclass(frozen=True, slots=True)
class DependencyPlan:
    """The directories of one workspace that need installed Node dependencies.

    ``directories`` are repository-relative working directories (the same
    shape the frozen contract uses). ``lockfiles`` maps each directory to the
    digest of the lockfile observed at the base commit.
    """

    directories: tuple[str, ...] = ()
    lockfiles: Mapping[str, str] = field(default_factory=dict)
    base_commit: str = ""

    def __bool__(self) -> bool:
        return bool(self.directories)


@dataclass(frozen=True, slots=True)
class DependencyContext:
    """What the functional check needs to keep a workspace's install current.

    ``installed`` maps a directory to the lockfile digest the last install
    used, so the check can tell whether the agent changed the lockfile and
    the installed tree has to be refreshed.
    """

    store: Any = None
    task_id: str = ""
    lease: Any = None
    installed: Mapping[str, str] = field(default_factory=dict)
    base_commit: str = ""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def normalize_dependency_directory(value: Any) -> str:
    """Normalize a contract working_directory into a safe relative path."""
    if not isinstance(value, str) or not value or len(value) > 240:
        raise TaskStoreError("workspace_dependency_directory_invalid")
    if value == ".":
        return "."
    if not _RELATIVE_DIR.fullmatch(value) or "\\" in value:
        raise TaskStoreError("workspace_dependency_directory_invalid")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise TaskStoreError("workspace_dependency_directory_invalid")
    return str(PurePosixPath(*parts))


def _git_blob(worktree: Path, base_commit: str, relative: str) -> bytes | None:
    """Read one path at the base commit without touching the working tree."""
    if not base_commit:
        return None
    try:
        completed = subprocess.run(
            ["git", "-C", str(worktree), "show", f"{base_commit}:{relative}"],
            stdin=subprocess.DEVNULL, capture_output=True, timeout=30, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode or len(completed.stdout) > MAX_LOCKFILE_BYTES:
        return None
    return completed.stdout


def dependency_directories(checks: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    """The working directories of a frozen contract that need Node dependencies.

    An ``npm_test`` profile always needs them. A ``python_pytest`` profile only
    needs them when its working directory carries a ``package-lock.json``,
    which is decided by the caller against the workspace tree.
    """
    directories: list[str] = []
    for check in checks or ():
        if not isinstance(check, Mapping):
            continue
        profile = check.get("profile_id")
        directory = normalize_dependency_directory(check.get("working_directory", "."))
        if profile == "npm_test" or profile == "node_dependencies":
            if directory not in directories:
                directories.append(directory)
    return tuple(directories)


def dependency_plan_from_checks(
    checks: Sequence[Mapping[str, Any]],
    *,
    base_commit: str = "",
) -> DependencyPlan:
    """The directories a frozen contract needs installed, and nothing else.

    This is the plan the workspace preparation step uses: it depends only on
    the contract Goal launch froze, so a plan without Node checks never runs
    npm and the agent cannot widen the install set.
    """
    return DependencyPlan(directories=dependency_directories(checks),
                          lockfiles={}, base_commit=base_commit)


def build_dependency_plan(
    checks: Sequence[Mapping[str, Any]],
    worktree: Path,
    *,
    base_commit: str = "",
) -> DependencyPlan:
    """Resolve the directories and lockfile digests a workspace needs.

    A directory that carries a lockfile at the base commit is included even
    when no check profile names it, so a repository that ships a Node
    workspace always gets its dependencies installed.
    """
    directories = list(dependency_directories(checks))
    for check in checks or ():
        if not isinstance(check, Mapping):
            continue
        directory = normalize_dependency_directory(check.get("working_directory", "."))
        if directory in directories:
            continue
        if (worktree.joinpath(*PurePosixPath(directory).parts) / LOCKFILE_NAME).is_file():
            directories.append(directory)
    lockfiles: dict[str, str] = {}
    for directory in directories:
        relative = LOCKFILE_NAME if directory == "." else f"{directory}/{LOCKFILE_NAME}"
        payload = _git_blob(worktree, base_commit, relative)
        if payload is None:
            payload_path = worktree.joinpath(*PurePosixPath(directory).parts) / LOCKFILE_NAME
            if payload_path.is_file() and payload_path.stat().st_size <= MAX_LOCKFILE_BYTES:
                payload = payload_path.read_bytes()
        if payload is not None:
            lockfiles[directory] = _sha256_bytes(payload)
    return DependencyPlan(directories=tuple(directories), lockfiles=lockfiles,
                          base_commit=base_commit)


def _npm_argv() -> list[str]:
    """Resolve the npm CLI the same way the functional oracle resolves it."""
    npm = shutil.which("npm")
    if not npm:
        raise WorkspaceDependencyError()
    npm_path = Path(npm).resolve()
    candidates = [npm_path] if npm_path.suffix == ".js" else [
        npm_path.parent / "node_modules/npm/bin/npm-cli.js"]
    cli = next((path for path in candidates if path.is_file()), None)
    if cli is None:
        raise WorkspaceDependencyError()
    node = shutil.which("node")
    if not node:
        raise WorkspaceDependencyError()
    return [str(Path(node).resolve()), str(cli.resolve()), "ci"]


def _install_environment(root: Path, config_dir: Path) -> dict[str, str]:
    """A sanitized child environment; no credentials, no Owner npm config."""
    names = ("PATH", "SystemRoot", "WINDIR", "TEMP", "TMP", "TMPDIR", "HOME", "USERPROFILE",
             "LOCALAPPDATA", "APPDATA", "PROGRAMDATA", "COMSPEC", "PATHEXT", "LANG", "LC_ALL")
    env = {key: os.environ[key] for key in names if key in os.environ}
    user_config = config_dir / "user.npmrc"
    global_config = config_dir / "global.npmrc"
    for path in (user_config, global_config):
        path.write_text("", encoding="utf-8")
    env.update(CI="true", NPM_CONFIG_OFFLINE="false", NPM_CONFIG_AUDIT="false",
               NPM_CONFIG_FUND="false", NPM_CONFIG_UPDATE_NOTIFIER="false",
               NPM_CONFIG_IGNORE_SCRIPTS="true",
               NPM_CONFIG_USERCONFIG=str(user_config),
               NPM_CONFIG_GLOBALCONFIG=str(global_config),
               NPM_CONFIG_CACHE=str(config_dir / "cache"))
    env.pop("PYTHONPATH", None)
    env.pop("PYTEST_ADDOPTS", None)
    return env


def _run_install(argv: list[str], cwd: Path, env: dict[str, str],
                 timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            argv, cwd=str(cwd), stdin=subprocess.DEVNULL, capture_output=True,
            timeout=timeout, check=False, env=env,
        )
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "timed_out": True, "duration_ms": (time.monotonic() - started) * 1000,
                "output_digest": "", "output_bytes": 0}
    except (OSError, subprocess.SubprocessError) as exc:
        raise WorkspaceDependencyError(detail=type(exc).__name__) from exc
    output = completed.stdout or b""
    return {"exit_code": completed.returncode, "timed_out": False,
            "duration_ms": round((time.monotonic() - started) * 1000),
            "output_digest": _sha256_bytes(output), "output_bytes": len(output)}


def _record(store: Any, task_id: str, document: Mapping[str, Any], *, lease: Any = None) -> None:
    detail = json.dumps(document, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    identity = hashlib.sha256(detail.encode("utf-8")).hexdigest()
    fields = dict(category=DEPENDENCY_CATEGORY, label=DEPENDENCY_LABEL, value=identity,
                  status=document.get("status", "UNKNOWN"), detail=detail,
                  raw_json_digest=identity)
    if lease is None:
        store.add_evidence(task_id, **fields)
    else:
        store._fenced_add_evidence(lease.run_id, task_id, **fields,
                                   owner=lease.owner, epoch=lease.epoch)


def provision_workspace_dependencies(
    store: Any,
    task_id: str,
    plan: DependencyPlan,
    worktree: Path,
    *,
    lease: Any = None,
    runner: Callable[..., dict[str, Any]] | None = None,
    timeout: int = INSTALL_TIMEOUT_SECONDS,
    lockfile_source: str = "base",
) -> dict[str, Any]:
    """Install the Node dependencies a workspace needs and record the proof.

    ``lockfile_source`` selects which lockfile pins the install:

    ``"base"``
        the base commit's lockfile, restored into the workspace before the
        install. This is the workspace-preparation step: the agent's tree is
        not consulted, so it cannot influence what the host installs before
        it starts (#1503).
    ``"workspace"``
        the lockfile currently in the workspace. This is the functional-check
        step: when the agent changed ``package-lock.json``, the check
        re-provisions from the agent's own lockfile and records that it did.

    ``npm ci`` is used, so the installed tree is exactly what the lockfile
    pins and lifecycle scripts never run.

    Raises ``WorkspaceDependencyError`` when the install fails: the caller
    treats that as a blocked host fault, not a model failure.
    """
    if not plan or not plan.directories:
        return {"status": "NOT_REQUIRED", "directories": []}
    if lockfile_source not in {"base", "workspace"}:
        raise WorkspaceDependencyError(detail="lockfile_source_invalid")
    root = Path(worktree)
    argv = _npm_argv()
    results: list[dict[str, Any]] = []
    import tempfile
    with tempfile.TemporaryDirectory(prefix="nerelan-workspace-deps-") as temporary:
        config_dir = Path(temporary) / "npm-config"
        config_dir.mkdir()
        env = _install_environment(root, config_dir)
        for directory in plan.directories:
            target = root.joinpath(*PurePosixPath(directory).parts)
            if not target.is_dir() or not target.is_relative_to(root):
                raise WorkspaceDependencyError(detail="directory_missing")
            lockfile = target / LOCKFILE_NAME
            if lockfile_source == "base":
                restored = _restore_base_lockfile(root, plan.base_commit, directory)
                if restored is None:
                    raise WorkspaceDependencyError(detail="lockfile_missing")
            elif not lockfile.is_file():
                # Nothing pins the dependency set; npm ci cannot run and the
                # check would fail with an opaque "not recognized" message.
                raise WorkspaceDependencyError(detail="lockfile_missing")
            if lockfile.stat().st_size > MAX_LOCKFILE_BYTES:
                raise WorkspaceDependencyError(detail="lockfile_too_large")
            package = target / "package.json"
            if package.is_file() and package.stat().st_size > MAX_PACKAGE_BYTES:
                raise WorkspaceDependencyError(detail="package_too_large")
            command = [*argv, "--ignore-scripts", "--no-audit", "--no-fund"]
            observed = (runner(command, target, env, timeout) if runner is not None
                        else _run_install(command, target, env, timeout))
            entry = {
                "directory": directory,
                "lockfile_digest": _sha256_bytes(lockfile.read_bytes()),
                "lockfile_source": lockfile_source,
                "exit_code": observed.get("exit_code"),
                "timed_out": bool(observed.get("timed_out")),
                "duration_ms": observed.get("duration_ms"),
                "output_digest": observed.get("output_digest", ""),
                "output_bytes": observed.get("output_bytes", 0),
            }
            results.append(entry)
            if entry["timed_out"] or entry["exit_code"] != 0:
                document = {"status": "FAILED", "directories": results,
                            "failure": DEPENDENCY_FAILURE_CODE,
                            "failed_directory": directory}
                _record(store, task_id, document, lease=lease)
                raise WorkspaceDependencyError(detail=f"install_failed:{directory}")
    document = {"status": "INSTALLED", "directories": results, "failure": ""}
    _record(store, task_id, document, lease=lease)
    return document


def _restore_base_lockfile(root: Path, base_commit: str, directory: str) -> bytes | None:
    """Put the base commit's lockfile back into the workspace.

    The workspace preparation step installs from the base commit's lockfile,
    never from whatever the agent's tree carries, so the dependency set the
    host installs is the one the repository was reviewed against.
    """
    if not base_commit:
        return None
    relative = LOCKFILE_NAME if directory == "." else f"{directory}/{LOCKFILE_NAME}"
    payload = _git_blob(root, base_commit, relative)
    if payload is None:
        return None
    target = root.joinpath(*PurePosixPath(directory).parts) / LOCKFILE_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return payload


def dependency_evidence(task: Any) -> list[Mapping[str, Any]]:
    """Read-only projection of the recorded dependency installs."""
    rows = [row for row in getattr(task, "evidence_refs", ())
            if row.get("category") == DEPENDENCY_CATEGORY]
    return rows


def installed_lockfile_digests(task: Any) -> dict[str, str]:
    """The lockfile digest each directory was last installed from.

    The functional check compares this with the workspace's current lockfile
    to learn whether the agent changed it and the installed tree has to be
    refreshed (#1503).
    """
    digests: dict[str, str] = {}
    for row in dependency_evidence(task):
        try:
            document = json.loads(row.get("detail", "{}"))
        except (ValueError, TypeError):
            continue
        if not isinstance(document, Mapping) or document.get("status") != "INSTALLED":
            continue
        for entry in document.get("directories", ()):
            if not isinstance(entry, Mapping):
                continue
            directory = entry.get("directory")
            digest = entry.get("lockfile_digest")
            if isinstance(directory, str) and isinstance(digest, str) and digest:
                digests[directory] = digest
    return digests


def task_dependency_plan(store: Any, task_id: str) -> DependencyPlan:
    """The Node dependency plan a task's frozen contract requires.

    A plan without Node checks yields an empty plan, and the workspace
    preparation step then never runs npm (#1503). The plan is derived from
    the contract Goal launch froze, so the agent cannot widen it.
    """
    from .functional_validation import load_contract
    try:
        contract = load_contract(store.get_task(task_id))
    except (TaskStoreError, OSError, ValueError, KeyError, TypeError, AttributeError):
        return DependencyPlan()
    if not contract:
        return DependencyPlan()
    try:
        return dependency_plan_from_checks(contract.get("checks") or (),
                                           base_commit=contract.get("base_commit") or "")
    except TaskStoreError:
        return DependencyPlan()


def prepare_workspace_with_dependencies(
    executor: Any,
    task_id: str,
    root_path: Any,
    event_callback: Any,
    *,
    plan: DependencyPlan,
    store: Any,
) -> Any:
    """Prepare the task workspace and provision its Node dependencies.

    The dependency arguments are only passed when the plan actually needs an
    install, so an executor that does not implement the optional host-owned
    provisioning step keeps working unchanged for every plan without Node
    checks (#1503).
    """
    if plan and plan.directories:
        return executor.prepare_worktree_once(
            task_id, root_path, event_callback,
            dependencies=plan, dependency_store=store,
        )
    return executor.prepare_worktree_once(task_id, root_path, event_callback)
