"""Owner-reviewed fixed checks and exact Git artifact proof in the existing TaskStore.

The catalog is host code, not a browser command runner. Contracts/results live in
the existing evidence table; Git's private index supplies immutable tree identity.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
from typing import Any, Mapping, Sequence

from reverse_agent.executor_neutral.core import _snapshot_workspace
from .repository_workspace import resolve_repository_workspace
from .run_store import TaskStoreError

FUNCTIONAL_COMMAND_ID = "approved_functional_checks"
CONTRACT_CATEGORY = "FunctionalContract"
RESULT_CATEGORY = "FunctionalValidation"
CATALOG_VERSION = 1
OUTPUT_LIMIT = 4096
_SHA40 = re.compile(r"[0-9a-f]{40}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_CATALOG = {
    "python_pytest": {"argv": ["@python", "-m", "pytest", "-q", "-p", "no:cacheprovider"], "timeout_seconds": 600},
    "npm_test": {"argv": ["@node", "@npm_cli", "test"], "timeout_seconds": 600},
}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def catalog_digest() -> str:
    return digest({"version": CATALOG_VERSION, "profiles": _CATALOG, "output_limit": OUTPUT_LIMIT,
                   "reports": {"python_pytest": "junit", "npm_test": {"node --test": "tap", "vitest run": "junit"}}})


def normalize_checks(raw: Any) -> tuple[dict[str, str], ...]:
    if not isinstance(raw, (list, tuple)) or len(raw) > 8:
        raise TaskStoreError("functional_checks_invalid")
    checks: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in raw:
        if not isinstance(item, Mapping) or set(item) - {"profile_id", "working_directory"}:
            raise TaskStoreError("functional_check_fields_invalid")
        profile = item.get("profile_id")
        directory = item.get("working_directory", ".")
        if not isinstance(profile, str) or profile not in _CATALOG:
            raise TaskStoreError("functional_profile_unapproved")
        if (not isinstance(directory, str) or not directory or len(directory) > 240
                or "\\" in directory or ":" in directory or "\x00" in directory
                or directory.startswith("/") or directory != directory.strip()
                or any(part in {"", ".."} for part in directory.split("/"))
                or (directory != "." and "." in directory.split("/"))):
            raise TaskStoreError("functional_directory_invalid")
        identity = (profile, directory)
        if identity in seen:
            raise TaskStoreError("functional_check_duplicate")
        seen.add(identity)
        checks.append({"profile_id": profile, "working_directory": directory})
    return tuple(checks)


def git_output(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], stdin=subprocess.DEVNULL,
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                            timeout=15, check=False)
    if result.returncode or len(result.stdout) > 16384:
        raise TaskStoreError("functional_git_observation_failed")
    return result.stdout.strip()


def repository_base(repository: str) -> str:
    binding = resolve_repository_workspace(repository)
    head = git_output(binding.repo_dir, "rev-parse", "HEAD")
    if not _SHA40.fullmatch(head):
        raise TaskStoreError("functional_base_invalid")
    return head


def prepared_base(task: Any, workspace: str) -> str:
    """Use the executor's persisted workspace-preparation observation, not HEAD later."""
    identities = set()
    for event in task.events:
        if event.get("type") != "WORKSPACE_READY":
            continue
        metadata = event.get("metadata", {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except ValueError:
                continue
        if not isinstance(metadata, Mapping):
            continue
        observed_workspace = metadata.get("workspace")
        base = metadata.get("base_sha")
        if (metadata.get("execution_id") == task.execution_id
                and isinstance(observed_workspace, str) and isinstance(base, str)
                and _SHA40.fullmatch(base) and Path(observed_workspace).resolve() == Path(workspace).resolve()):
            identities.add(base)
    return next(iter(identities)) if len(identities) == 1 else ""


def freeze_contract(store: Any, task: Any, *, goal: Any, plan_task: Any, base_commit: str) -> dict[str, Any] | None:
    checks = normalize_checks(plan_task.validation_checks)
    if not checks:
        return None
    if not _SHA40.fullmatch(base_commit) or not _SHA256.fullmatch(goal.artifact_digest):
        raise TaskStoreError("functional_contract_identity_invalid")
    contract = {"version": CATALOG_VERSION, "catalog_digest": catalog_digest(),
                "task_id": task.id, "repository": task.repository, "base_commit": base_commit,
                "goal_id": goal.id, "goal_revision": goal.revision, "goal_artifact_digest": goal.artifact_digest,
                "plan_task_id": plan_task.id, "requires_implementation": plan_task.capability == "execute_task",
                "checks": list(checks)}
    previous = load_contract(store.get_task(task.id))
    if previous is not None:
        if previous != contract:
            raise TaskStoreError("functional_contract_conflict")
        return previous
    identity = digest(contract)
    store.add_evidence(task.id, category=CONTRACT_CATEGORY, label="approved_goal_checks",
                       value=identity, status="APPROVED", detail=canonical(contract), raw_json_digest=identity)
    return contract


def load_contract(task: Any) -> dict[str, Any] | None:
    rows = [row for row in task.evidence_refs if row.get("category") == CONTRACT_CATEGORY]
    if not rows:
        return None
    if len(rows) != 1:
        raise TaskStoreError("functional_contract_ambiguous")
    row = rows[0]
    try:
        contract = json.loads(row["detail"])
        fields = {"version", "catalog_digest", "task_id", "repository", "base_commit", "goal_id",
                  "goal_revision", "goal_artifact_digest", "plan_task_id", "requires_implementation", "checks"}
        if (not isinstance(contract, dict) or set(contract) != fields or row["status"] != "APPROVED"
                or row["value"] != digest(contract) or row["raw_json_digest"] != digest(contract)
                or contract["version"] != CATALOG_VERSION or contract["catalog_digest"] != catalog_digest()
                or contract["task_id"] != task.id or contract["repository"] != task.repository
                or not isinstance(contract["base_commit"], str) or not _SHA40.fullmatch(contract["base_commit"])
                or not isinstance(contract["goal_artifact_digest"], str) or not _SHA256.fullmatch(contract["goal_artifact_digest"])
                or not isinstance(contract["requires_implementation"], bool)
                or type(contract["goal_revision"]) is not int or contract["goal_revision"] < 1
                or any(not isinstance(contract[key], str) or not contract[key] for key in ("goal_id", "plan_task_id"))
                or list(normalize_checks(contract["checks"])) != contract["checks"] or not contract["checks"]):
            raise ValueError
    except (ValueError, TypeError, KeyError, TaskStoreError) as exc:
        raise TaskStoreError("functional_contract_invalid_or_stale") from exc
    return contract


def _working_directory(root: Path, relative: str) -> Path:
    candidate = root.joinpath(*PurePosixPath(relative).parts).resolve(strict=True)
    if not candidate.is_dir() or not candidate.is_relative_to(root):
        raise TaskStoreError("functional_directory_outside_worktree")
    return candidate


def _resolved_argv(profile: str) -> list[str]:
    if profile == "python_pytest":
        return [str(Path(sys.executable).resolve()), *_CATALOG[profile]["argv"][1:]]
    node, npm = shutil.which("node"), shutil.which("npm")
    if not node or not npm:
        raise TaskStoreError("functional_runtime_unavailable")
    npm_path = Path(npm).resolve()
    candidates = [npm_path] if npm_path.suffix == ".js" else [npm_path.parent / "node_modules/npm/bin/npm-cli.js"]
    cli = next((path for path in candidates if path.is_file()), None)
    if cli is None:
        raise TaskStoreError("functional_npm_cli_unavailable")
    return [str(Path(node).resolve()), str(cli.resolve()), "test"]


def _environment(root: Path) -> dict[str, str]:
    # Model/provider/GitHub credentials and parent Python injection flags are not inherited.
    names = ("PATH", "SystemRoot", "WINDIR", "TEMP", "TMP", "TMPDIR", "HOME", "USERPROFILE",
             "LOCALAPPDATA", "APPDATA", "COMSPEC", "PATHEXT", "LANG", "LC_ALL")
    env = {key: os.environ[key] for key in names if key in os.environ}
    env.update(CI="true", PYTHONPATH=str(root), PYTHONDONTWRITEBYTECODE="1",
               NPM_CONFIG_OFFLINE="true", NPM_CONFIG_AUDIT="false",
               NPM_CONFIG_FUND="false", NPM_CONFIG_UPDATE_NOTIFIER="false", NPM_CONFIG_USERCONFIG=os.devnull,
               NPM_CONFIG_GLOBALCONFIG=os.devnull)
    return env


class _WindowsJob:
    """A job is assigned before resuming the child, so descendants cannot escape."""
    def __init__(self) -> None:
        import ctypes
        from ctypes import wintypes
        class Limits(ctypes.Structure):
            _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                        ("flags", wintypes.DWORD), ("minimum", ctypes.c_size_t), ("maximum", ctypes.c_size_t),
                        ("active", wintypes.DWORD), ("affinity", ctypes.c_size_t),
                        ("priority", wintypes.DWORD), ("scheduling", wintypes.DWORD)]
        class Extended(ctypes.Structure):
            _fields_ = [("basic", Limits), ("io", ctypes.c_ulonglong * 6),
                        ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                        ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.kernel.CreateJobObjectW.restype = wintypes.HANDLE
        self.kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        self.kernel.SetInformationJobObject.restype = wintypes.BOOL
        self.kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.kernel.AssignProcessToJobObject.restype = wintypes.BOOL
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL
        self.handle = self.kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = Extended()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise error
        self.nt = ctypes.WinDLL("ntdll")
        self.nt.NtResumeProcess.argtypes = [wintypes.HANDLE]
        self.nt.NtResumeProcess.restype = wintypes.LONG

    def attach_and_resume(self, proc: subprocess.Popen[bytes]) -> None:
        import ctypes
        handle = int(proc._handle)
        if not self.kernel.AssignProcessToJobObject(self.handle, handle):
            raise ctypes.WinError(ctypes.get_last_error())
        if self.nt.NtResumeProcess(handle) < 0:
            raise OSError("functional_process_resume_failed")

    def close(self) -> None:
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def _terminate(proc: subprocess.Popen[bytes], job: _WindowsJob | None) -> None:
    if job is not None:
        job.close()
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if proc.poll() is None:
        proc.kill()
    proc.wait(timeout=10)


def _run_check(check: Mapping[str, str], root: Path) -> dict[str, Any]:
    profile = check["profile_id"]
    cwd = _working_directory(root, check["working_directory"])
    # npm reads project configuration independently of user/global configuration.
    # Refuse it without inspecting potentially sensitive configuration contents.
    if profile == "npm_test" and any((directory / ".npmrc").exists()
            for directory in (cwd, *cwd.parents) if directory.is_relative_to(root)):
        raise TaskStoreError("functional_npm_project_config_unsupported")
    argv = _resolved_argv(profile)
    with tempfile.TemporaryDirectory(prefix="nerelan-functional-check-") as temporary:
        env = _environment(root)
        report = Path(temporary) / "tests.xml"
        report_kind = "junit"
        if profile == "python_pytest":
            argv.append(f"--junitxml={report}")
        if profile == "npm_test":
            package = cwd / "package.json"
            if package.stat().st_size > 1048576:
                raise TaskStoreError("functional_package_metadata_too_large")
            scripts = json.loads(package.read_text(encoding="utf-8")).get("scripts", {})
            command = scripts.get("test", "") if isinstance(scripts, dict) else ""
            if isinstance(scripts, dict) and any(scripts.get(key) for key in ("pretest", "posttest")):
                raise TaskStoreError("functional_npm_lifecycle_hooks_unsupported")
            if command == "node --test":
                report_kind = "tap"
                argv.extend(["--", "--test-reporter=tap"])
            elif command == "vitest run":
                argv.extend(["--", "--reporter=junit", f"--outputFile={report}"])
            else:
                raise TaskStoreError("functional_npm_test_runner_unsupported")
            config_root = Path(temporary)
            for name in ("user.npmrc", "global.npmrc"):
                (config_root / name).write_text("", encoding="utf-8")
            env.update(NPM_CONFIG_USERCONFIG=str(config_root / "user.npmrc"),
                       NPM_CONFIG_GLOBALCONFIG=str(config_root / "global.npmrc"),
                       NPM_CONFIG_CACHE=str(config_root / "cache"))
        result = _run_process(check, argv, cwd, env)
        tail = result.pop("_output_tail")
        result["test_report"] = _test_report(report_kind, report, tail)
        return result


def _test_report(kind: str, report: Path, tail: bytes) -> dict[str, Any]:
    counts = {"tests": 0, "passed": 0, "failed": 0, "skipped": 0}
    try:
        if kind == "junit":
            if not report.is_file() or report.stat().st_size > 8388608:
                raise ValueError
            raw = report.read_bytes()
            if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
                raise ValueError
            cases = list(ET.fromstring(raw).iter("testcase"))
            counts["tests"] = len(cases)
            for case in cases:
                key = "failed" if case.find("failure") is not None or case.find("error") is not None else (
                    "skipped" if case.find("skipped") is not None else "passed")
                counts[key] += 1
        else:
            summary = tail.decode("utf-8", errors="replace")
            observed = {key: int(value) for key, value in re.findall(
                r"(?m)^# (tests|pass|fail|cancelled|skipped) (\d+)\s*$", summary)}
            if set(observed) != {"tests", "pass", "fail", "cancelled", "skipped"}:
                raise ValueError
            counts.update(tests=observed["tests"], passed=observed["pass"],
                          failed=observed["fail"] + observed["cancelled"], skipped=observed["skipped"])
        complete = counts["tests"] == counts["passed"] + counts["failed"] + counts["skipped"]
        return {"format": kind, **counts, "accepted": complete and counts["passed"] > 0 and counts["failed"] == 0}
    except (OSError, ValueError, ET.ParseError):
        return {"format": kind, **counts, "accepted": False}


def _run_process(check: Mapping[str, str], argv: list[str], cwd: Path, env: dict[str, str]) -> dict[str, Any]:
    profile = check["profile_id"]
    started = time.monotonic()
    job = _WindowsJob() if os.name == "nt" else None
    try:
        proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, env=env, shell=False,
                                start_new_session=os.name != "nt",
                                creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW | 4) if job else 0)
        if job:
            try:
                job.attach_and_resume(proc)
            except BaseException:
                job.close()
                if proc.poll() is None:
                    proc.kill()
                proc.wait(timeout=10)
                raise
    except BaseException:
        if job:
            job.close()
        raise
    output_hash = hashlib.sha256()
    output_size = [0]
    retained = bytearray()
    def drain() -> None:
        assert proc.stdout is not None
        while chunk := proc.stdout.read(8192):
            output_hash.update(chunk)
            output_size[0] += len(chunk)
            retained.extend(chunk)
            if len(retained) > OUTPUT_LIMIT:
                del retained[:-OUTPUT_LIMIT]
    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    timed_out = False
    try:
        proc.wait(timeout=_CATALOG[profile]["timeout_seconds"])
        reader.join(timeout=2)
        if reader.is_alive():
            timed_out = True
            _terminate(proc, job)
    except subprocess.TimeoutExpired:
        timed_out = True
        _terminate(proc, job)
    finally:
        if job:
            job.close()
        else:
            _terminate(proc, None)
        reader.join(timeout=10)
        if not reader.is_alive() and proc.stdout is not None:
            proc.stdout.close()
    if reader.is_alive():
        raise TaskStoreError("functional_output_drain_incomplete")
    return {**check, "argv": argv, "argv_digest": digest(argv), "exit_code": proc.returncode,
            "timed_out": timed_out, "duration_ms": round((time.monotonic() - started) * 1000),
            "output_digest": output_hash.hexdigest(), "output_bytes": output_size[0],
            "output_truncated": output_size[0] > OUTPUT_LIMIT, "_output_tail": bytes(retained)}


def validate_functional(task: Any, *, worktree: str | Path, base_commit: str, execution_id: str) -> dict[str, Any] | None:
    contract = load_contract(task)
    if contract is None:
        return None
    result: dict[str, Any] = {"version": 1, "task_id": task.id, "execution_id": execution_id,
        "contract_digest": digest(contract), "repository": task.repository, "base_commit": base_commit,
        "head_before": "", "head_after": "", "tree_before": "", "tree_after": "",
        "checks": [], "passed": False, "verified": False, "status": "FAILED", "reason": ""}
    try:
        if base_commit != contract["base_commit"]:
            raise TaskStoreError("functional_base_mismatch")
        root = Path(worktree).resolve(strict=True)
        binding = resolve_repository_workspace(task.repository, source_dir=root)
        if binding.repo_dir != root:
            raise TaskStoreError("functional_worktree_root_required")
        if (root / ".reverse-agent-handoff").exists():
            raise TaskStoreError("functional_transient_handoff_present")
        result["head_before"] = git_output(root, "rev-parse", "HEAD")
        if git_output(root, "merge-base", base_commit, result["head_before"]) != base_commit:
            raise TaskStoreError("functional_base_ancestry_mismatch")
        _, before, changed, hygiene = _snapshot_workspace(root, base_commit)
        result["tree_before"] = before
        if contract["requires_implementation"] and not changed:
            raise TaskStoreError("functional_implementation_missing")
        if hygiene["exit_code"] != 0:
            raise TaskStoreError("functional_patch_hygiene_failed")
        for check in contract["checks"]:
            observed = _run_check(check, root)
            result["checks"].append(observed)
            if observed["timed_out"] or observed["exit_code"] != 0 or not observed["test_report"]["accepted"]:
                break
        result["head_after"] = git_output(root, "rev-parse", "HEAD")
        _, after, _, after_hygiene = _snapshot_workspace(root, base_commit)
        result["tree_after"] = after
        if before != after or result["head_before"] != result["head_after"]:
            raise TaskStoreError("functional_artifact_changed_during_checks")
        if after_hygiene["exit_code"] != 0 or len(result["checks"]) != len(contract["checks"]) or any(
            check["timed_out"] or check["exit_code"] != 0 or not check["test_report"]["accepted"] for check in result["checks"]
        ):
            raise TaskStoreError("functional_check_failed")
        result.update(passed=True, verified=task.executor_kind != "deterministic_fixture",
                      status="FIXTURE_VERIFIED" if task.executor_kind == "deterministic_fixture" else "VERIFIED")
    except (TaskStoreError, OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        result["reason"] = str(exc) if isinstance(exc, TaskStoreError) else f"functional_observation_failed:{type(exc).__name__}"
    return result


def run_task_validation(store: Any, task_id: str, *, worktree: str | Path, base_commit: str = "",
                        execution_id: str = "", lease: Any = None) -> tuple[str, int, str, str]:
    """Run the approved oracle, or legacy hygiene, and persist fenced proof.

    The caller retains its existing lifecycle/checkpoint writes. Evidence is
    written first; a crash before binding its digest cannot claim verification.
    """
    from .task_runtime import LocalValidationRunner
    task = store.get_task(task_id)
    try:
        contract = load_contract(task)
    except TaskStoreError as exc:
        return FUNCTIONAL_COMMAND_ID, -1, str(exc), ""
    if contract is None:
        code, output, output_digest = LocalValidationRunner().run(
            task_id=task_id, command_id="git_diff_check", cwd=str(worktree))
        return "git_diff_check", code, output, output_digest
    if lease is not None:
        store._validate_durable_lease(lease.run_id, lease.owner, lease.epoch)
    result = validate_functional(task, worktree=worktree,
                                 base_commit=base_commit,
                                 execution_id=execution_id or task.execution_id)
    assert result is not None
    result["run_id"] = lease.run_id if lease is not None else ""
    result["lease_epoch"] = lease.epoch if lease is not None else None
    identity = digest(result)
    fields = dict(category=RESULT_CATEGORY, label=FUNCTIONAL_COMMAND_ID, value=identity,
                  status=result["status"], detail=canonical(result), raw_json_digest=identity)
    if lease is None:
        store.add_evidence(task_id, **fields)
    else:
        store._fenced_add_evidence(lease.run_id, task_id, **fields, owner=lease.owner, epoch=lease.epoch)
    return FUNCTIONAL_COMMAND_ID, 0 if result["passed"] else 1, result["reason"], identity


def functional_evidence(task: Any) -> dict[str, Any]:
    """Safe read-only proof projection; stale/missing/fixture results never verify."""
    if isinstance(task, Mapping):
        from types import SimpleNamespace
        task = SimpleNamespace(**task)
    fallback = {"status": "UNVERIFIED", "verified": False}
    try:
        contract = load_contract(task)
        if contract is None:
            return fallback
        fallback["contract_digest"] = digest(contract)
        if getattr(task, "status", "") not in {"VALIDATING", "READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE", "FAILED"}:
            return fallback
        if getattr(task, "validation_command_id", "") != FUNCTIONAL_COMMAND_ID:
            return fallback
        identity = getattr(task, "validation_output_digest", "")
        rows = [row for row in task.evidence_refs if row.get("category") == RESULT_CATEGORY
                and row.get("value") == identity and row.get("raw_json_digest") == identity]
        if not rows:
            return fallback
        row = rows[-1]
        result = json.loads(row["detail"])
        if (digest(result) != identity or result["task_id"] != task.id
                or result["contract_digest"] != digest(contract)
                or result["repository"] != task.repository or result["base_commit"] != contract["base_commit"]
                or result["execution_id"] != task.execution_id or row["status"] != result["status"]):
            return fallback
        checks = result["checks"]
        identities = [{key: item[key] for key in ("profile_id", "working_directory")} for item in checks]
        consistent = (identities == contract["checks"]
                      and all(type(item["exit_code"]) is int and item["exit_code"] == 0
                              and item["timed_out"] is False and item["test_report"]["accepted"] is True
                              and digest(item["argv"]) == item["argv_digest"] for item in checks)
                      and _SHA40.fullmatch(result["head_before"]) is not None
                      and _SHA40.fullmatch(result["tree_before"]) is not None
                      and result["head_before"] == result["head_after"]
                      and result["tree_before"] == result["tree_after"])
        verified = (consistent and result["passed"] is True and result["verified"] is True
                    and result["status"] == "VERIFIED" and task.executor_kind == "opencode"
                    and type(task.validation_exit_code) is int and task.validation_exit_code == 0)
        return {"status": "VERIFIED" if verified else ("FIXTURE_VERIFIED" if consistent
                and result["status"] == "FIXTURE_VERIFIED" else "FAILED"), "verified": verified,
                "contract_digest": digest(contract), "result_digest": identity,
                "run_id": result.get("run_id", ""), "lease_epoch": result.get("lease_epoch"),
                "base_commit": result["base_commit"], "head": result["head_after"],
                "tree": result["tree_after"], "checks": [
                    {key: item[key] for key in ("profile_id", "working_directory", "exit_code", "timed_out",
                     "duration_ms", "output_digest", "output_bytes", "output_truncated", "test_report")}
                    for item in checks], "reason": result["reason"]}
    except (TaskStoreError, ValueError, KeyError, TypeError, AttributeError):
        return fallback


def accepted_checkpoint_proof(task: Any, run: Any) -> dict[str, Any]:
    """Re-observe an accepted result without rerunning accepted executor work."""
    from dataclasses import replace
    if (run.accepted_checkpoint != "POST_VALIDATION"
            or (task.status in {"READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE"}
                and (task.validation_command_id != run.validation_command_id
                     or task.validation_exit_code != run.validation_exit_code
                     or task.validation_output_digest != run.validation_output_digest))):
        return {"status": "UNVERIFIED", "verified": False, "passed": False,
                "reason": "functional_checkpoint_binding_mismatch"}
    candidate = replace(task, status="VALIDATING", validation_command_id=run.validation_command_id,
                        validation_exit_code=run.validation_exit_code,
                        validation_output_digest=run.validation_output_digest)
    proof = functional_evidence(candidate)
    if proof["status"] not in {"VERIFIED", "FIXTURE_VERIFIED"}:
        return {**proof, "passed": False, "reason": proof.get("reason") or "functional_checkpoint_evidence_invalid"}
    try:
        if (proof["run_id"] != run.run_id or type(proof["lease_epoch"]) is not int
                or proof["lease_epoch"] > run.lease_epoch or proof["lease_epoch"] < 1
                or run.execution_id != task.execution_id or proof["base_commit"] != run.repository_base_sha):
            raise TaskStoreError("functional_checkpoint_binding_mismatch")
        root = Path(run.worktree_path).resolve(strict=True)
        if resolve_repository_workspace(task.repository, source_dir=root).repo_dir != root:
            raise TaskStoreError("functional_worktree_root_required")
        if git_output(root, "rev-parse", "HEAD") != proof["head"]:
            raise TaskStoreError("functional_checkpoint_artifact_changed")
        _, tree, _, hygiene = _snapshot_workspace(root, proof["base_commit"])
        if tree != proof["tree"] or hygiene["exit_code"] != 0:
            raise TaskStoreError("functional_checkpoint_artifact_changed")
        return {**proof, "passed": True}
    except (TaskStoreError, OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        return {**proof, "passed": False, "verified": False, "status": "UNVERIFIED",
                "reason": str(exc) if isinstance(exc, TaskStoreError) else "functional_checkpoint_observation_failed"}
