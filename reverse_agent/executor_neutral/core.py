from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
import hashlib, json, os, re, subprocess, tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


REQUIRED_CHECK_TIMEOUT_SECONDS = 60
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported canonical JSON type: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(_plain(value), ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True)


def sha256_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _text(payload: Mapping[str, Any], name: str) -> str:
    value = payload.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing_or_invalid:{name}")
    return value.strip()


def _string_tuple(payload: Mapping[str, Any], name: str) -> tuple[str, ...]:
    value = payload.get(name)
    if not isinstance(value, list) or not value:
        raise ValueError(f"missing_or_invalid:{name}")
    result = tuple(item.strip() for item in value if isinstance(item, str) and item.strip())
    if len(result) != len(value) or len(set(result)) != len(result):
        raise ValueError(f"missing_or_invalid:{name}")
    return result


def _normalize_allowed_path(pattern: str) -> str:
    if not isinstance(pattern, str) or not pattern or pattern != pattern.strip():
        raise ValueError(f"invalid_allowed_path:{pattern}")
    normalized = pattern.replace("\\", "/")
    if (
        normalized.startswith("/")
        or re.match(r"^[A-Za-z]:/", normalized)
        or normalized.endswith("/")
        or "//" in normalized
    ):
        raise ValueError(f"invalid_allowed_path:{pattern}")
    components = normalized.split("/")
    if any(component in {"", ".", ".."} for component in components):
        raise ValueError(f"invalid_allowed_path:{pattern}")
    recursive = normalized.endswith("/**")
    prefix_components = components[:-1] if recursive else components
    if not prefix_components or any(any(char in item for char in "*?[]") for item in prefix_components):
        raise ValueError(f"invalid_allowed_path:{pattern}")
    if not recursive and any(char in normalized for char in "*?[]"):
        raise ValueError(f"invalid_allowed_path:{pattern}")
    return normalized


@dataclass(frozen=True)
class TaskContract:
    schema_version: str
    task_id: str
    objective: str
    repository_identity: str
    base_commit: str
    allowed_paths: tuple[str, ...]
    required_checks: tuple[str, ...]
    executor_hint: str

    def __post_init__(self) -> None:
        for name in ("schema_version", "task_id", "objective", "repository_identity", "executor_hint"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"missing_or_invalid:{name}")
        base_commit = self.base_commit.lower()
        if not _SHA40.fullmatch(base_commit):
            raise ValueError("missing_or_invalid:base_commit")
        normalized_paths = tuple(_normalize_allowed_path(item) for item in self.allowed_paths)
        checks = tuple(self.required_checks)
        if not normalized_paths or len(set(normalized_paths)) != len(normalized_paths):
            raise ValueError("missing_or_invalid:allowed_paths")
        if not checks or len(set(checks)) != len(checks) or any(
            not isinstance(command, str) or not command.strip() for command in checks
        ):
            raise ValueError("missing_or_invalid:required_checks")
        object.__setattr__(self, "base_commit", base_commit)
        object.__setattr__(self, "allowed_paths", normalized_paths)
        object.__setattr__(self, "required_checks", checks)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TaskContract":
        if not isinstance(payload, Mapping):
            raise ValueError("contract_must_be_mapping")
        return cls(
            schema_version=_text(payload, "schema_version"),
            task_id=_text(payload, "task_id"),
            objective=_text(payload, "objective"),
            repository_identity=_text(payload, "repository_identity"),
            base_commit=_text(payload, "base_commit"),
            allowed_paths=_string_tuple(payload, "allowed_paths"),
            required_checks=_string_tuple(payload, "required_checks"),
            executor_hint=_text(payload, "executor_hint"),
        )

    def to_dict(self) -> dict[str, Any]:
        return _plain(asdict(self))

    @property
    def digest(self) -> str:
        return sha256_digest(self)


@dataclass(frozen=True)
class ExecutionEvidence:
    schema_version: str
    task_id: str
    executor: str
    contract_digest: str
    base_commit: str
    base_tree: str
    observed_tree: str
    changed_paths: tuple[str, ...]
    git_diff_check: Mapping[str, Any]
    required_check_results: tuple[Mapping[str, Any], ...]
    agent_completion_claim: bool
    started_at: str
    completed_at: str

    def to_dict(self) -> dict[str, Any]:
        return _plain(asdict(self))

    @property
    def digest(self) -> str:
        return sha256_digest(self)


@dataclass(frozen=True)
class AcceptanceResult:
    schema_version: str
    task_id: str
    accepted: bool
    scope_result: str
    required_check_results: tuple[Mapping[str, Any], ...]
    blocking_reasons: tuple[str, ...]
    contract_digest: str
    base_tree: str
    observed_tree: str
    evidence_digest: str

    def to_dict(self) -> dict[str, Any]:
        return _plain(asdict(self))


@dataclass(frozen=True)
class CapabilityObservation:
    task_class: str
    executor: str
    success: bool
    attempts: int
    elapsed_time: float
    failure_class: str | None

    def to_dict(self) -> dict[str, Any]:
        return _plain(asdict(self))


def export_task_bundle(contract: TaskContract, output_dir: Path | str) -> tuple[Path, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "task_contract.json"
    markdown_path = directory / "task.md"
    json_path.write_text(canonical_json(contract) + "\n", encoding="utf-8")
    markdown = "\n".join(
        [
            f"# Task {contract.task_id}",
            "",
            contract.objective,
            "",
            f"- Repository routing identity (descriptive): `{contract.repository_identity}`",
            f"- Base commit (authoritative content identity): `{contract.base_commit}`",
            f"- Executor hint: `{contract.executor_hint}`",
            f"- Contract SHA-256: `{contract.digest}`",
            "",
            "The trusted collector derives authoritative base and observed tree IDs.",
            "",
            "## Allowed paths",
            "",
            *(f"- `{path}`" for path in contract.allowed_paths),
            "",
            "## Required checks",
            "",
            *(f"- `{command}`" for command in contract.required_checks),
            "",
            f"Each trusted contract check has a fixed {REQUIRED_CHECK_TIMEOUT_SECONDS}-second timeout.",
            "Only modify allowed paths. A completion claim is not acceptance.",
            "",
        ]
    )
    markdown_path.write_text(markdown, encoding="utf-8")
    return json_path, markdown_path


def _run(
    command: Sequence[str] | str,
    *,
    cwd: Path,
    shell: bool = False,
    env: Mapping[str, str] | None = None,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        shell=shell,
        env=dict(env) if env is not None else None,
        timeout=timeout,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _command_result(
    command: Sequence[str] | str,
    result: subprocess.CompletedProcess[str],
    *,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    rendered = command if isinstance(command, str) else " ".join(command)
    payload: dict[str, Any] = {
        "command": rendered,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    if timeout_seconds is not None:
        payload.update(timed_out=False, timeout_seconds=timeout_seconds)
    return payload


def _captured_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value


def _run_required_check(command: str, repo: Path) -> dict[str, Any]:
    try:
        result = _run(
            command,
            cwd=repo,
            shell=True,
            timeout=REQUIRED_CHECK_TIMEOUT_SECONDS,
        )
        return _command_result(
            command,
            result,
            timeout_seconds=REQUIRED_CHECK_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "exit_code": None,
            "stdout": _captured_text(exc.stdout),
            "stderr": _captured_text(exc.stderr),
            "timed_out": True,
            "timeout_seconds": REQUIRED_CHECK_TIMEOUT_SECONDS,
        }


def _git(
    repo: Path,
    *args: str,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = _run(("git", *args), cwd=repo, env=env)
    if result.returncode != 0:
        raise ValueError(f"git_command_failed:{' '.join(args)}:{result.stderr.strip()}")
    return result


def _real_index_state(repo: Path) -> tuple[Path, bytes | None]:
    raw = _git(repo, "rev-parse", "--git-path", "index").stdout.strip()
    path = Path(raw)
    resolved = (path if path.is_absolute() else repo / path).resolve()
    return resolved, resolved.read_bytes() if resolved.exists() else None


def _changed_paths(name_status_z: str) -> tuple[str, ...]:
    tokens = name_status_z.split("\0")
    if tokens and tokens[-1] == "":
        tokens.pop()
    if len(tokens) % 2:
        raise ValueError("invalid_name_status_evidence")
    paths: list[str] = []
    for index in range(0, len(tokens), 2):
        status, path = tokens[index], tokens[index + 1]
        if not status or not path:
            raise ValueError("invalid_name_status_evidence")
        paths.append(path.replace("\\", "/"))
    return tuple(dict.fromkeys(paths))


def _snapshot_workspace(
    repo: Path,
    base_commit: str,
) -> tuple[str, str, tuple[str, ...], dict[str, Any]]:
    base_tree = _git(repo, "rev-parse", f"{base_commit}^{{tree}}").stdout.strip().lower()
    real_index_before, real_bytes_before = _real_index_state(repo)
    temp_dir = Path(tempfile.mkdtemp(prefix="reverse-agent-index-")).resolve()
    temp_index = temp_dir / "index"
    if temp_index.resolve() == real_index_before:
        raise ValueError("temporary_index_matches_real_index")
    alternate_env = os.environ.copy()
    alternate_env["GIT_INDEX_FILE"] = str(temp_index)
    observed_tree = ""
    changed_paths: tuple[str, ...] = ()
    diff_result: dict[str, Any] = {}
    try:
        _git(repo, "read-tree", base_commit, env=alternate_env)
        _git(repo, "add", "-A", "--", ".", env=alternate_env)
        observed_tree = _git(repo, "write-tree", env=alternate_env).stdout.strip().lower()
        name_status = _git(
            repo,
            "diff",
            "--name-status",
            "-z",
            "--no-renames",
            base_tree,
            observed_tree,
            "--",
        )
        changed_paths = _changed_paths(name_status.stdout)
        diff_command = ("git", "diff", "--check", base_tree, observed_tree, "--")
        diff_result = _command_result(diff_command, _run(diff_command, cwd=repo))
    finally:
        real_index_after, real_bytes_after = _real_index_state(repo)
        index_unchanged = (
            real_index_after == real_index_before
            and real_bytes_after == real_bytes_before
        )
        for owned_path in (temp_index, temp_dir / "index.lock"):
            if owned_path.exists():
                owned_path.unlink()
        temp_dir.rmdir()
        if not index_unchanged:
            raise ValueError("real_index_mutated_during_snapshot")
    if not _SHA40.fullmatch(base_tree) or not _SHA40.fullmatch(observed_tree):
        raise ValueError("invalid_tree_identity")
    return base_tree, observed_tree, changed_paths, diff_result


def collect_execution_evidence(
    contract: TaskContract,
    repository: Path | str,
    *,
    executor: str,
    agent_completion_claim: bool,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> ExecutionEvidence:
    supplied = Path(repository).resolve()
    if not supplied.is_dir():
        raise ValueError("repository_not_found")
    root_result = _git(supplied, "rev-parse", "--show-toplevel")
    repo = Path(root_result.stdout.strip()).resolve()
    actual_base = _git(repo, "rev-parse", f"{contract.base_commit}^{{commit}}").stdout.strip().lower()
    if actual_base != contract.base_commit:
        raise ValueError("base_commit_mismatch")
    check_results = tuple(_run_required_check(command, repo) for command in contract.required_checks)
    base_tree, observed_tree, changed_paths, diff_result = _snapshot_workspace(repo, actual_base)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return ExecutionEvidence(
        schema_version=contract.schema_version,
        task_id=contract.task_id,
        executor=executor.strip() or "unknown",
        contract_digest=contract.digest,
        base_commit=actual_base,
        base_tree=base_tree,
        observed_tree=observed_tree,
        changed_paths=changed_paths,
        git_diff_check=diff_result,
        required_check_results=check_results,
        agent_completion_claim=bool(agent_completion_claim),
        started_at=started_at or now,
        completed_at=completed_at or now,
    )


def _path_allowed(path: str, patterns: tuple[str, ...]) -> bool:
    normalized = path.replace("\\", "/")
    for pattern in patterns:
        if pattern.endswith("/**"):
            if normalized.startswith(pattern[:-3] + "/"):
                return True
        elif normalized == pattern:
            return True
    return False


def _check_result_malformed(result: Mapping[str, Any]) -> bool:
    return (
        not all(isinstance(result.get(name), str) for name in ("command", "stdout", "stderr"))
        or not isinstance(result.get("timed_out"), bool)
        or result.get("timeout_seconds") != REQUIRED_CHECK_TIMEOUT_SECONDS
        or (result.get("exit_code") is not None and not isinstance(result.get("exit_code"), int))
    )


def accept_execution(contract: TaskContract, evidence: ExecutionEvidence) -> AcceptanceResult:
    reasons: list[str] = []
    if evidence.schema_version != contract.schema_version:
        reasons.append("schema_version_mismatch")
    if evidence.task_id != contract.task_id:
        reasons.append("task_id_mismatch")
    if not _SHA40.fullmatch(evidence.base_commit):
        reasons.append("base_commit_malformed")
    elif evidence.base_commit != contract.base_commit:
        reasons.append("base_commit_mismatch")
    if not _SHA40.fullmatch(evidence.base_tree):
        reasons.append("base_tree_malformed")
    if not _SHA40.fullmatch(evidence.observed_tree):
        reasons.append("observed_tree_malformed")
    if not _SHA256.fullmatch(evidence.contract_digest):
        reasons.append("contract_digest_malformed")
    elif evidence.contract_digest != contract.digest:
        reasons.append("contract_digest_mismatch")
    evidence_digest = evidence.digest
    if not _SHA256.fullmatch(evidence_digest):
        reasons.append("evidence_digest_malformed")
    outside = tuple(path for path in evidence.changed_paths if not _path_allowed(path, contract.allowed_paths))
    reasons.extend(f"changed_path_outside_allowed_scope:{path}" for path in outside)
    diff_check = evidence.git_diff_check
    if (
        not isinstance(diff_check, Mapping)
        or not isinstance(diff_check.get("command"), str)
        or not isinstance(diff_check.get("stdout"), str)
        or not isinstance(diff_check.get("stderr"), str)
        or not isinstance(diff_check.get("exit_code"), int)
    ):
        reasons.append("git_diff_check_malformed")
    elif diff_check.get("exit_code") != 0:
        reasons.append("git_diff_check_failed")
    commands = tuple(
        result.get("command") if isinstance(result, Mapping) else None
        for result in evidence.required_check_results
    )
    if commands != contract.required_checks:
        reasons.append("required_check_evidence_mismatch")
    for result in evidence.required_check_results:
        if not isinstance(result, Mapping) or _check_result_malformed(result):
            reasons.append("required_check_result_malformed")
            continue
        if result.get("timed_out"):
            reasons.append(f"required_check_timeout:{result.get('command')}")
        elif result.get("exit_code") != 0:
            reasons.append(f"required_check_failed:{result.get('command')}")
    accepted = not reasons
    summaries = tuple(
        {
            "command": result.get("command") if isinstance(result, Mapping) else None,
            "exit_code": result.get("exit_code") if isinstance(result, Mapping) else None,
            "timed_out": result.get("timed_out") if isinstance(result, Mapping) else None,
            "timeout_seconds": result.get("timeout_seconds") if isinstance(result, Mapping) else None,
            "passed": (
                isinstance(result, Mapping)
                and result.get("timed_out") is False
                and result.get("exit_code") == 0
            ),
        }
        for result in evidence.required_check_results
    )
    return AcceptanceResult(
        schema_version=contract.schema_version,
        task_id=contract.task_id,
        accepted=accepted,
        scope_result="PASS" if not outside else "FAIL",
        required_check_results=summaries,
        blocking_reasons=tuple(dict.fromkeys(reasons)),
        contract_digest=evidence.contract_digest,
        base_tree=evidence.base_tree,
        observed_tree=evidence.observed_tree,
        evidence_digest=evidence_digest,
    )


def observe_capability(
    contract: TaskContract,
    evidence: ExecutionEvidence,
    acceptance: AcceptanceResult,
    *,
    task_class: str = "bounded_coding_task",
    attempts: int = 1,
) -> CapabilityObservation:
    if evidence.task_id != contract.task_id or acceptance.task_id != contract.task_id:
        raise ValueError("task_id_mismatch")
    started = datetime.fromisoformat(evidence.started_at)
    completed = datetime.fromisoformat(evidence.completed_at)
    elapsed = max(0.0, (completed - started).total_seconds())
    failure = None if acceptance.accepted else (
        acceptance.blocking_reasons[0].split(":", 1)[0]
        if acceptance.blocking_reasons else "unknown"
    )
    return CapabilityObservation(
        task_class=task_class,
        executor=evidence.executor,
        success=acceptance.accepted,
        attempts=max(1, attempts),
        elapsed_time=elapsed,
        failure_class=failure,
    )
