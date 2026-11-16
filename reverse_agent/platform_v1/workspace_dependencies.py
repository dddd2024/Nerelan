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
  ``--no-audit``, ``--no-fund``) and recorded as its own evidence row; it runs
  under the functional checks' owned process-tree runner, so the timeout ends
  every descendant, not only the direct child;
* every install starts from an empty ``node_modules`` (removed without
  following links), so functional validation never trusts a dependency tree
  the agent could have modified;
* the target directory, its lockfile and ``package.json`` must be real paths
  inside the workspace (no symlink or junction component), and a project
  ``.npmrc`` is refused exactly as the functional npm check refuses it;
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
import stat
import subprocess
import tempfile
from typing import Any, Callable, Mapping, Sequence

from .run_store import TaskStoreError

DEPENDENCY_CATEGORY = "WorkspaceDependencies"
DEPENDENCY_FAILURE_CODE = "workspace_dependencies_unavailable"
# The install's process tree could not be confirmed gone (#1557 review).
DEPENDENCY_CLEANUP_CODE = "workspace_dependencies_cleanup_unconfirmed"
# Properties of the workspace tree, not of the host: refused before installing.
PATH_UNTRUSTED_CODE = "workspace_dependency_path_untrusted"
PROJECT_CONFIG_CODE = "npm_project_config_unsupported"
LOCKFILE_INVALID_CODE = "workspace_dependency_lockfile_invalid"
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
    """What the functional check needs to install a workspace's dependencies.

    ``installed`` maps a directory to the lockfile digest the last recorded
    install used. It only annotates the check's fresh-install evidence (did
    the agent change the lockfile?); it is never a reason to reuse a tree.
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
    """Run ``npm ci`` under the functional checks' owned process-tree runner.

    A Windows kill-on-close Job object (or a POSIX process group) owns npm and
    every descendant, so the timeout bounds the whole tree and output draining
    cannot outlive it. If the tree cannot be confirmed gone the install is not
    an ordinary failure: ``workspace_dependencies_cleanup_unconfirmed``.
    """
    from .functional_validation import run_owned_process
    try:
        observed = run_owned_process(argv, cwd, env, timeout)
    except WorkspaceDependencyError:
        raise
    except TaskStoreError as exc:
        raise WorkspaceDependencyError(DEPENDENCY_CLEANUP_CODE, detail=str(exc)) from exc
    except (OSError, subprocess.SubprocessError) as exc:
        raise WorkspaceDependencyError(detail=type(exc).__name__) from exc
    observed.pop("_output_tail", None)
    return observed


def _is_link(path: Path) -> bool:
    """A symlink or any reparse point (including a Windows junction)."""
    try:
        status = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(status.st_mode)
            or bool(getattr(status, "st_file_attributes", 0)
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)))


def _trusted_target(root: Path, directory: str) -> tuple[Path, Path]:
    """The real install directory, refusing any indirection out of the workspace.

    Every component from the workspace root to the target, and the target's
    lockfile and ``package.json``, must be a real entry (no symlink or
    junction), and the resolved target must lie inside the resolved root. A
    project ``.npmrc`` between the target and the root is refused, as the
    functional npm check refuses it, without reading its contents.
    """
    try:
        real_root = Path(root).resolve(strict=True)
    except OSError as exc:
        raise WorkspaceDependencyError(PATH_UNTRUSTED_CODE, detail="root_missing") from exc
    current = real_root
    for part in (() if directory == "." else PurePosixPath(directory).parts):
        current = current / part
        if _is_link(current):
            raise WorkspaceDependencyError(PATH_UNTRUSTED_CODE, detail=f"link:{directory}")
    if not current.is_dir():
        raise WorkspaceDependencyError(PATH_UNTRUSTED_CODE, detail=f"directory_missing:{directory}")
    resolved = current.resolve(strict=True)
    if (os.path.normcase(str(resolved)) != os.path.normcase(str(current))
            or not resolved.is_relative_to(real_root)):
        raise WorkspaceDependencyError(PATH_UNTRUSTED_CODE, detail=f"outside:{directory}")
    for name in (LOCKFILE_NAME, "package.json"):
        if _is_link(current / name):
            raise WorkspaceDependencyError(PATH_UNTRUSTED_CODE, detail=f"link:{name}")
    for folder in (current, *current.parents):
        if not folder.is_relative_to(real_root):
            break
        config = folder / ".npmrc"
        if _is_link(config) or config.exists():
            raise WorkspaceDependencyError(PROJECT_CONFIG_CODE)
    return real_root, current


def _clear_node_modules(target: Path) -> None:
    """Remove ``node_modules`` so the install never reuses an agent-writable tree.

    A link or junction is removed itself, never followed; a real directory is
    removed with ``shutil.rmtree``, which does not follow nested junctions.
    """
    modules = target / "node_modules"

    def writable(function: Any, path: str, _exc: BaseException) -> None:
        os.chmod(path, stat.S_IWRITE)
        function(path)

    try:
        if _is_link(modules):
            try:
                os.unlink(modules)
            except OSError:
                os.rmdir(modules)
        elif modules.is_dir():
            shutil.rmtree(modules, onexc=writable)
        elif modules.exists():
            modules.unlink()
    except OSError as exc:
        raise WorkspaceDependencyError(detail=f"node_modules_not_removed:{type(exc).__name__}") from exc
    if _is_link(modules) or modules.exists():
        raise WorkspaceDependencyError(detail="node_modules_not_removed")


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
    previous_digests: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Install the Node dependencies a workspace needs and record the proof.

    ``lockfile_source`` selects which lockfile pins the install:

    ``"base"``
        the base commit's lockfile, restored into the workspace before the
        install. This is the workspace-preparation step: the agent's tree is
        not consulted, so it cannot influence what the host installs before
        it starts (#1503).
    ``"workspace"``
        the lockfile currently in the workspace (part of the reviewed
        artifact). This is the functional-check step, which always installs
        afresh: the tree the agent ran with is never trusted.

    Each install first removes ``node_modules`` and then runs ``npm ci``, so
    the installed tree is exactly what the lockfile pins, and lifecycle
    scripts never run. ``previous_digests`` (the last recorded install per
    directory) only annotates the evidence; it is never a reason to skip.

    Raises ``WorkspaceDependencyError``: ``workspace_dependencies_unavailable``
    for a failed install (a blocked host fault, not a model failure),
    ``workspace_dependencies_cleanup_unconfirmed`` when the install's process
    tree could not be confirmed gone, and the path/config codes when the
    workspace tree is not trusted for installation.
    """
    if not plan or not plan.directories:
        return {"status": "NOT_REQUIRED", "directories": []}
    if lockfile_source not in {"base", "workspace"}:
        raise WorkspaceDependencyError(detail="lockfile_source_invalid")
    previous = dict(previous_digests or {})
    root = Path(worktree)
    argv = _npm_argv()
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="nerelan-workspace-deps-") as temporary:
        config_dir = Path(temporary) / "npm-config"
        config_dir.mkdir()
        env = _install_environment(root, config_dir)
        for directory in plan.directories:
            real_root, target = _trusted_target(root, directory)
            lockfile = target / LOCKFILE_NAME
            if lockfile_source == "base":
                restored = _restore_base_lockfile(real_root, plan.base_commit, directory, target)
                if restored is None:
                    raise WorkspaceDependencyError(detail="lockfile_missing")
            elif not lockfile.is_file():
                # Nothing pins the dependency set; npm ci cannot run. In the
                # workspace this is the agent's tree, not a host outage.
                raise WorkspaceDependencyError(LOCKFILE_INVALID_CODE, detail="lockfile_missing")
            if lockfile.stat().st_size > MAX_LOCKFILE_BYTES:
                raise WorkspaceDependencyError(LOCKFILE_INVALID_CODE, detail="lockfile_too_large")
            package = target / "package.json"
            if package.is_file() and package.stat().st_size > MAX_PACKAGE_BYTES:
                raise WorkspaceDependencyError(LOCKFILE_INVALID_CODE, detail="package_too_large")
            digest = _sha256_bytes(lockfile.read_bytes())
            _clear_node_modules(target)
            command = [*argv, "--ignore-scripts", "--no-audit", "--no-fund"]
            entry = {
                "directory": directory,
                "lockfile_digest": digest,
                "lockfile_source": lockfile_source,
                "previous_lockfile_digest": previous.get(directory, ""),
                "fresh_install": True,
            }
            try:
                observed = (runner(command, target, env, timeout) if runner is not None
                            else _run_install(command, target, env, timeout))
            except WorkspaceDependencyError as exc:
                if exc.code != DEPENDENCY_CLEANUP_CODE:
                    raise
                entry.update(exit_code=None, timed_out=True, cleanup="unknown")
                results.append(entry)
                _record(store, task_id, {"status": "FAILED", "directories": results,
                                         "failure": DEPENDENCY_CLEANUP_CODE,
                                         "failed_directory": directory}, lease=lease)
                raise
            entry.update(
                exit_code=observed.get("exit_code"),
                timed_out=bool(observed.get("timed_out")),
                duration_ms=observed.get("duration_ms"),
                output_digest=observed.get("output_digest", ""),
                output_bytes=observed.get("output_bytes", 0),
                cleanup=observed.get("cleanup", "not_reported"),
            )
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


def _restore_base_lockfile(root: Path, base_commit: str, directory: str,
                           target: Path) -> bytes | None:
    """Put the base commit's lockfile back into the (already trusted) target.

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
    (target / LOCKFILE_NAME).write_bytes(payload)
    return payload


def dependency_evidence(task: Any) -> list[Mapping[str, Any]]:
    """Read-only projection of the recorded dependency installs."""
    rows = [row for row in getattr(task, "evidence_refs", ())
            if row.get("category") == DEPENDENCY_CATEGORY]
    return rows


def installed_lockfile_digests(task: Any) -> dict[str, str]:
    """The lockfile digest each directory was last installed from.

    The functional check records this next to its own fresh install, so the
    evidence shows whether the agent changed the lockfile (#1503). It is not
    proof that the installed tree is intact and is never used to skip one.
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
